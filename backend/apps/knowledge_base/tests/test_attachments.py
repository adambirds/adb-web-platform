import os
from tempfile import TemporaryDirectory
from typing import Any
from unittest.mock import Mock, patch

from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.knowledge_base.attachment_security import quarantine_attachment
from apps.knowledge_base.models import (
    KnowledgeBaseAttachment,
    KnowledgeBaseDocument,
    KnowledgeBaseSection,
)
from apps.knowledge_base.tasks import scan_knowledge_base_attachment
from apps.ticketing.services.scanning import AttachmentScanResult
from authentication.models import User


class KnowledgeBaseAttachmentApiTests(TestCase):
    def setUp(self) -> None:
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.media.name)
        self.override.enable()
        self.addCleanup(self.override.disable)

        self.staff = User.objects.create_user(
            email="kb-attachments@example.test",
            password="test-password",
            first_name="KB",
            last_name="Operator",
            is_staff=True,
        )
        profile = StaffAccessProfile.objects.create(user=self.staff)
        self.client_account = Client.objects.create(
            name="Visible",
            company="Visible Client",
            email="kb-attachments-client@example.test",
        )
        self.hidden_client = Client.objects.create(
            name="Hidden",
            company="Hidden Client",
            email="kb-attachments-hidden@example.test",
        )
        ClientAccessGrant.objects.create(
            profile=profile,
            client=self.client_account,
            granted_by=self.staff,
        )
        self.section = KnowledgeBaseSection.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_account,
            name="Operations",
        )
        self.document = KnowledgeBaseDocument.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_account,
            section=self.section,
            title="Deployment runbook",
            content="# Deploy",
        )
        hidden_section = KnowledgeBaseSection.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.hidden_client,
            name="Hidden",
        )
        self.hidden_document = KnowledgeBaseDocument.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.hidden_client,
            section=hidden_section,
            title="Hidden runbook",
            content="# Hidden",
        )
        self.client.force_login(self.staff)

    def grant(self, *permissions: tuple[str, str]) -> None:
        for app_label, codename in permissions:
            permission = Permission.objects.get(
                content_type__app_label=app_label,
                codename=codename,
            )
            self.staff.user_permissions.add(permission)

    def _upload(self, filename: str = "runbook.pdf") -> Any:
        return self.client.post(
            f"/api/admin/knowledge-base/documents/{self.document.id}/attachments",
            {
                "file": SimpleUploadedFile(
                    filename,
                    b"%PDF-test",
                    content_type="application/pdf",
                )
            },
        )

    @patch.dict(os.environ, {"TICKETING_MALWARE_SCANNING_ENABLED": "0"})
    def test_upload_quarantines_and_sanitises_filename(self) -> None:
        self.grant(
            ("knowledge_base", "change_knowledgebasedocument"),
            ("knowledge_base", "add_knowledgebaseattachment"),
        )

        response = self._upload("../../unsafe?.pdf")

        self.assertEqual(response.status_code, 201)
        attachment = KnowledgeBaseAttachment.objects.get(id=response.json()["id"])
        self.assertEqual(attachment.original_name, "unsafe_.pdf")
        self.assertEqual(
            attachment.scan_status,
            KnowledgeBaseAttachment.ScanStatus.PENDING,
        )
        self.assertEqual(attachment.detected_content_type, "application/pdf")
        self.assertEqual(len(attachment.sha256), 64)
        file_name = attachment.file.name or ""
        self.assertIn("knowledge-base/quarantine/", file_name)
        self.assertNotIn("..", file_name)

    @patch.dict(os.environ, {"TICKETING_MALWARE_SCANNING_ENABLED": "0"})
    def test_pending_attachment_downloads_when_scanning_is_disabled(self) -> None:
        self.grant(
            ("knowledge_base", "change_knowledgebasedocument"),
            ("knowledge_base", "add_knowledgebaseattachment"),
            ("knowledge_base", "view_knowledgebasedocument"),
            ("knowledge_base", "view_knowledgebaseattachment"),
        )
        upload = self._upload()

        response = self.client.get(
            f"/api/admin/knowledge-base/attachments/{upload.json()['id']}/download"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")

    @patch.dict(os.environ, {"TICKETING_MALWARE_SCANNING_ENABLED": "0"})
    def test_infected_attachment_is_never_downloadable(self) -> None:
        self.grant(
            ("knowledge_base", "change_knowledgebasedocument"),
            ("knowledge_base", "add_knowledgebaseattachment"),
            ("knowledge_base", "view_knowledgebasedocument"),
            ("knowledge_base", "view_knowledgebaseattachment"),
        )
        upload = self._upload()
        KnowledgeBaseAttachment.objects.filter(id=upload.json()["id"]).update(
            scan_status=KnowledgeBaseAttachment.ScanStatus.INFECTED
        )

        response = self.client.get(
            f"/api/admin/knowledge-base/attachments/{upload.json()['id']}/download"
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "attachment_not_safe")

    @patch.dict(os.environ, {"TICKETING_MALWARE_SCANNING_ENABLED": "1"})
    @patch("apps.knowledge_base.tasks.scan_knowledge_base_attachment.delay")
    def test_pending_attachment_is_quarantined_when_scanning_is_enabled(
        self,
        delay: Mock,
    ) -> None:
        self.grant(
            ("knowledge_base", "change_knowledgebasedocument"),
            ("knowledge_base", "add_knowledgebaseattachment"),
            ("knowledge_base", "view_knowledgebasedocument"),
            ("knowledge_base", "view_knowledgebaseattachment"),
        )
        with self.captureOnCommitCallbacks(execute=True):
            upload = self._upload()
        delay.assert_called_once_with(upload.json()["id"])

        response = self.client.get(
            f"/api/admin/knowledge-base/attachments/{upload.json()['id']}/download"
        )
        self.assertEqual(response.status_code, 409)

    @patch.dict(os.environ, {"TICKETING_MALWARE_SCANNING_ENABLED": "0"})
    def test_attachment_outside_client_scope_is_hidden(self) -> None:
        self.grant(
            ("knowledge_base", "view_knowledgebasedocument"),
            ("knowledge_base", "view_knowledgebaseattachment"),
        )
        attachment = quarantine_attachment(
            document=self.hidden_document,
            upload=SimpleUploadedFile(
                "hidden.txt",
                b"hidden",
                content_type="text/plain",
            ),
            uploader=self.staff,
        )

        response = self.client.get(
            f"/api/admin/knowledge-base/attachments/{attachment.id}/download"
        )

        self.assertEqual(response.status_code, 404)

    @patch.dict(os.environ, {"TICKETING_MALWARE_SCANNING_ENABLED": "0"})
    def test_delete_requires_explicit_attachment_permission(self) -> None:
        self.grant(
            ("knowledge_base", "change_knowledgebasedocument"),
            ("knowledge_base", "add_knowledgebaseattachment"),
        )
        upload = self._upload()
        attachment_id = upload.json()["id"]

        forbidden = self.client.delete(f"/api/admin/knowledge-base/attachments/{attachment_id}")
        self.assertEqual(forbidden.status_code, 403)

        self.grant(("knowledge_base", "delete_knowledgebaseattachment"))
        deleted = self.client.delete(f"/api/admin/knowledge-base/attachments/{attachment_id}")
        self.assertEqual(deleted.status_code, 200)
        self.assertFalse(KnowledgeBaseAttachment.objects.filter(id=attachment_id).exists())


class KnowledgeBaseAttachmentScanTests(TestCase):
    def setUp(self) -> None:
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.media.name)
        self.override.enable()
        self.addCleanup(self.override.disable)

        self.user = User.objects.create_user(
            email="kb-scan@example.test",
            password="test-password",
            first_name="KB",
            last_name="Scanner",
            is_staff=True,
        )
        section = KnowledgeBaseSection.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Internal",
        )
        document = KnowledgeBaseDocument.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            section=section,
            title="Internal runbook",
            content="# Runbook",
        )
        with patch.dict(os.environ, {"TICKETING_MALWARE_SCANNING_ENABLED": "0"}):
            self.attachment = quarantine_attachment(
                document=document,
                upload=SimpleUploadedFile(
                    "runbook.txt",
                    b"clean content",
                    content_type="text/plain",
                ),
                uploader=self.user,
            )

    @patch.dict(os.environ, {"TICKETING_MALWARE_SCANNING_ENABLED": "1"})
    @patch("apps.knowledge_base.tasks.clamav_scanner_from_environment")
    def test_clean_scan_releases_attachment(self, scanner_factory: Mock) -> None:
        scanner = Mock(engine_name="clamav")
        scanner.scan.return_value = AttachmentScanResult(clean=True)
        scanner_factory.return_value = scanner

        scan_knowledge_base_attachment(self.attachment.id)

        self.attachment.refresh_from_db()
        self.assertEqual(
            self.attachment.scan_status,
            KnowledgeBaseAttachment.ScanStatus.SAFE,
        )
        self.assertIsNotNone(self.attachment.safe_at)
        self.assertEqual(self.attachment.scan_result, "Clean")

    @patch.dict(os.environ, {"TICKETING_MALWARE_SCANNING_ENABLED": "1"})
    @patch("apps.knowledge_base.tasks.clamav_scanner_from_environment")
    def test_infected_scan_remains_quarantined(self, scanner_factory: Mock) -> None:
        scanner = Mock(engine_name="clamav")
        scanner.scan.return_value = AttachmentScanResult(
            clean=False,
            signature="Eicar-Test-Signature",
        )
        scanner_factory.return_value = scanner

        scan_knowledge_base_attachment(self.attachment.id)

        self.attachment.refresh_from_db()
        self.assertEqual(
            self.attachment.scan_status,
            KnowledgeBaseAttachment.ScanStatus.INFECTED,
        )
        self.assertIsNone(self.attachment.safe_at)
        self.assertEqual(self.attachment.scan_result, "Eicar-Test-Signature")

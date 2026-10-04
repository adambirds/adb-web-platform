import os
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.core.ownership import OwnershipType
from apps.knowledge_base.attachment_security import quarantine_attachment
from apps.knowledge_base.models import KnowledgeBaseDocument, KnowledgeBaseSection
from authentication.models import User


class KnowledgeBaseAttachmentProjectionTests(TestCase):
    def setUp(self) -> None:
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.media.name)
        self.override.enable()
        self.addCleanup(self.override.disable)

        self.staff = User.objects.create_user(
            email="kb-projection@example.test",
            password="test-password",
            first_name="KB",
            last_name="Operator",
            is_staff=True,
        )
        section = KnowledgeBaseSection.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Runbooks",
        )
        self.document = KnowledgeBaseDocument.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            section=section,
            title="Private attachment runbook",
            content="# Runbook",
        )
        with patch.dict(os.environ, {"TICKETING_MALWARE_SCANNING_ENABLED": "0"}):
            self.attachment = quarantine_attachment(
                document=self.document,
                upload=SimpleUploadedFile(
                    "diagram.png",
                    b"\x89PNG\r\n\x1a\ncontent",
                    content_type="image/png",
                ),
                uploader=self.staff,
            )
        self.client.force_login(self.staff)
        self._grant("view_knowledgebasedocument")

    def _grant(self, codename: str) -> None:
        permission = Permission.objects.get(
            content_type__app_label="knowledge_base",
            codename=codename,
        )
        self.staff.user_permissions.add(permission)

    def test_detail_hides_attachment_metadata_without_attachment_permission(self) -> None:
        response = self.client.get(f"/api/admin/knowledge-base/documents/{self.document.id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["attachments"], [])

    def test_detail_returns_safe_attachment_metadata_with_permission(self) -> None:
        self._grant("view_knowledgebaseattachment")

        response = self.client.get(f"/api/admin/knowledge-base/documents/{self.document.id}")

        self.assertEqual(response.status_code, 200)
        attachment = response.json()["attachments"][0]
        self.assertEqual(attachment["id"], self.attachment.id)
        self.assertEqual(attachment["scan_status"], "pending")
        self.assertEqual(attachment["detected_content_type"], "image/png")
        self.assertNotIn("file", attachment)
        self.assertNotIn("sha256", attachment)
        self.assertNotIn("scan_result", attachment)

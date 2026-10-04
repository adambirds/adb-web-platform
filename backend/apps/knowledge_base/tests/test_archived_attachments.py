from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.core.ownership import OwnershipType
from apps.knowledge_base.models import (
    KnowledgeBaseAttachment,
    KnowledgeBaseDocument,
    KnowledgeBaseSection,
)
from apps.knowledge_base.services import archive_document
from authentication.models import User


class ArchivedKnowledgeBaseAttachmentTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="kb-archived-attachment@example.test",
            password="test-password",
            first_name="KB",
            last_name="Archive",
            is_staff=True,
        )
        for codename in (
            "change_knowledgebasedocument",
            "add_knowledgebaseattachment",
        ):
            self.user.user_permissions.add(
                Permission.objects.get(
                    content_type__app_label="knowledge_base",
                    codename=codename,
                )
            )
        section = KnowledgeBaseSection.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Archived runbooks",
        )
        self.document = KnowledgeBaseDocument.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            section=section,
            title="Archived attachment runbook",
            content="# Archived",
        )
        archive_document(self.document.id, editor=self.user)
        self.client.force_login(self.user)

    def test_archived_document_rejects_attachment_upload(self) -> None:
        response = self.client.post(
            f"/api/admin/knowledge-base/documents/{self.document.id}/attachments",
            {
                "file": SimpleUploadedFile(
                    "archived.txt",
                    b"archived",
                    content_type="text/plain",
                )
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "document_archived")
        self.assertFalse(KnowledgeBaseAttachment.objects.filter(document=self.document).exists())

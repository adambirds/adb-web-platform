from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.knowledge_base.models import DocumentVersion, KnowledgeBaseDocument, KnowledgeBaseSection
from apps.knowledge_base.services import (
    DocumentWrite,
    archive_document,
    create_document,
    restore_document,
    update_document,
)
from authentication.models import User


class KnowledgeBaseDocumentServiceTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="editor@example.test",
            password="TestPassword123!",
            first_name="Editor",
            last_name="User",
            is_staff=True,
        )
        self.client_record = Client.objects.create(
            name="Client",
            company="Client Ltd",
            email="client@example.test",
        )
        self.other_client_record = Client.objects.create(
            name="Other",
            company="Other Ltd",
            email="other@example.test",
        )
        self.section = KnowledgeBaseSection.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_record,
            name="Operations",
        )
        self.other_section = KnowledgeBaseSection.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.other_client_record,
            name="Operations",
        )

    def _write(
        self,
        *,
        title: str = "Deployment runbook",
        content: str = "# Deploy",
        section: KnowledgeBaseSection | None = None,
        change_summary: str = "",
    ) -> DocumentWrite:
        return DocumentWrite(
            ownership_type=OwnershipType.CLIENT,
            client_id=self.client_record.id,
            title=title,
            summary="Safe deployment steps.",
            section=section or self.section,
            content=content,
            change_summary=change_summary,
        )

    def test_create_document_creates_initial_immutable_version(self) -> None:
        document = create_document(write=self._write(), editor=self.user)

        version = document.versions.get()
        self.assertEqual(version.version_number, 1)
        self.assertEqual(version.title, "Deployment runbook")
        self.assertEqual(version.content, "# Deploy")
        self.assertEqual(version.section_path, "Operations")
        self.assertEqual(version.editor, self.user)
        self.assertEqual(version.change_summary, "Initial version")

    def test_content_update_creates_next_version(self) -> None:
        document = create_document(write=self._write(), editor=self.user)

        updated = update_document(
            document.id,
            write=self._write(
                content="# Deploy\n\n1. Verify health.",
                change_summary="Add health verification",
            ),
            editor=self.user,
        )

        self.assertEqual(updated.versions.count(), 2)
        latest = updated.versions.first()
        assert latest is not None
        self.assertEqual(latest.version_number, 2)
        self.assertEqual(latest.change_summary, "Add health verification")
        self.assertEqual(latest.content, "# Deploy\n\n1. Verify health.")

    def test_metadata_only_update_does_not_create_content_version(self) -> None:
        document = create_document(write=self._write(), editor=self.user)
        write = self._write()
        write = DocumentWrite(
            ownership_type=write.ownership_type,
            client_id=write.client_id,
            title=write.title,
            summary="Updated summary only.",
            section=write.section,
            content=write.content,
        )

        updated = update_document(document.id, write=write, editor=self.user)

        self.assertEqual(updated.summary, "Updated summary only.")
        self.assertEqual(updated.versions.count(), 1)

    def test_update_rejects_ownership_scope_move(self) -> None:
        document = create_document(write=self._write(), editor=self.user)
        moved = DocumentWrite(
            ownership_type=OwnershipType.CLIENT,
            client_id=self.other_client_record.id,
            title=document.title,
            summary=document.summary,
            section=self.other_section,
            content=document.content,
        )

        with self.assertRaises(ValidationError):
            update_document(document.id, write=moved, editor=self.user)

    def test_archived_document_must_be_restored_before_editing(self) -> None:
        document = create_document(write=self._write(), editor=self.user)
        archive_document(document.id, editor=self.user)

        with self.assertRaisesMessage(
            ValidationError,
            "Restore an archived Knowledge Base document before editing it.",
        ):
            update_document(
                document.id,
                write=self._write(content="# Changed while archived"),
                editor=self.user,
            )

        document.refresh_from_db()
        self.assertEqual(document.content, "# Deploy")
        self.assertEqual(document.versions.count(), 1)

    def test_archive_and_restore_preserve_document_and_versions(self) -> None:
        document = create_document(write=self._write(), editor=self.user)

        archived = archive_document(document.id, editor=self.user)
        self.assertIsNotNone(archived.archived_at)
        self.assertTrue(KnowledgeBaseDocument.objects.filter(id=document.id).exists())
        self.assertEqual(DocumentVersion.objects.filter(document=document).count(), 1)

        restored = restore_document(document.id, editor=self.user)
        self.assertIsNone(restored.archived_at)
        self.assertEqual(DocumentVersion.objects.filter(document=document).count(), 1)

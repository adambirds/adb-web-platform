from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.credentials.models import StoredCredential
from apps.infrastructure.models import InfrastructureResource
from apps.knowledge_base.models import (
    DocumentVersion,
    KnowledgeBaseCredentialLink,
    KnowledgeBaseDocument,
    KnowledgeBaseResourceLink,
    KnowledgeBaseSection,
)


class KnowledgeBaseModelTests(TestCase):
    def setUp(self) -> None:
        self.first_client = Client.objects.create(
            name="First",
            company="First Ltd",
            email="first@example.test",
        )
        self.second_client = Client.objects.create(
            name="Second",
            company="Second Ltd",
            email="second@example.test",
        )
        self.internal_section = KnowledgeBaseSection.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Internal",
        )
        self.client_section = KnowledgeBaseSection.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.first_client,
            name="Operations",
        )

    def test_nested_section_requires_same_ownership_scope(self) -> None:
        child = KnowledgeBaseSection(
            ownership_type=OwnershipType.CLIENT,
            client=self.first_client,
            parent=self.internal_section,
            name="Runbooks",
        )

        with self.assertRaises(ValidationError):
            child.full_clean()

    def test_section_cycle_is_rejected(self) -> None:
        parent = KnowledgeBaseSection.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Parent",
        )
        child = KnowledgeBaseSection.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            parent=parent,
            name="Child",
        )
        parent.parent = child

        with self.assertRaises(ValidationError):
            parent.full_clean()

    def test_document_requires_section_in_same_scope(self) -> None:
        document = KnowledgeBaseDocument(
            ownership_type=OwnershipType.CLIENT,
            client=self.first_client,
            title="Client runbook",
            section=self.internal_section,
            content="# Runbook",
        )

        with self.assertRaises(ValidationError):
            document.full_clean()

    def test_resource_link_rejects_cross_client_resource(self) -> None:
        document = KnowledgeBaseDocument.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.first_client,
            title="Client runbook",
            section=self.client_section,
            content="# Runbook",
        )
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.second_client,
            name="Other client server",
            resource_type=InfrastructureResource.ResourceType.SERVER,
        )
        link = KnowledgeBaseResourceLink(document=document, resource=resource)

        with self.assertRaises(ValidationError):
            link.full_clean()

    def test_credential_link_rejects_cross_client_credential(self) -> None:
        document = KnowledgeBaseDocument.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.first_client,
            title="Client runbook",
            section=self.client_section,
            content="# Runbook",
        )
        credential = StoredCredential.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.second_client,
            name="Other client credential",
        )
        link = KnowledgeBaseCredentialLink(document=document, credential=credential)

        with self.assertRaises(ValidationError):
            link.full_clean()

    def test_document_version_cannot_be_modified_after_creation(self) -> None:
        document = KnowledgeBaseDocument.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            title="Internal runbook",
            section=self.internal_section,
            content="# Runbook",
        )
        version = DocumentVersion.objects.create(
            document=document,
            version_number=1,
            title=document.title,
            content=document.content,
            section_path=self.internal_section.path,
        )
        version.content = "# Changed"

        with self.assertRaises(ValidationError):
            version.save()

from django.contrib.auth.models import Permission
from django.test import TestCase

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.credentials.models import CredentialType, StoredCredential
from apps.knowledge_base.models import KnowledgeBaseDocument, KnowledgeBaseSection
from authentication.models import User


class AdminResourceAPITests(TestCase):
    def setUp(self) -> None:
        self.staff = User.objects.create_user(
            email="resource-staff@example.com",
            password="test-password",
            is_staff=True,
        )
        self.profile = StaffAccessProfile.objects.create(user=self.staff)
        self.allowed_client = Client.objects.create(
            name="Allowed Contact",
            company="Allowed Client",
            email="allowed-resource@example.test",
        )
        self.hidden_client = Client.objects.create(
            name="Hidden Contact",
            company="Hidden Client",
            email="hidden-resource@example.test",
        )
        ClientAccessGrant.objects.create(
            profile=self.profile,
            client=self.allowed_client,
            granted_by=self.staff,
        )

        credential_type = CredentialType.objects.create(name="Resource Test Login")
        StoredCredential.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Internal Credential",
            credential_type=credential_type,
            username="internal-user",
            password="internal-secret",
            api_key="internal-api-key",
        )
        StoredCredential.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.allowed_client,
            name="Allowed Credential",
            credential_type=credential_type,
            username="allowed-user",
            password="allowed-secret",
            secret_key="allowed-secret-key",
        )
        StoredCredential.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.hidden_client,
            name="Hidden Credential",
            credential_type=credential_type,
            username="hidden-user",
            private_key="hidden-private-key",
        )

        section = KnowledgeBaseSection.objects.create(
            name="Resource Test Section",
            order=1,
        )
        KnowledgeBaseDocument.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            title="Internal Document",
            section=section,
            content="Internal test content",
        )
        KnowledgeBaseDocument.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.allowed_client,
            title="Allowed Document",
            section=section,
            content="Allowed test content",
        )
        KnowledgeBaseDocument.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.hidden_client,
            title="Hidden Document",
            section=section,
            content="Hidden test content",
        )

        self.client.force_login(self.staff)

    def grant(self, app_label: str, codename: str) -> None:
        permission = Permission.objects.get(
            content_type__app_label=app_label,
            codename=codename,
        )
        self.staff.user_permissions.add(permission)

    def test_credentials_require_permission_and_respect_client_scope(self) -> None:
        denied = self.client.get("/api/admin/credentials")
        self.assertEqual(denied.status_code, 403)

        self.grant("credentials", "view_storedcredential")
        allowed = self.client.get("/api/admin/credentials")

        self.assertEqual(allowed.status_code, 200)
        names = {credential["name"] for credential in allowed.json()}
        self.assertSetEqual(names, {"Internal Credential", "Allowed Credential"})
        for credential in allowed.json():
            self.assertNotIn("password", credential)
            self.assertNotIn("api_key", credential)
            self.assertNotIn("secret_key", credential)
            self.assertNotIn("private_key", credential)

    def test_knowledge_base_requires_permission_and_respects_client_scope(self) -> None:
        denied = self.client.get("/api/admin/knowledge-base")
        self.assertEqual(denied.status_code, 403)

        self.grant("knowledge_base", "view_knowledgebasedocument")
        allowed = self.client.get("/api/admin/knowledge-base")

        self.assertEqual(allowed.status_code, 200)
        titles = {document["title"] for document in allowed.json()}
        self.assertSetEqual(titles, {"Internal Document", "Allowed Document"})

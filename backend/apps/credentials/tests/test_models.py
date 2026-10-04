from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.credentials.models import CredentialResourceLink, CredentialType, StoredCredential
from apps.infrastructure.models import InfrastructureResource


class CredentialVaultModelTests(TestCase):
    def setUp(self) -> None:
        self.client_a = Client.objects.create(
            name="Client A",
            company="Client A Ltd",
            email="client-a@example.test",
        )
        self.client_b = Client.objects.create(
            name="Client B",
            company="Client B Ltd",
            email="client-b@example.test",
        )
        self.internal_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="ADB shared Cloudflare account",
            resource_type=InfrastructureResource.ResourceType.PROVIDER_ACCOUNT,
        )
        self.client_a_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_a,
            name="Client A website",
            resource_type=InfrastructureResource.ResourceType.WEBSITE,
        )
        self.client_b_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_b,
            name="Client B website",
            resource_type=InfrastructureResource.ResourceType.WEBSITE,
        )

    def test_builtin_ssh_template_is_seeded(self) -> None:
        credential_type = CredentialType.objects.get(slug="ssh-key")

        private_key = next(
            field for field in credential_type.field_schema if field["key"] == "private_key"
        )
        self.assertTrue(credential_type.is_system)
        self.assertEqual(private_key["storage"], "secret")
        self.assertTrue(private_key["required"])

    def test_legacy_type_creation_generates_unique_slug(self) -> None:
        first = CredentialType.objects.create(name="Legacy portal login")
        second = CredentialType.objects.create(name="API key")

        self.assertEqual(first.slug, "legacy-portal-login")
        self.assertTrue(second.slug.startswith("api-key-"))
        self.assertNotEqual(second.slug, CredentialType.objects.get(name="API key or token").slug)

    def test_internal_credential_can_link_to_internal_and_client_resources(self) -> None:
        credential = StoredCredential.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="ADB shared token",
        )

        for resource in (self.internal_resource, self.client_a_resource):
            link = CredentialResourceLink(credential=credential, resource=resource)
            link.full_clean()
            link.save()

        self.assertEqual(credential.resource_links.count(), 2)

    def test_client_credential_can_link_to_same_client_resource(self) -> None:
        credential = StoredCredential.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_a,
            name="Client A WordPress login",
        )
        link = CredentialResourceLink(
            credential=credential,
            resource=self.client_a_resource,
        )

        link.full_clean()
        link.save()

        self.assertEqual(link.resource, self.client_a_resource)

    def test_client_credential_cannot_link_to_internal_resource(self) -> None:
        credential = StoredCredential.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_a,
            name="Client A login",
        )
        link = CredentialResourceLink(
            credential=credential,
            resource=self.internal_resource,
        )

        with self.assertRaises(ValidationError):
            link.full_clean()

    def test_client_credential_cannot_link_across_clients(self) -> None:
        credential = StoredCredential.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_a,
            name="Client A login",
        )
        link = CredentialResourceLink(
            credential=credential,
            resource=self.client_b_resource,
        )

        with self.assertRaises(ValidationError):
            link.full_clean()

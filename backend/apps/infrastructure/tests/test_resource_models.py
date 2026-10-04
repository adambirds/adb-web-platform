from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.infrastructure.models import (
    InfrastructureResource,
    InfrastructureTag,
    ProviderAccount,
    ResourceRelationship,
    ServiceProvider,
)


class InfrastructureResourceModelTests(TestCase):
    def setUp(self) -> None:
        self.client_a = Client.objects.create(
            name="Client A",
            email="client-a@example.com",
        )
        self.client_b = Client.objects.create(
            name="Client B",
            email="client-b@example.com",
        )

    def _client_resource(
        self,
        client: Client,
        name: str,
        *,
        resource_type: str = InfrastructureResource.ResourceType.SERVER,
    ) -> InfrastructureResource:
        return InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=client,
            name=name,
            resource_type=resource_type,
        )

    def _internal_resource(
        self,
        name: str,
        *,
        resource_type: str = InfrastructureResource.ResourceType.SERVER,
    ) -> InfrastructureResource:
        return InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name=name,
            resource_type=resource_type,
        )

    def test_resource_ownership_requires_matching_client_state(self) -> None:
        missing_client = InfrastructureResource(
            ownership_type=OwnershipType.CLIENT,
            name="Client server",
            resource_type=InfrastructureResource.ResourceType.SERVER,
        )
        with self.assertRaises(ValidationError):
            missing_client.full_clean()

        internal_with_client = InfrastructureResource(
            ownership_type=OwnershipType.INTERNAL,
            client=self.client_a,
            name="Invalid internal server",
            resource_type=InfrastructureResource.ResourceType.SERVER,
        )
        with self.assertRaises(ValidationError):
            internal_with_client.full_clean()

    def test_tags_can_be_shared_across_resources(self) -> None:
        tag = InfrastructureTag.objects.create(name="Production", slug="production")
        first = self._internal_resource("Internal server")
        second = self._client_resource(self.client_a, "Client server")

        first.tags.add(tag)
        second.tags.add(tag)

        self.assertEqual(set(tag.resources.values_list("id", flat=True)), {first.id, second.id})

    def test_same_client_resources_can_be_related(self) -> None:
        application = self._client_resource(
            self.client_a,
            "Client application",
            resource_type=InfrastructureResource.ResourceType.APPLICATION,
        )
        server = self._client_resource(self.client_a, "Client server")
        relationship = ResourceRelationship(
            source_resource=application,
            target_resource=server,
            relationship_type=ResourceRelationship.RelationshipType.HOSTED_ON,
        )

        relationship.full_clean()
        relationship.save()

        self.assertEqual(application.outgoing_relationships.get(), relationship)

    def test_cross_client_relationship_is_rejected(self) -> None:
        source = self._client_resource(self.client_a, "Client A app")
        target = self._client_resource(self.client_b, "Client B server")
        relationship = ResourceRelationship(
            source_resource=source,
            target_resource=target,
            relationship_type=ResourceRelationship.RelationshipType.DEPENDS_ON,
        )

        with self.assertRaisesMessage(
            ValidationError,
            "Client-owned resources cannot be related across different clients.",
        ):
            relationship.full_clean()

    def test_internal_and_client_resources_can_be_related(self) -> None:
        shared_server = self._internal_resource("ADB shared server")
        client_site = self._client_resource(
            self.client_a,
            "Client website",
            resource_type=InfrastructureResource.ResourceType.WEBSITE,
        )
        relationship = ResourceRelationship(
            source_resource=client_site,
            target_resource=shared_server,
            relationship_type=ResourceRelationship.RelationshipType.HOSTED_ON,
        )

        relationship.full_clean()
        relationship.save()

        self.assertEqual(client_site.outgoing_relationships.get(), relationship)

    def test_self_relationship_is_rejected(self) -> None:
        resource = self._internal_resource("Server")
        relationship = ResourceRelationship(
            source_resource=resource,
            target_resource=resource,
            relationship_type=ResourceRelationship.RelationshipType.RELATED_TO,
        )

        with self.assertRaisesMessage(ValidationError, "A resource cannot be related to itself."):
            relationship.full_clean()

    def test_provider_account_requires_provider_account_resource(self) -> None:
        provider = ServiceProvider.objects.create(
            name="DigitalOcean",
            slug="digitalocean",
            category=ServiceProvider.Category.CLOUD,
        )
        wrong_resource = self._internal_resource("Wrong resource")
        invalid_account = ProviderAccount(
            resource=wrong_resource,
            provider=provider,
        )
        with self.assertRaises(ValidationError):
            invalid_account.full_clean()

        account_resource = self._internal_resource(
            "ADB DigitalOcean",
            resource_type=InfrastructureResource.ResourceType.PROVIDER_ACCOUNT,
        )
        account = ProviderAccount(
            resource=account_resource,
            provider=provider,
            account_identifier="adb-production",
        )
        account.full_clean()
        account.save()

        self.assertEqual(account_resource.provider_account, account)

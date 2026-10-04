from __future__ import annotations

from django.contrib.auth.models import Permission
from django.test import TestCase

from apps.access_control.models import StaffAccessProfile
from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.infrastructure.models import InfrastructureResource, ResourceRelationship
from authentication.models import User


class InfrastructureTopologyAPITests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="topology@example.test",
            password="test-password",
            first_name="Topology",
            last_name="User",
            is_staff=True,
        )
        self.allowed_client = Client.objects.create(
            name="Allowed",
            company="Allowed Ltd",
            email="allowed@example.test",
        )
        self.hidden_client = Client.objects.create(
            name="Hidden",
            company="Hidden Ltd",
            email="hidden@example.test",
        )
        profile = StaffAccessProfile.objects.create(user=self.user)
        profile.client_grants.create(client=self.allowed_client)
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="infrastructure",
                codename="view_infrastructureresource",
            )
        )
        self.client.force_login(self.user)

    def _resource(
        self,
        name: str,
        *,
        ownership_type: str = OwnershipType.CLIENT,
        client: Client | None = None,
    ) -> InfrastructureResource:
        return InfrastructureResource.objects.create(
            ownership_type=ownership_type,
            client=client,
            name=name,
            resource_type=InfrastructureResource.ResourceType.APPLICATION,
        )

    def test_topology_hides_relationships_to_inaccessible_resources(self) -> None:
        root = self._resource("Allowed app", client=self.allowed_client)
        neighbour = self._resource("Allowed database", client=self.allowed_client)
        hidden = self._resource("Hidden app", client=self.hidden_client)
        ResourceRelationship.objects.create(
            source_resource=root,
            target_resource=neighbour,
            relationship_type=ResourceRelationship.RelationshipType.DEPENDS_ON,
        )
        ResourceRelationship.objects.create(
            source_resource=root,
            target_resource=hidden,
            relationship_type=ResourceRelationship.RelationshipType.RELATED_TO,
        )

        response = self.client.get(
            f"/api/admin/infrastructure/resources/{root.id}/topology",
            {"depth": "1"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual({node["id"] for node in payload["nodes"]}, {root.id, neighbour.id})
        self.assertEqual(len(payload["edges"]), 1)
        self.assertEqual(payload["edges"][0]["target_id"], neighbour.id)

    def test_depth_two_discovers_bounded_second_hop(self) -> None:
        root = self._resource("Root", client=self.allowed_client)
        neighbour = self._resource("Neighbour", client=self.allowed_client)
        internal = self._resource(
            "Internal dependency",
            ownership_type=OwnershipType.INTERNAL,
        )
        ResourceRelationship.objects.create(
            source_resource=root,
            target_resource=neighbour,
            relationship_type=ResourceRelationship.RelationshipType.DEPENDS_ON,
        )
        ResourceRelationship.objects.create(
            source_resource=neighbour,
            target_resource=internal,
            relationship_type=ResourceRelationship.RelationshipType.CONNECTS_TO,
        )

        response = self.client.get(
            f"/api/admin/infrastructure/resources/{root.id}/topology",
            {"depth": "2"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {node["id"] for node in response.json()["nodes"]},
            {root.id, neighbour.id, internal.id},
        )
        self.assertEqual(len(response.json()["edges"]), 2)

    def test_hidden_root_is_not_discoverable(self) -> None:
        hidden = self._resource("Hidden root", client=self.hidden_client)

        response = self.client.get(f"/api/admin/infrastructure/resources/{hidden.id}/topology")

        self.assertEqual(response.status_code, 404)

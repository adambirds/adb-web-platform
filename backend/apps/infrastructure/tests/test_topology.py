from __future__ import annotations

from django.contrib.auth.models import Permission
from django.test import TestCase

from apps.access_control.models import StaffAccessProfile
from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.credentials.models import CredentialResourceLink, StoredCredential
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

    def test_credential_links_require_metadata_permission_and_never_return_secrets(self) -> None:
        root = self._resource("Server", client=self.allowed_client)
        credential = StoredCredential.objects.create(
            name="SSH login",
            ownership_type="client",
            client=self.allowed_client,
            encrypted_secret_payload="ciphertext-must-not-appear",
        )
        CredentialResourceLink.objects.create(
            resource=root, credential=credential, purpose="SSH access"
        )
        url = f"/api/admin/infrastructure/resources/{root.id}/topology"
        payload = self.client.get(url).json()
        self.assertEqual(payload["edges"], [])
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="credentials", codename="view_storedcredential"
            )
        )
        response = self.client.get(url)
        payload = response.json()
        self.assertEqual(len(payload["edges"]), 1)
        node = next(node for node in payload["nodes"] if node["resource_type"] == "credential")
        self.assertEqual(node["href"], f"/admin/credentials/{credential.id}")
        self.assertEqual(payload["edges"][0]["target_id"], node["id"])
        self.assertNotContains(response, "ciphertext-must-not-appear")
        self.assertNotIn("encrypted_secret_payload", node)

    def test_topology_hides_out_of_scope_and_archived_credentials(self) -> None:
        root = self._resource("Server", client=self.allowed_client)
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="credentials", codename="view_storedcredential"
            )
        )
        for client, status in [(self.hidden_client, "active"), (self.allowed_client, "archived")]:
            credential = StoredCredential.objects.create(
                name=f"Hidden {status}", ownership_type="client", client=client, status=status
            )
            CredentialResourceLink.objects.create(resource=root, credential=credential)
        payload = self.client.get(f"/api/admin/infrastructure/resources/{root.id}/topology").json()
        self.assertEqual(payload["edges"], [])
        self.assertEqual(len(payload["nodes"]), 1)

    def test_credentials_on_neighbour_resources_require_two_hops(self) -> None:
        root = self._resource("Application", client=self.allowed_client)
        server = self._resource("Server", client=self.allowed_client)
        ResourceRelationship.objects.create(
            source_resource=root, target_resource=server, relationship_type="hosted_on"
        )
        credential = StoredCredential.objects.create(name="SSH", ownership_type="internal")
        CredentialResourceLink.objects.create(resource=server, credential=credential)
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="credentials", codename="view_storedcredential"
            )
        )
        url = f"/api/admin/infrastructure/resources/{root.id}/topology"
        one = self.client.get(url, {"depth": 1}).json()
        two = self.client.get(url, {"depth": 2}).json()
        self.assertEqual(len(one["edges"]), 1)
        self.assertEqual(len(two["edges"]), 2)
        self.assertTrue(any(node["resource_type"] == "credential" for node in two["nodes"]))

from typing import cast

from django.contrib.auth.models import Permission
from django.http import HttpRequest
from django.test import RequestFactory, TestCase

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.infrastructure.models import (
    InfrastructureResource,
    IPAddress,
    Network,
    NetworkInterface,
    ProviderAccount,
    ServerProfile,
    ServiceProvider,
    Subnet,
)
from apps.infrastructure.ninja.specialist_schemas import (
    InfrastructureSpecialistOptionsOut,
    IPAddressCreateIn,
    IPAddressOut,
    NetworkInterfaceCreateIn,
    NetworkInterfaceOut,
    ServerCreateIn,
    ServerOut,
)
from apps.infrastructure.ninja.specialist_views import (
    archive_server,
    create_ip_address,
    create_network_interface,
    create_server,
    get_server,
    infrastructure_specialist_options,
)
from authentication.models import User


class InfrastructureSpecialistApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.client_a = Client.objects.create(
            name="Client A",
            company="Client A Ltd",
            email="client-a@example.com",
            status="active",
        )
        self.client_b = Client.objects.create(
            name="Client B",
            company="Client B Ltd",
            email="client-b@example.com",
            status="active",
        )
        provider = ServiceProvider.objects.create(
            name="DigitalOcean",
            slug="digitalocean",
            category=ServiceProvider.Category.CLOUD,
        )
        internal_provider_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="ADB DigitalOcean",
            resource_type=InfrastructureResource.ResourceType.PROVIDER_ACCOUNT,
        )
        self.internal_provider = ProviderAccount.objects.create(
            resource=internal_provider_resource,
            provider=provider,
        )
        client_b_provider_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_b,
            name="Client B Cloud",
            resource_type=InfrastructureResource.ResourceType.PROVIDER_ACCOUNT,
        )
        self.client_b_provider = ProviderAccount.objects.create(
            resource=client_b_provider_resource,
            provider=provider,
        )

    def _request(self, user: User) -> HttpRequest:
        request = self.factory.get("/api/admin/infrastructure/servers")
        request.user = user
        return request

    def _user(self, email: str, codenames: list[str]) -> User:
        user = User.objects.create_user(
            email=email,
            password="test-password",
            first_name="Infra",
            last_name="Operator",
            is_staff=True,
        )
        permissions = Permission.objects.filter(
            content_type__app_label="infrastructure",
            codename__in=codenames,
        )
        user.user_permissions.add(*permissions)
        return user

    def _grant_client(self, user: User, client: Client) -> None:
        profile = StaffAccessProfile.objects.create(user=user)
        ClientAccessGrant.objects.create(profile=profile, client=client)

    def test_create_client_server_with_internal_provider_is_atomic(self) -> None:
        user = self._user(
            "server-create@example.com",
            ["add_infrastructureresource", "add_serverprofile"],
        )
        self._grant_client(user, self.client_a)

        status, result = create_server(
            self._request(user),
            ServerCreateIn(
                ownership_type="client",
                client_id=self.client_a.id,
                name="Client A Production Web",
                hostname="client-a-web01",
                environment="production",
                provider_account_resource_id=self.internal_provider.resource_id,
                distribution="Ubuntu",
                os_version="24.04",
                ssh_port=22,
            ),
        )

        self.assertEqual(status, 201)
        server = cast(ServerOut, result)
        self.assertEqual(server.hostname, "client-a-web01")
        self.assertEqual(server.client_id, self.client_a.id)
        self.assertEqual(
            server.provider_account_resource_id,
            self.internal_provider.resource_id,
        )
        self.assertTrue(ServerProfile.objects.filter(resource_id=server.resource_id).exists())

    def test_create_server_rejects_inaccessible_provider_without_orphan_resource(self) -> None:
        user = self._user(
            "server-provider-scope@example.com",
            ["add_infrastructureresource", "add_serverprofile"],
        )
        self._grant_client(user, self.client_a)
        before = InfrastructureResource.objects.count()

        status, payload = create_server(
            self._request(user),
            ServerCreateIn(
                ownership_type="client",
                client_id=self.client_a.id,
                name="Client A Production Web",
                hostname="client-a-web01",
                provider_account_resource_id=self.client_b_provider.resource_id,
            ),
        )

        self.assertEqual(status, 404)
        self.assertEqual(cast(dict[str, object], payload)["code"], "not_found")
        self.assertEqual(InfrastructureResource.objects.count(), before)

    def test_invalid_server_does_not_leave_orphan_resource(self) -> None:
        user = self._user(
            "server-invalid@example.com",
            ["add_infrastructureresource", "add_serverprofile"],
        )
        before = InfrastructureResource.objects.count()

        status, _ = create_server(
            self._request(user),
            ServerCreateIn(
                name="Invalid server",
                hostname="invalid-server",
                ssh_port=70000,
            ),
        )

        self.assertEqual(status, 400)
        self.assertEqual(InfrastructureResource.objects.count(), before)
        self.assertFalse(ServerProfile.objects.filter(hostname="invalid-server").exists())

    def test_server_detail_respects_client_scope(self) -> None:
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_b,
            name="Client B server",
            resource_type=InfrastructureResource.ResourceType.SERVER,
        )
        ServerProfile.objects.create(resource=resource, hostname="client-b-web01")
        user = self._user(
            "server-scope@example.com",
            ["view_infrastructureresource", "view_serverprofile"],
        )
        self._grant_client(user, self.client_a)

        result = get_server(self._request(user), resource.id)

        self.assertIsInstance(result, tuple)
        status, payload = cast(tuple[int, dict[str, object]], result)
        self.assertEqual(status, 404)
        self.assertEqual(payload["code"], "not_found")

    def test_archive_server_uses_resource_lifecycle(self) -> None:
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Server",
            resource_type=InfrastructureResource.ResourceType.SERVER,
        )
        ServerProfile.objects.create(resource=resource, hostname="adb-lon-ws01")
        user = self._user(
            "server-archive@example.com",
            ["change_infrastructureresource", "change_serverprofile"],
        )

        result = cast(ServerOut, archive_server(self._request(user), resource.id))

        resource.refresh_from_db()
        self.assertEqual(
            resource.lifecycle_status,
            InfrastructureResource.LifecycleStatus.ARCHIVED,
        )
        self.assertIsNotNone(resource.archived_at)
        self.assertEqual(result.lifecycle_status, "archived")

    def test_options_only_return_accessible_clients_and_resources(self) -> None:
        network_a_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_a,
            name="Client A Network",
            resource_type=InfrastructureResource.ResourceType.NETWORK,
        )
        Network.objects.create(resource=network_a_resource, cidr="10.10.0.0/16")
        network_b_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_b,
            name="Client B Network",
            resource_type=InfrastructureResource.ResourceType.NETWORK,
        )
        Network.objects.create(resource=network_b_resource, cidr="10.20.0.0/16")
        user = self._user("options@example.com", ["view_infrastructureresource"])
        self._grant_client(user, self.client_a)

        result = cast(
            InfrastructureSpecialistOptionsOut,
            infrastructure_specialist_options(self._request(user)),
        )

        self.assertEqual([client.id for client in result.clients], [self.client_a.id])
        self.assertIn(
            self.internal_provider.resource_id,
            {item.resource_id for item in result.provider_accounts},
        )
        self.assertNotIn(
            self.client_b_provider.resource_id,
            {item.resource_id for item in result.provider_accounts},
        )
        self.assertEqual(
            [item.resource_id for item in result.networks],
            [network_a_resource.id],
        )

    def test_interface_and_ip_address_follow_server_resource(self) -> None:
        server_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Server",
            resource_type=InfrastructureResource.ResourceType.SERVER,
        )
        ServerProfile.objects.create(resource=server_resource, hostname="adb-lon-ws01")
        network_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Production VPC",
            resource_type=InfrastructureResource.ResourceType.NETWORK,
        )
        network = Network.objects.create(resource=network_resource, cidr="10.10.0.0/16")
        subnet_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Web subnet",
            resource_type=InfrastructureResource.ResourceType.SUBNET,
        )
        Subnet.objects.create(
            resource=subnet_resource,
            network=network,
            cidr="10.10.10.0/24",
        )
        user = self._user(
            "interface@example.com",
            [
                "view_infrastructureresource",
                "view_serverprofile",
                "add_networkinterface",
                "add_ipaddress",
            ],
        )

        interface_status, interface_result = create_network_interface(
            self._request(user),
            server_resource.id,
            NetworkInterfaceCreateIn(
                name="eth0",
                network_resource_id=network_resource.id,
                subnet_resource_id=subnet_resource.id,
            ),
        )
        self.assertEqual(interface_status, 201)
        interface = cast(NetworkInterfaceOut, interface_result)
        interface_id = interface.id

        ip_status, ip_result = create_ip_address(
            self._request(user),
            server_resource.id,
            IPAddressCreateIn(
                address="10.10.10.12",
                interface_id=interface_id,
                is_primary=True,
            ),
        )

        self.assertEqual(ip_status, 201)
        ip_address = cast(IPAddressOut, ip_result)
        saved_ip = IPAddress.objects.get(id=ip_address.id)
        self.assertEqual(saved_ip.resource_id, server_resource.id)
        self.assertEqual(saved_ip.interface_id, interface_id)
        self.assertTrue(
            NetworkInterface.objects.filter(
                id=interface_id,
                server__resource=server_resource,
            ).exists()
        )

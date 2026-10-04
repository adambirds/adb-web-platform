from typing import cast

from django.contrib.auth.models import Permission
from django.http import HttpRequest
from django.test import RequestFactory, TestCase

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.infrastructure.models import (
    InfrastructureResource,
    Network,
    ProviderAccount,
    ServerProfile,
    ServiceProvider,
    Subnet,
)
from apps.infrastructure.ninja.specialist_edit_views import (
    InfrastructureSpecialistEditOut,
    get_infrastructure_specialist_edit_details,
)
from authentication.models import User


class InfrastructureSpecialistEditApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.client_a = Client.objects.create(
            name="Client A",
            company="Client A Ltd",
            email="client-a-edit@example.com",
            status="active",
        )
        self.client_b = Client.objects.create(
            name="Client B",
            company="Client B Ltd",
            email="client-b-edit@example.com",
            status="active",
        )
        provider = ServiceProvider.objects.create(
            name="DigitalOcean Edit",
            slug="digitalocean-edit",
            category=ServiceProvider.Category.CLOUD,
        )
        provider_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="ADB Cloud Account",
            resource_type=InfrastructureResource.ResourceType.PROVIDER_ACCOUNT,
        )
        self.provider_account = ProviderAccount.objects.create(
            resource=provider_resource,
            provider=provider,
        )

    def _user(self, email: str) -> User:
        user = User.objects.create_user(
            email=email,
            password="test-password",
            first_name="Infra",
            last_name="Editor",
            is_staff=True,
        )
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="infrastructure",
                codename="view_infrastructureresource",
            )
        )
        return user

    def _request(self, user: User) -> HttpRequest:
        request = self.factory.get("/api/admin/infrastructure/resources/1/specialist-edit")
        request.user = user
        return request

    def _grant_client(self, user: User, client: Client) -> None:
        profile = StaffAccessProfile.objects.create(user=user)
        ClientAccessGrant.objects.create(profile=profile, client=client)

    def test_server_edit_details_return_exact_safe_values(self) -> None:
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="ADB production server",
            resource_type=InfrastructureResource.ResourceType.SERVER,
            environment=InfrastructureResource.Environment.PRODUCTION,
            criticality=InfrastructureResource.Criticality.HIGH,
        )
        ServerProfile.objects.create(
            resource=resource,
            hostname="adb-lon-ws01",
            compute_type=ServerProfile.ComputeType.CLOUD_VM,
            os_family=ServerProfile.OSFamily.LINUX,
            provider_account=self.provider_account,
            cpu_cores=4,
            ram_mb=8192,
            automatic_updates=True,
            patch_window="Sunday 03:00 Europe/London",
        )
        user = self._user("server-edit-details@example.com")

        result = cast(
            InfrastructureSpecialistEditOut,
            get_infrastructure_specialist_edit_details(self._request(user), resource.id),
        )

        self.assertEqual(result.resource_type, "server")
        self.assertEqual(result.ownership_type, "internal")
        self.assertEqual(result.values["hostname"], "adb-lon-ws01")
        self.assertEqual(result.values["compute_type"], "cloud_vm")
        self.assertEqual(
            result.values["provider_account_resource_id"], self.provider_account.resource_id
        )
        self.assertEqual(result.values["automatic_updates"], True)
        self.assertEqual(result.values["patch_window"], "Sunday 03:00 Europe/London")
        self.assertNotIn("password", result.values)
        self.assertNotIn("token", result.values)
        self.assertNotIn("private_key", result.values)

    def test_network_and_subnet_edit_details_return_relation_ids(self) -> None:
        network_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="ADB Production VPC",
            resource_type=InfrastructureResource.ResourceType.NETWORK,
        )
        network = Network.objects.create(
            resource=network_resource,
            provider_account=self.provider_account,
            network_type=Network.NetworkType.VPC,
            provider_network_id="vpc-lon1-01",
            cidr="10.42.0.0/16",
            gateway="10.42.0.1",
            dns_servers=["1.1.1.1", "1.0.0.1"],
        )
        subnet_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="ADB Web Subnet",
            resource_type=InfrastructureResource.ResourceType.SUBNET,
        )
        Subnet.objects.create(
            resource=subnet_resource,
            network=network,
            cidr="10.42.10.0/24",
            gateway="10.42.10.1",
        )
        user = self._user("network-edit-details@example.com")

        network_result = cast(
            InfrastructureSpecialistEditOut,
            get_infrastructure_specialist_edit_details(
                self._request(user),
                network_resource.id,
            ),
        )
        subnet_result = cast(
            InfrastructureSpecialistEditOut,
            get_infrastructure_specialist_edit_details(
                self._request(user),
                subnet_resource.id,
            ),
        )

        self.assertEqual(
            network_result.values["provider_account_resource_id"],
            self.provider_account.resource_id,
        )
        self.assertEqual(network_result.values["dns_servers"], ["1.1.1.1", "1.0.0.1"])
        self.assertEqual(subnet_result.values["network_resource_id"], network_resource.id)

    def test_edit_details_hide_inaccessible_client_resource(self) -> None:
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_b,
            name="Client B Server",
            resource_type=InfrastructureResource.ResourceType.SERVER,
        )
        ServerProfile.objects.create(resource=resource, hostname="client-b-web01")
        user = self._user("edit-details-scope@example.com")
        self._grant_client(user, self.client_a)

        result = get_infrastructure_specialist_edit_details(self._request(user), resource.id)

        self.assertIsInstance(result, tuple)
        status, payload = cast(tuple[int, dict[str, object]], result)
        self.assertEqual(status, 404)
        self.assertEqual(payload["code"], "not_found")

from django.core.exceptions import ValidationError
from django.test import TestCase

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


class InfrastructureSpecialistModelTests(TestCase):
    def setUp(self) -> None:
        self.client_a = Client.objects.create(
            name="Client A",
            company="Client A Ltd",
            email="client-a@example.com",
        )
        self.client_b = Client.objects.create(
            name="Client B",
            company="Client B Ltd",
            email="client-b@example.com",
        )
        self.provider = ServiceProvider.objects.create(
            name="DigitalOcean",
            slug="digitalocean",
            category=ServiceProvider.Category.CLOUD,
        )
        self.internal_provider_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="ADB DigitalOcean",
            resource_type=InfrastructureResource.ResourceType.PROVIDER_ACCOUNT,
        )
        self.internal_provider_account = ProviderAccount.objects.create(
            resource=self.internal_provider_resource,
            provider=self.provider,
        )
        self.client_b_provider_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_b,
            name="Client B Cloud",
            resource_type=InfrastructureResource.ResourceType.PROVIDER_ACCOUNT,
        )
        self.client_b_provider_account = ProviderAccount.objects.create(
            resource=self.client_b_provider_resource,
            provider=self.provider,
        )

    def _resource(
        self,
        name: str,
        resource_type: str,
        *,
        client: Client | None = None,
    ) -> InfrastructureResource:
        return InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT if client else OwnershipType.INTERNAL,
            client=client,
            name=name,
            resource_type=resource_type,
        )

    def test_server_profile_requires_server_resource(self) -> None:
        resource = self._resource(
            "Not a server",
            InfrastructureResource.ResourceType.WEBSITE,
        )

        server = ServerProfile(resource=resource, hostname="example-host")

        with self.assertRaises(ValidationError):
            server.full_clean()

    def test_client_server_can_use_internal_provider_account(self) -> None:
        resource = self._resource(
            "Client A Server",
            InfrastructureResource.ResourceType.SERVER,
            client=self.client_a,
        )
        server = ServerProfile(
            resource=resource,
            hostname="client-a-web01",
            provider_account=self.internal_provider_account,
        )

        server.full_clean()
        server.save()

        self.assertEqual(server.provider_account, self.internal_provider_account)

    def test_client_server_cannot_use_other_client_provider_account(self) -> None:
        resource = self._resource(
            "Client A Server",
            InfrastructureResource.ResourceType.SERVER,
            client=self.client_a,
        )
        server = ServerProfile(
            resource=resource,
            hostname="client-a-web01",
            provider_account=self.client_b_provider_account,
        )

        with self.assertRaises(ValidationError):
            server.full_clean()

    def test_server_decommission_date_cannot_precede_commission_date(self) -> None:
        resource = self._resource(
            "Server",
            InfrastructureResource.ResourceType.SERVER,
        )
        server = ServerProfile(
            resource=resource,
            hostname="adb-lon-ws01",
            commissioned_at="2026-08-20",
            decommissioned_at="2026-08-19",
        )

        with self.assertRaises(ValidationError):
            server.full_clean()

    def test_network_validates_cidr_and_dns_servers(self) -> None:
        resource = self._resource(
            "ADB Production VPC",
            InfrastructureResource.ResourceType.NETWORK,
        )
        network = Network(
            resource=resource,
            cidr="10.10.0.0/16",
            dns_servers=["1.1.1.1", "2606:4700:4700::1111"],
        )

        network.full_clean()
        network.save()

        network.cidr = "not-a-cidr"
        with self.assertRaises(ValidationError):
            network.full_clean()

    def test_subnet_gateway_must_belong_to_cidr(self) -> None:
        network_resource = self._resource(
            "ADB Production VPC",
            InfrastructureResource.ResourceType.NETWORK,
        )
        network = Network.objects.create(
            resource=network_resource,
            cidr="10.10.0.0/16",
        )
        subnet_resource = self._resource(
            "Web subnet",
            InfrastructureResource.ResourceType.SUBNET,
        )
        subnet = Subnet(
            resource=subnet_resource,
            network=network,
            cidr="10.10.10.0/24",
            gateway="10.10.20.1",
        )

        with self.assertRaises(ValidationError):
            subnet.full_clean()

    def test_interface_subnet_must_belong_to_selected_network(self) -> None:
        server_resource = self._resource(
            "Server",
            InfrastructureResource.ResourceType.SERVER,
        )
        server = ServerProfile.objects.create(
            resource=server_resource,
            hostname="adb-lon-ws01",
        )
        network_a = Network.objects.create(
            resource=self._resource(
                "Network A",
                InfrastructureResource.ResourceType.NETWORK,
            ),
            cidr="10.10.0.0/16",
        )
        network_b = Network.objects.create(
            resource=self._resource(
                "Network B",
                InfrastructureResource.ResourceType.NETWORK,
            ),
            cidr="10.20.0.0/16",
        )
        subnet = Subnet.objects.create(
            resource=self._resource(
                "Network B web",
                InfrastructureResource.ResourceType.SUBNET,
            ),
            network=network_b,
            cidr="10.20.10.0/24",
        )
        interface = NetworkInterface(
            server=server,
            name="eth0",
            network=network_a,
            subnet=subnet,
        )

        with self.assertRaises(ValidationError):
            interface.full_clean()

    def test_ip_address_must_match_interface_resource_and_subnet(self) -> None:
        server_resource = self._resource(
            "Server",
            InfrastructureResource.ResourceType.SERVER,
        )
        server = ServerProfile.objects.create(
            resource=server_resource,
            hostname="adb-lon-ws01",
        )
        network = Network.objects.create(
            resource=self._resource(
                "Network",
                InfrastructureResource.ResourceType.NETWORK,
            ),
            cidr="10.10.0.0/16",
        )
        subnet = Subnet.objects.create(
            resource=self._resource(
                "Subnet",
                InfrastructureResource.ResourceType.SUBNET,
            ),
            network=network,
            cidr="10.10.10.0/24",
        )
        interface = NetworkInterface.objects.create(
            server=server,
            name="eth0",
            network=network,
            subnet=subnet,
        )

        invalid_subnet_address = IPAddress(
            resource=server_resource,
            interface=interface,
            address="10.10.20.10",
        )
        with self.assertRaises(ValidationError):
            invalid_subnet_address.full_clean()

        other_resource = self._resource(
            "Other server",
            InfrastructureResource.ResourceType.SERVER,
        )
        wrong_resource = IPAddress(
            resource=other_resource,
            interface=interface,
            address="10.10.10.10",
        )
        with self.assertRaises(ValidationError):
            wrong_resource.full_clean()

    def test_modern_server_and_network_models_do_not_store_secrets(self) -> None:
        forbidden_fields = {
            "password",
            "api_key",
            "secret_key",
            "private_key",
            "token",
            "credential",
        }

        for model in (ServerProfile, Network, Subnet, NetworkInterface, IPAddress):
            field_names = {field.name for field in model._meta.get_fields()}
            self.assertTrue(field_names.isdisjoint(forbidden_fields))

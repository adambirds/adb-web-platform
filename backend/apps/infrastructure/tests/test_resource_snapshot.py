from django.test import TestCase

from apps.core.ownership import OwnershipType
from apps.infrastructure.legacy_resource_snapshot import legacy_resource_snapshot
from apps.infrastructure.models import (
    InfrastructureResource,
    Licence,
    LicenceResourceIdentity,
    Server,
    ServerResourceIdentity,
)


class LegacyResourceSnapshotTests(TestCase):
    def test_server_snapshot_exposes_operational_fields(self) -> None:
        server = Server.objects.create(
            hostname="adb-lon-ws01",
            role="web",
            public_ip="203.0.113.10",
            provider="do",
            region="lon1",
            os="ubuntu_24",
            ram_gb=8,
            disk_gb=160,
        )
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="ADB London web server",
            resource_type=InfrastructureResource.ResourceType.SERVER,
        )
        ServerResourceIdentity.objects.create(server=server, resource=resource)

        snapshot = legacy_resource_snapshot(resource)

        self.assertIsNotNone(snapshot)
        assert snapshot is not None
        fields = {field.key: field.value for field in snapshot.fields}
        self.assertEqual(snapshot.legacy_type, "server")
        self.assertEqual(snapshot.register_path, "/admin/infrastructure/servers")
        self.assertEqual(fields["hostname"], "adb-lon-ws01")
        self.assertEqual(fields["provider"], "DigitalOcean")
        self.assertEqual(fields["os"], "Ubuntu 24.04")
        self.assertEqual(fields["ram_gb"], "8 GB")

    def test_licence_snapshot_never_exposes_legacy_secret_key(self) -> None:
        licence = Licence.objects.create(
            name="Sensitive plugin",
            licence_type="subscription",
            vendor="Example Vendor",
            renewal_date="2027-01-01",
            renewal_cost="49.99",
            portal_url="https://vendor.example.com",
            licence_key="this-must-never-be-serialised",
            notes="A note could also contain sensitive operational data.",
        )
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Sensitive plugin licence",
            resource_type=InfrastructureResource.ResourceType.LICENCE,
        )
        LicenceResourceIdentity.objects.create(licence=licence, resource=resource)

        snapshot = legacy_resource_snapshot(resource)

        self.assertIsNotNone(snapshot)
        assert snapshot is not None
        keys = {field.key for field in snapshot.fields}
        values = {field.value for field in snapshot.fields}
        self.assertNotIn("licence_key", keys)
        self.assertNotIn("notes", keys)
        self.assertNotIn("this-must-never-be-serialised", values)

    def test_unreconciled_resource_has_no_legacy_snapshot(self) -> None:
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Native structured network",
            resource_type=InfrastructureResource.ResourceType.NETWORK,
        )

        self.assertIsNone(legacy_resource_snapshot(resource))

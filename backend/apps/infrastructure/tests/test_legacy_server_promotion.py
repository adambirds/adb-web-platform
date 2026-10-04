from django.test import TestCase

from apps.core.ownership import OwnershipType
from apps.infrastructure.legacy_reconciliation import reconcile_legacy_resource
from apps.infrastructure.models import InfrastructureResource, IPAddress, Server, ServerProfile


class LegacyServerPromotionTests(TestCase):
    def test_reconciliation_promotes_safe_server_fields(self) -> None:
        legacy = Server.objects.create(
            hostname="adb-lon-ws01",
            role="web",
            public_ip="203.0.113.10",
            private_ip="10.10.10.10",
            provider="do",
            region="lon1",
            os="ubuntu_24",
            cpu="AMD EPYC",
            ram_gb=4,
            disk_gb=80,
            virtualization_type="vm",
            notes="Do not promote potentially sensitive free-text notes.",
        )

        resource = reconcile_legacy_resource(
            legacy_type="server",
            legacy_id=legacy.id,
            ownership_type=OwnershipType.INTERNAL,
            client=None,
            lifecycle_status=InfrastructureResource.LifecycleStatus.ACTIVE,
            environment=InfrastructureResource.Environment.PRODUCTION,
            criticality=InfrastructureResource.Criticality.HIGH,
            name=None,
            linked_by=None,
        )

        profile = ServerProfile.objects.get(resource=resource)
        self.assertEqual(profile.hostname, "adb-lon-ws01")
        self.assertEqual(profile.role, "Web Server")
        self.assertEqual(profile.compute_type, ServerProfile.ComputeType.VIRTUAL_MACHINE)
        self.assertEqual(profile.cpu_model, "AMD EPYC")
        self.assertEqual(profile.ram_mb, 4096)
        self.assertEqual(profile.root_disk_gb, 80)
        self.assertEqual(profile.os_family, ServerProfile.OSFamily.LINUX)
        self.assertEqual(profile.distribution, "Ubuntu")
        self.assertEqual(profile.os_version, "24.04")
        self.assertEqual(profile.region, "lon1")
        self.assertIsNone(profile.provider_account_id)
        self.assertNotIn("sensitive", resource.description.lower())

        addresses = {
            item.address: (item.scope, item.is_primary)
            for item in IPAddress.objects.filter(resource=resource)
        }
        self.assertEqual(
            addresses,
            {
                "203.0.113.10": (IPAddress.Scope.PUBLIC, True),
                "10.10.10.10": (IPAddress.Scope.PRIVATE, False),
            },
        )

    def test_unknown_legacy_os_and_provider_are_not_guessed(self) -> None:
        legacy = Server.objects.create(
            hostname="legacy-appliance",
            provider="other",
            os="other",
            virtualization_type="bare_metal",
        )

        resource = reconcile_legacy_resource(
            legacy_type="server",
            legacy_id=legacy.id,
            ownership_type=OwnershipType.INTERNAL,
            client=None,
            lifecycle_status=InfrastructureResource.LifecycleStatus.ACTIVE,
            environment=InfrastructureResource.Environment.NOT_APPLICABLE,
            criticality=InfrastructureResource.Criticality.NORMAL,
            name=None,
            linked_by=None,
        )

        profile = ServerProfile.objects.get(resource=resource)
        self.assertEqual(profile.os_family, ServerProfile.OSFamily.OTHER)
        self.assertEqual(profile.distribution, "")
        self.assertEqual(profile.os_version, "")
        self.assertEqual(profile.compute_type, ServerProfile.ComputeType.BARE_METAL)
        self.assertIsNone(profile.provider_account_id)

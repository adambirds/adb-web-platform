from typing import cast

from django.contrib.auth.models import Permission
from django.test import RequestFactory, TestCase

from apps.core.ownership import OwnershipType
from apps.infrastructure.models import InfrastructureResource, IPAddress, ServerProfile
from apps.infrastructure.ninja.resource_schemas import InfrastructureResourceDetailOut
from apps.infrastructure.ninja.resource_views import get_infrastructure_resource
from authentication.models import User


class InfrastructureSpecialistSnapshotTests(TestCase):
    def test_resource_detail_projects_native_server_fields_without_secrets(self) -> None:
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="ADB production web server",
            resource_type=InfrastructureResource.ResourceType.SERVER,
            environment=InfrastructureResource.Environment.PRODUCTION,
        )
        ServerProfile.objects.create(
            resource=resource,
            hostname="adb-lon-ws01",
            fqdn="adb-lon-ws01.internal.example",
            role="Web server",
            cpu_model="AMD EPYC",
            cpu_cores=4,
            ram_mb=8192,
            distribution="Ubuntu",
            os_version="24.04",
            ssh_port=22,
        )
        IPAddress.objects.create(
            resource=resource,
            address="203.0.113.10",
            scope=IPAddress.Scope.PUBLIC,
            is_primary=True,
        )
        user = User.objects.create_user(
            email="specialist-projection@example.com",
            password="test-password",
            first_name="Infra",
            last_name="Viewer",
            is_staff=True,
        )
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="infrastructure",
                codename="view_infrastructureresource",
            )
        )
        request = RequestFactory().get(f"/api/admin/infrastructure/resources/{resource.id}")
        request.user = user

        result = get_infrastructure_resource(request, resource.id)

        self.assertIsInstance(result, InfrastructureResourceDetailOut)
        detail = cast(InfrastructureResourceDetailOut, result)
        fields = {field.key: field.value for field in detail.specialist_fields}
        self.assertEqual(fields["hostname"], "adb-lon-ws01")
        self.assertEqual(fields["cpu_model"], "AMD EPYC")
        self.assertEqual(fields["ram_mb"], "8192 MB")
        self.assertEqual(fields["distribution"], "Ubuntu")
        self.assertEqual(fields["direct_ip_addresses"], "203.0.113.10")
        self.assertTrue(
            {
                "password",
                "api_key",
                "secret_key",
                "private_key",
                "token",
                "credential",
            }.isdisjoint(fields)
        )

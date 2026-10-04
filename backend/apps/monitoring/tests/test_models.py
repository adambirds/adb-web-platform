from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.credentials.models import StoredCredential
from apps.infrastructure.models import InfrastructureResource
from apps.monitoring.models import MonitorCheck


class MonitorCheckModelTests(TestCase):
    def test_client_check_rejects_another_clients_credential(self) -> None:
        first = Client.objects.create(name="First", company="First Ltd", email="first@example.test")
        second = Client.objects.create(
            name="Second", company="Second Ltd", email="second@example.test"
        )
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=first,
            name="First client website",
            resource_type=InfrastructureResource.ResourceType.WEBSITE,
        )
        credential = StoredCredential.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=second,
            name="Other client credential",
        )
        check = MonitorCheck(
            resource=resource,
            credential=credential,
            name="Authenticated health",
            check_type=MonitorCheck.CheckType.HTTP,
            target="https://first.example.test/health",
        )
        with self.assertRaises(ValidationError):
            check.full_clean()

    def test_http_check_rejects_non_http_target(self) -> None:
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Internal website",
            resource_type=InfrastructureResource.ResourceType.WEBSITE,
        )
        check = MonitorCheck(
            resource=resource,
            name="Unsafe target",
            check_type=MonitorCheck.CheckType.HTTP,
            target="file:///etc/passwd",
        )

        with self.assertRaises(ValidationError):
            check.full_clean()

    def test_domain_expiry_requires_domain_resource(self) -> None:
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Website",
            resource_type=InfrastructureResource.ResourceType.WEBSITE,
        )
        check = MonitorCheck(
            resource=resource,
            name="Domain expiry",
            check_type=MonitorCheck.CheckType.DOMAIN_EXPIRY,
            target="example.test",
        )

        with self.assertRaises(ValidationError):
            check.full_clean()

    def test_retired_resource_cannot_receive_new_monitoring_check(self) -> None:
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Retired website",
            resource_type=InfrastructureResource.ResourceType.WEBSITE,
            lifecycle_status=InfrastructureResource.LifecycleStatus.RETIRED,
        )
        check = MonitorCheck(
            resource=resource,
            name="Retired health",
            check_type=MonitorCheck.CheckType.HTTP,
            target="https://retired.example.test/health",
        )

        with self.assertRaises(ValidationError):
            check.full_clean()

    def test_tcp_check_requires_port(self) -> None:
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Internal server",
            resource_type=InfrastructureResource.ResourceType.SERVER,
        )
        check = MonitorCheck(
            resource=resource,
            name="SSH",
            check_type=MonitorCheck.CheckType.TCP,
            target="server.example.test",
        )
        with self.assertRaises(ValidationError):
            check.full_clean()

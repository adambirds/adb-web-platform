from datetime import timedelta

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.infrastructure.models import DomainProfile, InfrastructureResource, TLSCertificate
from authentication.models import User


class InfrastructureSummaryTests(TestCase):
    def setUp(self) -> None:
        self.staff = User.objects.create_user(
            email="summary@example.test",
            password="test-password",
            first_name="Summary",
            last_name="Staff",
            is_staff=True,
        )
        self.profile = StaffAccessProfile.objects.create(user=self.staff)
        self.client.force_login(self.staff)

    def grant(self, *codenames: str) -> None:
        self.staff.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label="infrastructure", codename__in=codenames
            )
        )

    def domain(
        self, name: str, client: Client | None = None, lifecycle: str = "active"
    ) -> DomainProfile:
        resource = InfrastructureResource.objects.create(
            name=name,
            resource_type="domain",
            ownership_type=OwnershipType.CLIENT if client else OwnershipType.INTERNAL,
            client=client,
            lifecycle_status=lifecycle,
        )
        return DomainProfile.objects.create(
            resource=resource,
            domain_name=name,
            expires_on=timezone.localdate() + timedelta(days=10),
        )

    def summary(self) -> dict[str, int]:
        response = self.client.get("/api/admin/infrastructure/summary")
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_two_native_domains_are_counted_with_resource_permission(self) -> None:
        self.grant("view_infrastructureresource")
        self.domain("one.example.com")
        self.domain("two.example.com")
        result = self.summary()
        self.assertEqual(result["domain_count"], 2)
        self.assertEqual(result["expiring_domain_count"], 2)

    def test_each_native_resource_family_is_counted(self) -> None:
        self.grant("view_infrastructureresource")
        families = {
            "server": "server_count",
            "database_instance": "database_count",
            "website": "website_count",
            "tls_certificate": "ssl_certificate_count",
            "licence": "licence_count",
            "application": "application_count",
            "mobile_app": "mobile_app_count",
            "api": "api_count",
            "bot": "bot_count",
            "email_system": "email_system_count",
        }
        for resource_type in families:
            InfrastructureResource.objects.create(
                name=resource_type,
                resource_type=resource_type,
                ownership_type=OwnershipType.INTERNAL,
            )
        result = self.summary()
        for key in families.values():
            self.assertEqual(result[key], 1)

    def test_native_domain_counts_require_resource_capability(self) -> None:
        self.grant("view_domainprofile")
        self.domain("one.example.com")
        self.assertEqual(self.summary()["domain_count"], 0)
        self.assertEqual(self.summary()["expiring_domain_count"], 0)

    def test_client_scope_applies_with_specialist_model_permission(self) -> None:
        self.grant("view_infrastructureresource", "view_domainprofile")
        allowed = Client.objects.create(name="Allowed", email="allowed@example.test")
        hidden = Client.objects.create(name="Hidden", email="hidden@example.test")
        ClientAccessGrant.objects.create(profile=self.profile, client=allowed)
        self.domain("allowed.example.com", client=allowed)
        self.domain("hidden.example.com", client=hidden)
        self.assertEqual(self.summary()["domain_count"], 1)
        self.assertEqual(self.summary()["expiring_domain_count"], 1)

    def test_retired_and_archived_domains_are_excluded(self) -> None:
        self.staff.is_superuser = True
        self.staff.save()
        for lifecycle in ("retired", "archived"):
            self.domain(f"{lifecycle}.example.com", lifecycle=lifecycle)
        self.assertEqual(self.summary()["domain_count"], 0)
        self.assertEqual(self.summary()["expiring_domain_count"], 0)

    def test_tls_expiry_uses_native_metadata(self) -> None:
        self.grant("view_infrastructureresource")
        for days in (-1, 10, 100):
            resource = InfrastructureResource.objects.create(
                name=f"TLS {days}",
                resource_type="tls_certificate",
                ownership_type=OwnershipType.INTERNAL,
            )
            TLSCertificate.objects.create(
                resource=resource, expires_at=timezone.now() + timedelta(days=days)
            )
        result = self.summary()
        self.assertEqual(result["ssl_certificate_count"], 3)
        self.assertEqual(result["expiring_certificate_count"], 1)

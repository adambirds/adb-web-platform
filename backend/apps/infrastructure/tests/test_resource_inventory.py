"""Native category registers, technology projections and retired-model boundaries."""

from datetime import timedelta

from django.apps import apps
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test import TestCase
from django.utils import timezone

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.infrastructure.models import (
    ApplicationProfile,
    DomainProfile,
    InfrastructureResource,
    ServerProfile,
    TLSCertificate,
    WebsiteProfile,
)
from authentication.models import User


class ResourceInventoryTests(TestCase):
    def setUp(self) -> None:
        self.staff = User.objects.create_user(
            email="inventory@example.test",
            password="test-password",
            first_name="Inventory",
            last_name="Staff",
            is_staff=True,
        )
        self.profile = StaffAccessProfile.objects.create(user=self.staff)
        self.client.force_login(self.staff)

    def grant(self) -> None:
        self.staff.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="infrastructure", codename="view_infrastructureresource"
            )
        )

    def resource(
        self, name: str, resource_type: str, client: Client | None = None
    ) -> InfrastructureResource:
        return InfrastructureResource.objects.create(
            name=name,
            resource_type=resource_type,
            client=client,
            ownership_type=OwnershipType.CLIENT if client else OwnershipType.INTERNAL,
        )

    def test_every_category_reads_its_native_records(self) -> None:
        self.grant()
        types = (
            "server",
            "database_instance",
            "website",
            "domain",
            "tls_certificate",
            "licence",
            "application",
            "mobile_app",
            "api",
            "bot",
            "email_system",
        )
        for resource_type in types:
            self.resource(resource_type, resource_type)
        for resource_type in types:
            with self.subTest(resource_type=resource_type):
                response = self.client.get(
                    "/api/admin/infrastructure/resources", {"resource_type": resource_type}
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["total"], 1)
                self.assertEqual(response.json()["items"][0]["resource_type"], resource_type)

    def test_domain_and_tls_lists_include_expiry_and_auto_renew(self) -> None:
        self.grant()
        expiry = timezone.localdate() + timedelta(days=20)
        domain = self.resource("example.test", "domain")
        DomainProfile.objects.create(
            resource=domain, domain_name="example.test", expires_on=expiry, auto_renew=True
        )
        tls = self.resource("Example TLS", "tls_certificate")
        certificate = TLSCertificate.objects.create(
            resource=tls, expires_at=timezone.now() + timedelta(days=20), auto_renew=False
        )
        rows = self.client.get("/api/admin/infrastructure/resources").json()["items"]
        by_id = {row["id"]: row for row in rows}
        self.assertEqual(by_id[domain.id]["expires_on"], expiry.isoformat())
        self.assertTrue(by_id[domain.id]["auto_renew"])
        self.assertIsNotNone(by_id[tls.id]["expires_at"])
        self.assertFalse(by_id[certificate.resource_id]["auto_renew"])
        detail = self.client.get(f"/api/admin/infrastructure/resources/{domain.id}").json()
        self.assertNotIn("legacy_reference", detail)
        self.assertTrue(detail["specialist_fields"])

    def test_technology_requires_staff_and_resource_capability(self) -> None:
        url = "/api/admin/infrastructure/technology"
        self.assertEqual(self.client.get(url).status_code, 403)
        self.grant()
        self.assertEqual(self.client.get(url).status_code, 200)
        self.staff.is_staff = False
        self.staff.save()
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 401)

    def test_technology_scope_lifecycle_search_and_pagination(self) -> None:
        self.grant()
        visible = Client.objects.create(
            name="Visible", company="Visible Ltd", email="visible@example.test"
        )
        hidden = Client.objects.create(name="Hidden", email="hidden@example.test")
        ClientAccessGrant.objects.create(profile=self.profile, client=visible)
        site = self.resource("A Website", "website", visible)
        WebsiteProfile.objects.create(resource=site, cms="WordPress", cms_version="6.8")
        server = self.resource("B Compute", "server")
        ServerProfile.objects.create(
            resource=server,
            hostname="server.example.test",
            distribution="Ubuntu",
            os_version="24.04",
        )
        application = self.resource("C App", "application", hidden)
        ApplicationProfile.objects.create(resource=application, framework="Django")
        archived = self.resource("D Archived", "website")
        archived.lifecycle_status = "archived"
        archived.save()
        WebsiteProfile.objects.create(resource=archived, cms="Hidden CMS")
        url = "/api/admin/infrastructure/technology"
        first = self.client.get(url, {"page_size": 1}).json()
        self.assertEqual(first["total"], 2)
        self.assertEqual(first["total_pages"], 2)
        self.assertEqual(first["items"][0]["technology"], "WordPress")
        self.assertEqual(first["items"][0]["version"], "6.8")
        second = self.client.get(url, {"page_size": 1, "page": 2}).json()
        self.assertEqual(second["items"][0]["resource_id"], server.id)
        search = self.client.get(url, {"search": "Visible Ltd"}).json()
        self.assertEqual(search["total"], 1)
        self.assertEqual(search["items"][0]["resource_id"], site.id)
        self.assertEqual(self.client.get(url, {"search": "Hidden"}).json()["total"], 0)

    def test_obsolete_models_tables_and_capabilities_are_removed(self) -> None:
        names = {model.__name__ for model in apps.get_app_config("infrastructure").get_models()}
        obsolete = {
            "Server",
            "Database",
            "Website",
            "Domain",
            "SSLCertificate",
            "Licence",
            "Application",
            "MobileApp",
            "API",
            "Bot",
            "EmailSystem",
            "WebsiteTechStack",
        }
        self.assertFalse(names & obsolete)
        self.assertFalse(any(name.endswith("ResourceIdentity") for name in names))
        tables = set(connection.introspection.table_names())
        for name in obsolete:
            self.assertNotIn(f"infrastructure_{name.lower()}", tables)
        self.assertFalse(
            ContentType.objects.filter(app_label="infrastructure", model="domain").exists()
        )
        self.assertFalse(
            Permission.objects.filter(
                content_type__app_label="infrastructure", codename="reconcile_legacy_infrastructure"
            ).exists()
        )

    def test_obsolete_read_and_reconciliation_apis_are_unavailable(self) -> None:
        self.staff.is_superuser = True
        self.staff.save()
        for path in (
            "reconciliation",
            "domains",
            "websites",
            "servers",
            "databases",
            "licences",
            "ssl-certificates",
            "tech-stack",
            "applications",
            "mobile-apps",
            "apis",
            "bots",
            "email-systems",
        ):
            with self.subTest(path=path):
                self.assertIn(
                    self.client.get(f"/api/admin/infrastructure/{path}").status_code, (404, 405)
                )

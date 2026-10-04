from __future__ import annotations

import json
from typing import TYPE_CHECKING

from django.contrib.auth.models import Permission
from django.test import TestCase

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client
from apps.core.models import AuditEvent
from apps.core.ownership import OwnershipType
from apps.infrastructure.models import (
    InfrastructureResource,
    InfrastructureTag,
    ProviderAccount,
    ServiceProvider,
)
from authentication.models import User

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse


class ResourceCreationTests(TestCase):
    def setUp(self) -> None:
        self.staff = User.objects.create_user(
            email="create@example.test",
            password="test-password",
            first_name="Create",
            last_name="Staff",
            is_staff=True,
        )
        self.profile = StaffAccessProfile.objects.create(user=self.staff)
        self.client.force_login(self.staff)
        self.provider = ServiceProvider.objects.create(
            name="Example Cloud", slug="example-cloud", category="cloud"
        )
        self.allowed = Client.objects.create(name="Allowed", email="allowed@example.test")
        self.hidden = Client.objects.create(name="Hidden", email="hidden@example.test")
        ClientAccessGrant.objects.create(profile=self.profile, client=self.allowed)

    def grant(self, *names: str) -> None:
        self.staff.user_permissions.add(
            *Permission.objects.filter(content_type__app_label="infrastructure", codename__in=names)
        )

    def account_permissions(self) -> None:
        self.grant(
            "view_infrastructureresource",
            "view_serviceprovider",
            "add_infrastructureresource",
            "add_provideraccount",
        )

    def post(self, path: str, body: dict[str, object]) -> _MonkeyPatchedWSGIResponse:
        return self.client.post(
            f"/api/admin/infrastructure/{path}",
            data=json.dumps(body),
            content_type="application/json",
        )

    def account_payload(self, **changes: object) -> dict[str, object]:
        return {
            "name": "Cloud account",
            "provider_id": self.provider.id,
            "account_identifier": "team-account",
            "tenant_id": "tenant",
            "portal_url": "https://console.example.test/",
            **changes,
        }

    def test_provider_account_create_links_vendor_and_projects_metadata(self) -> None:
        self.account_permissions()
        response = self.post("provider-accounts", self.account_payload())
        self.assertEqual(response.status_code, 201)
        resource_id = response.json()["resource_id"]
        account = ProviderAccount.objects.get(resource_id=resource_id)
        self.assertEqual(account.provider, self.provider)
        self.assertEqual(account.resource.resource_type, "provider_account")
        self.assertEqual(account.resource.created_by, self.staff)
        detail = self.client.get(f"/api/admin/infrastructure/resources/{resource_id}")
        self.assertEqual(detail.status_code, 200)
        fields = {field["key"]: field["value"] for field in detail.json()["specialist_fields"]}
        self.assertEqual(fields["provider"], "Example Cloud")
        self.assertEqual(fields["tenant_id"], "tenant")
        self.assertTrue(
            AuditEvent.objects.filter(action="created", resource_id=resource_id).exists()
        )

    def test_provider_account_requires_both_resource_and_specialist_capabilities(self) -> None:
        self.grant(
            "view_infrastructureresource", "view_serviceprovider", "add_infrastructureresource"
        )
        self.assertEqual(self.post("provider-accounts", self.account_payload()).status_code, 403)
        self.assertFalse(ProviderAccount.objects.exists())
        self.grant("add_provideraccount")
        self.assertEqual(self.post("provider-accounts", self.account_payload()).status_code, 201)

    def test_provider_account_creation_validates_client_scope(self) -> None:
        self.account_permissions()
        for client_id, expected in ((self.hidden.id, 404), (self.allowed.id, 201)):
            with self.subTest(client_id=client_id):
                response = self.post(
                    "provider-accounts",
                    self.account_payload(ownership_type="client", client_id=client_id),
                )
                self.assertEqual(response.status_code, expected)
        self.assertEqual(ProviderAccount.objects.get().resource.client_id, self.allowed.id)

    def test_invalid_provider_or_account_rolls_back_the_shared_resource(self) -> None:
        self.account_permissions()
        for fields, status in (
            ({"provider_id": 999999}, 404),
            ({"portal_url": "invalid-url"}, 400),
            ({"name": "   "}, 400),
            ({"client_id": self.allowed.id}, 400),
        ):
            with self.subTest(fields=fields):
                response = self.post("provider-accounts", self.account_payload(**fields))
                self.assertEqual(response.status_code, status)
                self.assertEqual(InfrastructureResource.objects.count(), 0)
        self.provider.is_active = False
        self.provider.save()
        self.assertEqual(self.post("provider-accounts", self.account_payload()).status_code, 404)

    def test_provider_account_read_edit_and_archive_obey_scope_and_capabilities(self) -> None:
        self.account_permissions()
        resource_id = self.post("provider-accounts", self.account_payload()).json()["resource_id"]
        url = f"/api/admin/infrastructure/provider-accounts/{resource_id}"
        self.assertEqual(self.client.get(url).status_code, 403)
        self.grant(
            "view_provideraccount", "change_provideraccount", "change_infrastructureresource"
        )
        self.assertEqual(self.client.get(url).status_code, 200)
        payload = {
            "name": "Updated",
            "provider_id": self.provider.id,
            "lifecycle_status": "active",
            "environment": "production",
            "criticality": "normal",
            "tenant_id": "new-tenant",
        }
        response = self.client.patch(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        account = ProviderAccount.objects.get(resource_id=resource_id)
        self.assertEqual(account.tenant_id, "new-tenant")
        self.assertEqual(account.resource.name, "Updated")
        response = self.client.patch(
            url,
            data=json.dumps({**payload, "name": "Should roll back", "portal_url": "invalid"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(InfrastructureResource.objects.get(id=resource_id).name, "Updated")
        self.assertEqual(self.post(f"provider-accounts/{resource_id}/archive", {}).status_code, 200)
        self.assertEqual(
            InfrastructureResource.objects.get(id=resource_id).lifecycle_status, "archived"
        )
        hidden = InfrastructureResource.objects.create(
            name="Hidden account",
            resource_type="provider_account",
            ownership_type=OwnershipType.CLIENT,
            client=self.hidden,
        )
        ProviderAccount.objects.create(resource=hidden, provider=self.provider)
        hidden_url = f"/api/admin/infrastructure/provider-accounts/{hidden.id}"
        self.assertEqual(self.client.get(hidden_url).status_code, 404)
        self.assertEqual(
            self.client.patch(
                hidden_url, data=json.dumps(payload), content_type="application/json"
            ).status_code,
            404,
        )
        self.assertEqual(self.post(f"provider-accounts/{hidden.id}/archive", {}).status_code, 404)

    def test_every_basic_resource_type_can_be_created_and_edited(self) -> None:
        self.grant(
            "view_infrastructureresource",
            "add_infrastructureresource",
            "change_infrastructureresource",
        )
        for resource_type in (
            "api",
            "bot",
            "mobile_app",
            "licence",
            "email_system",
            "network_device",
            "other",
        ):
            with self.subTest(resource_type=resource_type):
                response = self.post(
                    "resources", {"name": resource_type, "resource_type": resource_type}
                )
                self.assertEqual(response.status_code, 201)
                resource_id = response.json()["resource_id"]
                response = self.client.patch(
                    f"/api/admin/infrastructure/resources/{resource_id}",
                    data=json.dumps(
                        {
                            "name": f"Updated {resource_type}",
                            "lifecycle_status": "archived",
                            "environment": "production",
                            "criticality": "high",
                        }
                    ),
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 200)
                resource = InfrastructureResource.objects.get(id=resource_id)
                self.assertIsNotNone(resource.archived_at)
                self.assertEqual(resource.resource_type, resource_type)

    def test_basic_routes_cannot_bypass_specialist_permissions_or_client_scope(self) -> None:
        self.assertEqual(
            self.post("resources", {"name": "API", "resource_type": "api"}).status_code, 403
        )
        self.grant(
            "view_infrastructureresource",
            "add_infrastructureresource",
            "change_infrastructureresource",
        )
        self.assertEqual(
            self.post("resources", {"name": "Server", "resource_type": "server"}).status_code, 422
        )
        self.assertEqual(
            self.post(
                "resources",
                {
                    "name": "API",
                    "resource_type": "api",
                    "ownership_type": "client",
                    "client_id": self.hidden.id,
                },
            ).status_code,
            404,
        )
        resource = InfrastructureResource.objects.create(
            name="Server", resource_type="server", ownership_type=OwnershipType.INTERNAL
        )
        payload = {
            "name": "Bypass",
            "lifecycle_status": "active",
            "environment": "shared",
            "criticality": "normal",
        }
        self.assertEqual(
            self.client.patch(
                f"/api/admin/infrastructure/resources/{resource.id}",
                data=json.dumps(payload),
                content_type="application/json",
            ).status_code,
            404,
        )
        resource.resource_type = "api"
        resource.ownership_type = OwnershipType.CLIENT
        resource.client = self.hidden
        resource.save()
        self.assertEqual(
            self.client.patch(
                f"/api/admin/infrastructure/resources/{resource.id}",
                data=json.dumps(payload),
                content_type="application/json",
            ).status_code,
            404,
        )

    def test_service_provider_create_and_list_require_separate_permissions(self) -> None:
        self.assertEqual(
            self.post(
                "service-providers",
                {"name": "New provider", "slug": "new-provider", "category": "hosting"},
            ).status_code,
            403,
        )
        self.grant("add_serviceprovider")
        response = self.post(
            "service-providers",
            {"name": "New provider", "slug": "new-provider", "category": "hosting"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            self.client.get("/api/admin/infrastructure/service-providers").status_code, 403
        )
        self.grant("view_serviceprovider")
        result = self.client.get(
            "/api/admin/infrastructure/service-providers", {"search": "New", "page_size": "1"}
        ).json()
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["items"][0]["id"], response.json()["id"])
        self.assertEqual(
            self.post(
                "service-providers",
                {"name": "New provider", "slug": "new-provider", "category": "hosting"},
            ).status_code,
            400,
        )

    def test_catalogue_options_scope_clients_and_catalogue_capability(self) -> None:
        self.assertEqual(
            self.client.get("/api/admin/infrastructure/catalogue-options").status_code, 403
        )
        self.grant("view_infrastructureresource")
        options = self.client.get("/api/admin/infrastructure/catalogue-options").json()
        self.assertEqual([item["id"] for item in options["clients"]], [self.allowed.id])
        self.assertEqual(options["providers"], [])
        self.grant("view_serviceprovider")
        options = self.client.get("/api/admin/infrastructure/catalogue-options").json()
        self.assertEqual(options["providers"][0]["id"], self.provider.id)

    def test_nonstaff_and_anonymous_creators_are_rejected(self) -> None:
        self.account_permissions()
        self.staff.is_staff = False
        self.staff.save()
        self.assertEqual(self.post("provider-accounts", self.account_payload()).status_code, 403)
        self.client.logout()
        self.assertEqual(self.post("provider-accounts", self.account_payload()).status_code, 401)

    def test_tag_creation_assignment_removal_and_hidden_resource_boundary(self) -> None:
        self.assertEqual(
            self.post("tags", {"name": "Production", "slug": "production"}).status_code, 403
        )
        self.grant(
            "add_infrastructuretag",
            "view_infrastructuretag",
            "view_infrastructureresource",
            "change_infrastructureresource",
        )
        tag_response = self.post("tags", {"name": "Production", "slug": "production"})
        self.assertEqual(tag_response.status_code, 201)
        tag_id = tag_response.json()["id"]
        self.assertEqual(
            self.client.get("/api/admin/infrastructure/tags", {"search": "Prod"}).json()["total"], 1
        )
        resource = InfrastructureResource.objects.create(
            name="Visible", resource_type="api", ownership_type=OwnershipType.INTERNAL
        )
        url = f"/api/admin/infrastructure/resources/{resource.id}/tags/{tag_id}"
        self.assertEqual(self.client.put(url).status_code, 200)
        self.assertTrue(resource.tags.filter(id=tag_id).exists())
        self.assertEqual(self.client.delete(url).status_code, 200)
        self.assertFalse(resource.tags.exists())
        resource.ownership_type = OwnershipType.CLIENT
        resource.client = self.hidden
        resource.save()
        self.assertEqual(self.client.put(url).status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.assertEqual(InfrastructureTag.objects.count(), 1)

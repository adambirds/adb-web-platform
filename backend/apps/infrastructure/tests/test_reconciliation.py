from __future__ import annotations

from typing import cast

from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.test import RequestFactory, TestCase

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.infrastructure.legacy_reconciliation import LEGACY_RESOURCE_DEFINITIONS
from apps.infrastructure.models import (
    InfrastructureResource,
    Server,
    ServerResourceIdentity,
    Website,
    WebsiteResourceIdentity,
)
from apps.infrastructure.ninja.reconciliation_schemas import (
    LegacyReconciliationOptionsOut,
    LegacyReconciliationPageOut,
    ReconciledResourceOut,
    ReconcileLegacyResourceIn,
)
from apps.infrastructure.ninja.reconciliation_views import (
    legacy_reconciliation_options,
    list_legacy_reconciliation,
    reconcile_legacy_record,
)
from apps.infrastructure.ninja.resource_schemas import InfrastructureResourceDetailOut
from apps.infrastructure.ninja.resource_views import get_infrastructure_resource
from authentication.models import User


class LegacyInfrastructureReconciliationTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.client_a = Client.objects.create(
            name="Client A",
            company="Client A Ltd",
            email="a@example.com",
        )
        self.client_b = Client.objects.create(
            name="Client B",
            company="Client B Ltd",
            email="b@example.com",
        )
        self.server = Server.objects.create(
            hostname="adb-lon-ws01",
            provider="do",
            os="ubuntu_24",
        )
        self.website = Website.objects.create(
            name="Client A website",
            primary_url="https://example.com",
            environment_type="production",
        )
        self.superuser = User.objects.create_superuser(
            email="infra-reconcile@example.com",
            password="test-password",
            first_name="Infra",
            last_name="Admin",
        )

    def _request(self, user: User) -> HttpRequest:
        request = self.factory.get("/api/admin/infrastructure/reconciliation")
        request.user = user
        return request

    def _staff_user(self, email: str) -> User:
        user = User.objects.create_user(
            email=email,
            password="test-password",
            first_name="Infra",
            last_name="Operator",
            is_staff=True,
        )
        permission = Permission.objects.get(
            content_type__app_label="infrastructure",
            codename="reconcile_legacy_infrastructure",
        )
        user.user_permissions.add(permission)
        return user

    def test_registry_covers_every_current_legacy_resource_family(self) -> None:
        self.assertSetEqual(
            {definition.key for definition in LEGACY_RESOURCE_DEFINITIONS},
            {
                "server",
                "database",
                "website",
                "domain",
                "ssl_certificate",
                "licence",
                "application",
                "mobile_app",
                "api",
                "bot",
                "email_system",
            },
        )

    def test_identity_rejects_wrong_structured_resource_type(self) -> None:
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Wrong type",
            resource_type=InfrastructureResource.ResourceType.WEBSITE,
        )
        identity = ServerResourceIdentity(
            server=self.server,
            resource=resource,
            linked_by=self.superuser,
        )

        with self.assertRaises(ValidationError):
            identity.full_clean()

    def test_reconciliation_defaults_to_unlinked_legacy_records(self) -> None:
        result = cast(
            LegacyReconciliationPageOut,
            list_legacy_reconciliation(self._request(self.superuser)),
        )

        rows = {(item.legacy_type, item.legacy_id) for item in result.items}
        self.assertIn(("server", self.server.id), rows)
        self.assertIn(("website", self.website.id), rows)
        self.assertEqual(result.linked, 0)
        self.assertEqual(result.unlinked, result.total_legacy)

    def test_internal_server_reconciliation_creates_typed_identity(self) -> None:
        payload = ReconcileLegacyResourceIn(ownership_type="internal")

        result = cast(
            ReconciledResourceOut,
            reconcile_legacy_record(
                self._request(self.superuser),
                "server",
                self.server.id,
                payload,
            ),
        )

        resource = InfrastructureResource.objects.get(id=result.resource_id)
        self.assertEqual(resource.name, self.server.hostname)
        self.assertEqual(resource.resource_type, InfrastructureResource.ResourceType.SERVER)
        self.assertEqual(resource.ownership_type, OwnershipType.INTERNAL)
        self.assertIsNone(resource.client_id)
        identity = ServerResourceIdentity.objects.get(server=self.server)
        self.assertEqual(identity.resource_id, resource.id)
        self.assertEqual(identity.linked_by_id, self.superuser.id)

        detail = cast(
            InfrastructureResourceDetailOut,
            get_infrastructure_resource(self._request(self.superuser), resource.id),
        )
        self.assertIsNotNone(detail.legacy_reference)
        assert detail.legacy_reference is not None
        self.assertEqual(detail.legacy_reference.legacy_type, "server")
        self.assertEqual(detail.legacy_reference.legacy_id, self.server.id)
        self.assertEqual(detail.legacy_reference.name, self.server.hostname)

    def test_client_reconciliation_respects_client_scope(self) -> None:
        user = self._staff_user("scoped-infra@example.com")
        profile = StaffAccessProfile.objects.create(user=user)
        ClientAccessGrant.objects.create(profile=profile, client=self.client_a)

        success = cast(
            ReconciledResourceOut,
            reconcile_legacy_record(
                self._request(user),
                "website",
                self.website.id,
                ReconcileLegacyResourceIn(
                    ownership_type="client",
                    client_id=self.client_a.id,
                    environment="production",
                ),
            ),
        )

        resource = InfrastructureResource.objects.get(id=success.resource_id)
        self.assertEqual(resource.client_id, self.client_a.id)
        self.assertEqual(resource.environment, InfrastructureResource.Environment.PRODUCTION)
        self.assertTrue(
            WebsiteResourceIdentity.objects.filter(
                website=self.website,
                resource=resource,
            ).exists()
        )

    def test_reconciliation_does_not_allow_inaccessible_client(self) -> None:
        user = self._staff_user("restricted-infra@example.com")
        profile = StaffAccessProfile.objects.create(user=user)
        ClientAccessGrant.objects.create(profile=profile, client=self.client_a)

        result = reconcile_legacy_record(
            self._request(user),
            "website",
            self.website.id,
            ReconcileLegacyResourceIn(
                ownership_type="client",
                client_id=self.client_b.id,
            ),
        )

        self.assertIsInstance(result, tuple)
        status, payload = cast(tuple[int, dict[str, object]], result)
        self.assertEqual(status, 404)
        self.assertEqual(payload["code"], "not_found")
        self.assertFalse(WebsiteResourceIdentity.objects.filter(website=self.website).exists())

    def test_reconciling_same_legacy_record_twice_is_conflict(self) -> None:
        payload = ReconcileLegacyResourceIn(ownership_type="internal")
        reconcile_legacy_record(
            self._request(self.superuser),
            "server",
            self.server.id,
            payload,
        )

        result = reconcile_legacy_record(
            self._request(self.superuser),
            "server",
            self.server.id,
            payload,
        )

        self.assertIsInstance(result, tuple)
        status, response_payload = cast(tuple[int, dict[str, object]], result)
        self.assertEqual(status, 409)
        self.assertEqual(response_payload["code"], "already_reconciled")
        self.assertEqual(ServerResourceIdentity.objects.filter(server=self.server).count(), 1)
        self.assertEqual(
            InfrastructureResource.objects.filter(
                resource_type=InfrastructureResource.ResourceType.SERVER
            ).count(),
            1,
        )

    def test_internal_ownership_rejects_client_id(self) -> None:
        result = reconcile_legacy_record(
            self._request(self.superuser),
            "server",
            self.server.id,
            ReconcileLegacyResourceIn(
                ownership_type="internal",
                client_id=self.client_a.id,
            ),
        )

        self.assertIsInstance(result, tuple)
        status, payload = cast(tuple[int, dict[str, object]], result)
        self.assertEqual(status, 422)
        self.assertEqual(payload["code"], "invalid_ownership")

    def test_reconciliation_options_only_include_accessible_clients(self) -> None:
        user = self._staff_user("options-infra@example.com")
        profile = StaffAccessProfile.objects.create(user=user)
        ClientAccessGrant.objects.create(profile=profile, client=self.client_a)

        result = cast(
            LegacyReconciliationOptionsOut,
            legacy_reconciliation_options(self._request(user)),
        )

        self.assertEqual([client.id for client in result.clients], [self.client_a.id])
        self.assertIn("server", result.legacy_types)
        self.assertIn("production", result.environments)

    def test_staff_without_reconciliation_permission_is_forbidden(self) -> None:
        user = User.objects.create_user(
            email="no-reconcile@example.com",
            password="test-password",
            first_name="No",
            last_name="Permission",
            is_staff=True,
        )

        result = list_legacy_reconciliation(self._request(user))

        self.assertIsInstance(result, tuple)
        status, payload = cast(tuple[int, dict[str, object]], result)
        self.assertEqual(status, 403)
        self.assertEqual(payload["code"], "forbidden")

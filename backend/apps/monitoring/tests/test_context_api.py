from django.contrib.auth.models import Permission
from django.test import TestCase

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.infrastructure.models import InfrastructureResource
from apps.monitoring.models import MonitorCheck
from authentication.models import User


class MonitoringContextAPITests(TestCase):
    def setUp(self) -> None:
        self.staff = User.objects.create_user(
            email="monitoring-context@example.test",
            password="test-password",
            first_name="Monitoring",
            last_name="Context",
            is_staff=True,
        )
        profile = StaffAccessProfile.objects.create(user=self.staff)
        self.visible_client = Client.objects.create(
            name="Visible Contact",
            company="Visible Client",
            email="visible-monitoring@example.test",
        )
        self.hidden_client = Client.objects.create(
            name="Hidden Contact",
            company="Hidden Client",
            email="hidden-context@example.test",
        )
        ClientAccessGrant.objects.create(
            profile=profile,
            client=self.visible_client,
            granted_by=self.staff,
        )

        self.internal_resource = self._resource(
            name="Internal API",
            ownership_type=OwnershipType.INTERNAL,
        )
        self.visible_resource = self._resource(
            name="Visible Client API",
            ownership_type=OwnershipType.CLIENT,
            client=self.visible_client,
        )
        self.hidden_resource = self._resource(
            name="Hidden Client API",
            ownership_type=OwnershipType.CLIENT,
            client=self.hidden_client,
        )
        self.internal_check = self._check(self.internal_resource, "Internal health")
        self.visible_check = self._check(self.visible_resource, "Visible health")
        self.hidden_check = self._check(self.hidden_resource, "Hidden health")
        self.client.force_login(self.staff)

    def _resource(
        self,
        *,
        name: str,
        ownership_type: str,
        client: Client | None = None,
    ) -> InfrastructureResource:
        return InfrastructureResource.objects.create(
            ownership_type=ownership_type,
            client=client,
            name=name,
            resource_type=InfrastructureResource.ResourceType.API,
            environment=InfrastructureResource.Environment.PRODUCTION,
        )

    def _check(self, resource: InfrastructureResource, name: str) -> MonitorCheck:
        return MonitorCheck.objects.create(
            resource=resource,
            name=name,
            check_type=MonitorCheck.CheckType.HTTP,
            target=f"https://{resource.id}.example.test/health",
        )

    def grant_view_permissions(self) -> None:
        permissions = Permission.objects.filter(
            content_type__app_label="monitoring",
            codename__in=["view_monitorcheck", "view_monitorincident"],
        )
        self.staff.user_permissions.add(*permissions)

    def test_overview_context_filters_apply_after_access_scope(self) -> None:
        self.grant_view_permissions()

        global_response = self.client.get("/api/admin/monitoring/overview")
        client_response = self.client.get(
            f"/api/admin/monitoring/overview?client_id={self.visible_client.id}"
        )
        hidden_client_response = self.client.get(
            f"/api/admin/monitoring/overview?client_id={self.hidden_client.id}"
        )
        resource_response = self.client.get(
            f"/api/admin/monitoring/overview?resource_id={self.internal_resource.id}"
        )

        self.assertEqual(global_response.status_code, 200)
        self.assertEqual(
            {check["id"] for check in global_response.json()["checks"]},
            {self.internal_check.id, self.visible_check.id},
        )
        self.assertEqual(client_response.status_code, 200)
        self.assertEqual(client_response.json()["total_checks"], 1)
        self.assertEqual(client_response.json()["checks"][0]["id"], self.visible_check.id)
        self.assertEqual(hidden_client_response.status_code, 200)
        self.assertEqual(hidden_client_response.json()["total_checks"], 0)
        self.assertEqual(hidden_client_response.json()["checks"], [])
        self.assertEqual(resource_response.status_code, 200)
        self.assertEqual(resource_response.json()["total_checks"], 1)
        self.assertEqual(resource_response.json()["checks"][0]["id"], self.internal_check.id)
        self.assertNotIn(
            self.hidden_check.id,
            {check["id"] for check in global_response.json()["checks"]},
        )

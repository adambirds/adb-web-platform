import json

from django.contrib.auth.models import Permission
from django.test import TestCase

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.credentials.models import CredentialType, StoredCredential
from apps.infrastructure.models import InfrastructureResource
from apps.monitoring.models import MonitorCheck
from authentication.models import User


class MonitoringManagementAPITests(TestCase):
    def setUp(self) -> None:
        self.staff = User.objects.create_user(
            email="monitoring-management@example.test",
            password="test-password",
            first_name="Monitoring",
            last_name="Management",
            is_staff=True,
        )
        profile = StaffAccessProfile.objects.create(user=self.staff)
        self.visible_client = Client.objects.create(
            name="Visible Contact",
            company="Visible Client",
            email="visible-management@example.test",
        )
        self.hidden_client = Client.objects.create(
            name="Hidden Contact",
            company="Hidden Client",
            email="hidden-management@example.test",
        )
        ClientAccessGrant.objects.create(
            profile=profile,
            client=self.visible_client,
            granted_by=self.staff,
        )
        self.internal_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Internal API",
            resource_type=InfrastructureResource.ResourceType.API,
            environment=InfrastructureResource.Environment.PRODUCTION,
        )
        self.visible_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.visible_client,
            name="Visible Client API",
            resource_type=InfrastructureResource.ResourceType.API,
            environment=InfrastructureResource.Environment.PRODUCTION,
        )
        self.hidden_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.hidden_client,
            name="Hidden Client API",
            resource_type=InfrastructureResource.ResourceType.API,
            environment=InfrastructureResource.Environment.PRODUCTION,
        )
        self.retired_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Retired API",
            resource_type=InfrastructureResource.ResourceType.API,
            lifecycle_status=InfrastructureResource.LifecycleStatus.RETIRED,
            environment=InfrastructureResource.Environment.PRODUCTION,
        )
        self.client.force_login(self.staff)

    def grant(self, *codenames: str) -> None:
        permissions = Permission.objects.filter(
            content_type__app_label="monitoring",
            codename__in=codenames,
        )
        self.staff.user_permissions.add(*permissions)

    def test_options_return_only_current_resources_in_access_scope(self) -> None:
        self.grant("add_monitorcheck")

        response = self.client.get("/api/admin/monitoring/options")

        self.assertEqual(response.status_code, 200)
        resource_ids = {resource["id"] for resource in response.json()["resources"]}
        self.assertEqual(
            resource_ids,
            {self.internal_resource.id, self.visible_resource.id},
        )
        self.assertNotIn(self.hidden_resource.id, resource_ids)
        self.assertNotIn(self.retired_resource.id, resource_ids)

    def test_configuration_read_requires_change_but_not_history_permissions(self) -> None:
        self.grant("change_monitorcheck")
        check = MonitorCheck.objects.create(
            resource=self.internal_resource,
            name="Editable endpoint",
            check_type=MonitorCheck.CheckType.HTTP,
            target="https://example.test/health",
        )

        response = self.client.get(f"/api/admin/monitoring/checks/{check.id}/configuration")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], check.id)
        self.assertEqual(response.json()["resource_id"], self.internal_resource.id)
        self.assertEqual(response.json()["name"], check.name)

    def test_update_without_credential_visibility_preserves_existing_reference(self) -> None:
        self.grant("change_monitorcheck")
        credential_type = CredentialType.objects.create(name="Monitoring Login")
        credential = StoredCredential.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Monitoring Credential",
            credential_type=credential_type,
            username="monitoring-user",
        )
        check = MonitorCheck.objects.create(
            resource=self.internal_resource,
            credential=credential,
            name="Authenticated endpoint",
            check_type=MonitorCheck.CheckType.HTTP,
            target="https://example.test/health",
        )

        response = self.client.put(
            f"/api/admin/monitoring/checks/{check.id}",
            data=json.dumps(
                {
                    "name": "Renamed endpoint",
                    "check_type": check.check_type,
                    "severity": check.severity,
                    "target": check.target,
                    "port": None,
                    "expected_value": "",
                    "forbidden_value": "",
                    "interval_seconds": 600,
                    "timeout_seconds": 10,
                    "failure_threshold": 3,
                    "recovery_threshold": 2,
                    "expiry_warning_days": 30,
                    "credential_id": None,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        check.refresh_from_db()
        self.assertEqual(check.name, "Renamed endpoint")
        self.assertEqual(check.interval_seconds, 600)
        self.assertEqual(check.credential_id, credential.id)

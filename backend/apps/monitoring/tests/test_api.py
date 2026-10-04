import json
from datetime import timedelta

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone

from apps.access_control.models import StaffAccessProfile
from apps.clients.models import Client
from apps.core.ownership import OwnershipType
from apps.credentials.models import CredentialType, StoredCredential
from apps.infrastructure.models import InfrastructureResource
from apps.monitoring.models import MonitorCheck, MonitorIncident, MonitorResult
from authentication.models import User


class MonitoringAdminAPITests(TestCase):
    def setUp(self) -> None:
        self.staff = User.objects.create_user(
            email="monitoring-staff@example.test",
            password="test-password",
            first_name="Monitoring",
            last_name="Staff",
            is_staff=True,
        )
        StaffAccessProfile.objects.create(user=self.staff)
        self.hidden_client = Client.objects.create(
            name="Hidden Contact",
            company="Hidden Client",
            email="hidden-monitoring@example.test",
        )
        self.resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Internal Website",
            resource_type=InfrastructureResource.ResourceType.WEBSITE,
            environment=InfrastructureResource.Environment.PRODUCTION,
        )
        self.hidden_resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.hidden_client,
            name="Hidden Website",
            resource_type=InfrastructureResource.ResourceType.WEBSITE,
            environment=InfrastructureResource.Environment.PRODUCTION,
        )
        self.check = MonitorCheck.objects.create(
            resource=self.resource,
            name="Homepage",
            check_type=MonitorCheck.CheckType.HTTP,
            target="https://example.test",
            interval_seconds=300,
            timeout_seconds=10,
        )
        self.hidden_check = MonitorCheck.objects.create(
            resource=self.hidden_resource,
            name="Hidden Homepage",
            check_type=MonitorCheck.CheckType.HTTP,
            target="https://hidden.example.test",
        )
        self.client.force_login(self.staff)

    def grant(self, *codenames: str) -> None:
        permissions = Permission.objects.filter(
            content_type__app_label="monitoring",
            codename__in=codenames,
        )
        self.staff.user_permissions.add(*permissions)

    def config_payload(self, **overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "name": self.check.name,
            "check_type": self.check.check_type,
            "severity": self.check.severity,
            "target": self.check.target,
            "port": self.check.port,
            "expected_value": self.check.expected_value,
            "forbidden_value": self.check.forbidden_value,
            "interval_seconds": self.check.interval_seconds,
            "timeout_seconds": self.check.timeout_seconds,
            "failure_threshold": self.check.failure_threshold,
            "recovery_threshold": self.check.recovery_threshold,
            "expiry_warning_days": self.check.expiry_warning_days,
            "credential_id": self.check.credential_id,
        }
        payload.update(overrides)
        return payload

    def test_check_detail_requires_history_permissions_and_respects_scope(self) -> None:
        denied = self.client.get(f"/api/admin/monitoring/checks/{self.check.id}")
        self.assertEqual(denied.status_code, 403)

        self.grant("view_monitorcheck", "view_monitorresult", "view_monitorincident")

        allowed = self.client.get(f"/api/admin/monitoring/checks/{self.check.id}")
        hidden = self.client.get(f"/api/admin/monitoring/checks/{self.hidden_check.id}")

        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()["id"], self.check.id)
        self.assertEqual(hidden.status_code, 404)

    def test_check_detail_returns_bounded_history_and_health_metrics(self) -> None:
        self.grant("view_monitorcheck", "view_monitorresult", "view_monitorincident")
        now = timezone.now()
        for index in range(55):
            started_at = now - timedelta(minutes=index + 1)
            outcome = MonitorResult.Outcome.SUCCESS if index < 45 else MonitorResult.Outcome.FAILURE
            MonitorResult.objects.create(
                monitor_check=self.check,
                outcome=outcome,
                started_at=started_at,
                finished_at=started_at + timedelta(milliseconds=100 + index),
                duration_ms=100 + index,
                message=f"Result {index}",
            )
        for index in range(25):
            opened_at = now - timedelta(days=index + 1)
            MonitorIncident.objects.create(
                monitor_check=self.check,
                status=MonitorIncident.Status.RESOLVED,
                severity=MonitorCheck.Severity.ERROR,
                opened_at=opened_at,
                resolved_at=opened_at + timedelta(minutes=5),
                failure_count=index + 1,
                summary=f"Incident {index}",
            )

        response = self.client.get(f"/api/admin/monitoring/checks/{self.check.id}")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["results"]), 50)
        self.assertEqual(len(payload["incidents"]), 20)
        self.assertEqual(payload["uptime_24h_percent"], 81.82)
        self.assertIsNotNone(payload["average_response_24h_ms"])
        self.assertIsNone(payload["credential_id"])

    def test_update_check_changes_configuration_without_deleting_history(self) -> None:
        self.grant("change_monitorcheck")
        now = timezone.now()
        result = MonitorResult.objects.create(
            monitor_check=self.check,
            outcome=MonitorResult.Outcome.SUCCESS,
            started_at=now,
            finished_at=now + timedelta(milliseconds=120),
            duration_ms=120,
        )

        response = self.client.put(
            f"/api/admin/monitoring/checks/{self.check.id}",
            data=json.dumps(
                self.config_payload(
                    name="Primary homepage",
                    target="https://www.example.test",
                    interval_seconds=600,
                    failure_threshold=2,
                )
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.check.refresh_from_db()
        self.assertEqual(self.check.name, "Primary homepage")
        self.assertEqual(self.check.target, "https://www.example.test")
        self.assertEqual(self.check.interval_seconds, 600)
        self.assertEqual(self.check.failure_threshold, 2)
        self.assertTrue(MonitorResult.objects.filter(id=result.id).exists())

    def test_pause_and_resume_preserve_history(self) -> None:
        self.grant("change_monitorcheck")
        now = timezone.now()
        result = MonitorResult.objects.create(
            monitor_check=self.check,
            outcome=MonitorResult.Outcome.SUCCESS,
            started_at=now,
            finished_at=now + timedelta(milliseconds=50),
            duration_ms=50,
        )

        paused = self.client.post(f"/api/admin/monitoring/checks/{self.check.id}/pause")
        self.assertEqual(paused.status_code, 200)
        self.check.refresh_from_db()
        self.assertFalse(self.check.enabled)
        self.assertEqual(self.check.status, MonitorCheck.Status.PAUSED)
        self.assertIsNone(self.check.next_run_at)

        resumed = self.client.post(f"/api/admin/monitoring/checks/{self.check.id}/resume")
        self.assertEqual(resumed.status_code, 200)
        self.check.refresh_from_db()
        self.assertTrue(self.check.enabled)
        self.assertEqual(self.check.status, MonitorCheck.Status.PENDING)
        self.assertIsNotNone(self.check.next_run_at)
        self.assertTrue(MonitorResult.objects.filter(id=result.id).exists())

    def test_update_check_cannot_reference_out_of_scope_credential(self) -> None:
        self.grant("change_monitorcheck")
        credential_permission = Permission.objects.get(
            content_type__app_label="credentials",
            codename="view_storedcredential",
        )
        self.staff.user_permissions.add(credential_permission)
        credential_type = CredentialType.objects.create(name="Monitoring Login")
        hidden_credential = StoredCredential.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.hidden_client,
            name="Hidden Login",
            credential_type=credential_type,
            username="hidden-user",
            password="hidden-secret",
        )

        response = self.client.put(
            f"/api/admin/monitoring/checks/{self.check.id}",
            data=json.dumps(self.config_payload(credential_id=hidden_credential.id)),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)
        self.check.refresh_from_db()
        self.assertIsNone(self.check.credential_id)

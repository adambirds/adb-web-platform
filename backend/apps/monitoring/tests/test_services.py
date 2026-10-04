from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.core.ownership import OwnershipType
from apps.infrastructure.models import InfrastructureResource
from apps.monitoring.models import MonitorCheck, MonitorIncident
from apps.monitoring.services import CheckObservation, record_observation


class MonitorIncidentLifecycleTests(TestCase):
    def setUp(self) -> None:
        resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Monitoring test endpoint",
            resource_type=InfrastructureResource.ResourceType.WEBSITE_ENDPOINT,
        )
        self.check = MonitorCheck.objects.create(
            resource=resource,
            name="Public HTTPS",
            check_type=MonitorCheck.CheckType.HTTP,
            target="https://example.test/health",
            failure_threshold=2,
            recovery_threshold=2,
        )

    def _record(self, successful: bool, message: str) -> None:
        started = timezone.now()
        record_observation(
            self.check.id,
            CheckObservation(
                successful=successful,
                started_at=started,
                finished_at=started + timedelta(milliseconds=25),
                duration_ms=25,
                message=message,
            ),
        )
        self.check.refresh_from_db()

    def test_failure_and_recovery_thresholds_drive_one_incident(self) -> None:
        self._record(False, "First failure")
        self.assertEqual(self.check.status, MonitorCheck.Status.DEGRADED)
        self.assertFalse(MonitorIncident.objects.exists())

        self._record(False, "Second failure")
        incident = MonitorIncident.objects.get(monitor_check=self.check)
        self.assertEqual(self.check.status, MonitorCheck.Status.FAILING)
        self.assertEqual(incident.status, MonitorIncident.Status.OPEN)

        self._record(True, "First recovery")
        incident.refresh_from_db()
        self.assertEqual(self.check.status, MonitorCheck.Status.DEGRADED)
        self.assertEqual(incident.status, MonitorIncident.Status.OPEN)

        self._record(True, "Recovered")
        incident.refresh_from_db()
        self.assertEqual(self.check.status, MonitorCheck.Status.HEALTHY)
        self.assertEqual(incident.status, MonitorIncident.Status.RESOLVED)
        self.assertIsNotNone(incident.resolved_at)

    def test_in_flight_result_does_not_unpause_check(self) -> None:
        self.check.enabled = False
        self.check.status = MonitorCheck.Status.PAUSED
        self.check.next_run_at = None
        self.check.save(update_fields=["enabled", "status", "next_run_at"])

        self._record(False, "Finished after pause")

        self.assertEqual(self.check.status, MonitorCheck.Status.PAUSED)
        self.assertIsNone(self.check.next_run_at)
        self.assertEqual(self.check.consecutive_failures, 0)
        self.assertFalse(MonitorIncident.objects.exists())
        self.assertEqual(self.check.results.count(), 1)

    def test_result_messages_are_bounded(self) -> None:
        self._record(False, "x" * 800)
        result = self.check.results.get()
        self.assertEqual(len(result.message), 500)
        self.assertEqual(len(self.check.last_message), 500)

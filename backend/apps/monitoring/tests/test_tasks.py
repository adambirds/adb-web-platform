from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.core.ownership import OwnershipType
from apps.infrastructure.models import InfrastructureResource
from apps.monitoring.models import MonitorCheck
from apps.monitoring.tasks import run_monitor_check


class MonitorTaskTests(TestCase):
    def setUp(self) -> None:
        self.resource = InfrastructureResource.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Scheduled endpoint",
            resource_type=InfrastructureResource.ResourceType.WEBSITE,
        )
        self.check = MonitorCheck.objects.create(
            resource=self.resource,
            name="Website health",
            check_type=MonitorCheck.CheckType.HTTP,
            target="https://example.test/health",
        )

    def test_run_check_skips_when_another_worker_holds_lock(self) -> None:
        with (
            patch("apps.monitoring.tasks._monitor_check_lock") as lock,
            patch("apps.monitoring.tasks.execute_check") as execute,
        ):
            lock.return_value.__enter__.return_value = False
            run_monitor_check(self.check.id)

        execute.assert_not_called()

    def test_run_check_skips_stale_duplicate_after_schedule_advances(self) -> None:
        self.check.next_run_at = timezone.now() + timedelta(minutes=5)
        self.check.save(update_fields=["next_run_at"])

        with (
            patch("apps.monitoring.tasks._monitor_check_lock") as lock,
            patch("apps.monitoring.tasks.execute_check") as execute,
        ):
            lock.return_value.__enter__.return_value = True
            run_monitor_check(self.check.id)

        execute.assert_not_called()

    def test_run_check_executes_due_check_inside_lock(self) -> None:
        self.check.next_run_at = timezone.now() - timedelta(seconds=1)
        self.check.save(update_fields=["next_run_at"])
        observation = object()

        with (
            patch("apps.monitoring.tasks._monitor_check_lock") as lock,
            patch("apps.monitoring.tasks.execute_check", return_value=observation) as execute,
            patch("apps.monitoring.tasks.record_observation") as record,
        ):
            lock.return_value.__enter__.return_value = True
            run_monitor_check(self.check.id)

        execute.assert_called_once()
        record.assert_called_once_with(self.check.id, observation)

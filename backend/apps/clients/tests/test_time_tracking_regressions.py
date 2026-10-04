from datetime import timedelta
from typing import cast

from django.http import HttpRequest
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.clients.models import Client, Project, RunningTimer, TimeEntry
from apps.clients.ninja.time_schemas import TimeEntryOut, TimerStartIn, TimerStopIn
from apps.clients.ninja.time_views import start_time_timer, stop_time_timer
from apps.core.ownership import OwnershipType
from apps.tasks.models import Task
from authentication.models import User


class TimerStopRegressionTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            email="timer-stop@example.com",
            password="test-password",
            first_name="Timer",
            last_name="Stop",
        )
        self.client_record = Client.objects.create(
            name="Timer Client",
            company="Timer Client Ltd",
            email="timer-client@example.com",
        )
        self.project = Project.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_record,
            name="Timer Project",
            start_date=timezone.localdate(),
        )
        self.task = Task.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_record,
            project=self.project,
            title="Investigate timer regression",
        )

    def _request(self) -> HttpRequest:
        request = self.factory.post("/api/admin/time-timer/stop")
        request.user = self.user
        return request

    def test_blank_timer_description_falls_back_to_work_context(self) -> None:
        start_result = start_time_timer(
            self._request(),
            TimerStartIn(description="", task_id=self.task.id),
        )
        self.assertIsInstance(start_result, tuple)
        timer = RunningTimer.objects.get(user=self.user)
        timer.started_at = timezone.now() - timedelta(minutes=5)
        timer.save(update_fields=["started_at"])

        result = stop_time_timer(self._request(), TimerStopIn(description=""))

        entry = cast(TimeEntryOut, result)
        self.assertEqual(entry.description, self.task.title)
        self.assertGreater(entry.duration_hours, 0)
        self.assertFalse(RunningTimer.objects.filter(user=self.user).exists())
        self.assertTrue(TimeEntry.objects.filter(id=entry.id).exists())

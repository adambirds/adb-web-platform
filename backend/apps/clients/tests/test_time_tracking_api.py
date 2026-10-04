from datetime import timedelta
from decimal import Decimal
from typing import Any, cast

from django.contrib.auth.models import Permission
from django.http import HttpRequest
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client, Project, RunningTimer, TimeEntry
from apps.clients.ninja.time_schemas import TimeEntryIn, TimeEntryOut, TimerStartIn, TimerStopIn
from apps.clients.ninja.time_views import (
    create_time_entry,
    current_timer,
    start_time_timer,
    stop_time_timer,
)
from apps.core.models import Brand
from apps.core.ownership import OwnershipType
from apps.tasks.models import Task
from apps.ticketing.models import Ticket, TicketQueue
from authentication.models import User


class TimeTrackingApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.superuser = User.objects.create_superuser(
            email="time-admin@example.com",
            password="test-password",
            first_name="Time",
            last_name="Admin",
        )
        self.client_record = Client.objects.create(
            name="Client Contact",
            company="Client Ltd",
            email="client@example.com",
        )
        self.other_client = Client.objects.create(
            name="Other Contact",
            company="Other Ltd",
            email="other@example.com",
        )
        self.client_project = Project.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_record,
            name="Client Project",
            start_date=timezone.localdate(),
        )
        self.internal_project = Project.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Internal Project",
            start_date=timezone.localdate(),
        )
        self.client_task = Task.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_record,
            project=self.client_project,
            title="Client task",
        )
        self.internal_task = Task.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            project=self.internal_project,
            title="Internal task",
        )
        self.brand = Brand.objects.create(
            name="ADB Test",
            slug="adb-test",
            domain="test.adb.example",
        )
        self.queue = TicketQueue.objects.create(
            name="Support",
            key="test-support",
            brand=self.brand,
        )
        self.client_ticket = Ticket.objects.create(
            brand=self.brand,
            queue=self.queue,
            client=self.client_record,
            subject="Client ticket",
        )
        self.internal_ticket = Ticket.objects.create(
            brand=self.brand,
            queue=self.queue,
            client=None,
            subject="Unmatched operational ticket",
        )

    def _request(self, user: User, method: str = "get") -> HttpRequest:
        request = getattr(self.factory, method)("/api/admin/time-records")
        request.user = user
        return request

    def test_project_context_derives_client_ownership(self) -> None:
        status, payload = create_time_entry(
            self._request(self.superuser, "post"),
            TimeEntryIn(
                date=timezone.localdate(),
                duration_hours=Decimal("1.5"),
                description="Project work",
                billable=True,
                ownership_type="internal",
                project_id=self.client_project.id,
            ),
        )
        self.assertEqual(status, 201)
        detail = cast(TimeEntryOut, payload)
        entry = TimeEntry.objects.get(id=detail.id)
        self.assertEqual(entry.ownership_type, OwnershipType.CLIENT)
        self.assertEqual(entry.client, self.client_record)
        self.assertEqual(entry.project, self.client_project)
        self.assertTrue(entry.billable)

    def test_internal_project_time_never_uses_fake_client_or_billable_flag(self) -> None:
        status, payload = create_time_entry(
            self._request(self.superuser, "post"),
            TimeEntryIn(
                date=timezone.localdate(),
                duration_hours=Decimal("0.75"),
                description="Internal development",
                billable=True,
                ownership_type="client",
                client_id=self.client_record.id,
                project_id=self.internal_project.id,
            ),
        )
        self.assertEqual(status, 201)
        detail = cast(TimeEntryOut, payload)
        entry = TimeEntry.objects.get(id=detail.id)
        self.assertEqual(entry.ownership_type, OwnershipType.INTERNAL)
        self.assertIsNone(entry.client)
        self.assertEqual(entry.project, self.internal_project)
        self.assertFalse(entry.billable)

    def test_task_context_derives_project_and_client(self) -> None:
        status, payload = create_time_entry(
            self._request(self.superuser, "post"),
            TimeEntryIn(
                date=timezone.localdate(),
                duration_hours=Decimal(2),
                description="Task implementation",
                task_id=self.client_task.id,
            ),
        )
        self.assertEqual(status, 201)
        detail = cast(TimeEntryOut, payload)
        entry = TimeEntry.objects.get(id=detail.id)
        self.assertEqual(entry.task, self.client_task)
        self.assertEqual(entry.project, self.client_project)
        self.assertEqual(entry.client, self.client_record)

    def test_ticket_context_supports_client_and_unmatched_internal_time(self) -> None:
        client_status, client_payload = create_time_entry(
            self._request(self.superuser, "post"),
            TimeEntryIn(
                date=timezone.localdate(),
                duration_hours=Decimal("0.5"),
                description="Ticket investigation",
                ticket_id=self.client_ticket.id,
            ),
        )
        internal_status, internal_payload = create_time_entry(
            self._request(self.superuser, "post"),
            TimeEntryIn(
                date=timezone.localdate(),
                duration_hours=Decimal("0.25"),
                description="Operational ticket",
                billable=True,
                ticket_id=self.internal_ticket.id,
            ),
        )
        self.assertEqual(client_status, 201)
        self.assertEqual(internal_status, 201)
        client_detail = cast(TimeEntryOut, client_payload)
        internal_detail = cast(TimeEntryOut, internal_payload)
        client_entry = TimeEntry.objects.get(id=client_detail.id)
        internal_entry = TimeEntry.objects.get(id=internal_detail.id)
        self.assertEqual(client_entry.client, self.client_record)
        self.assertEqual(client_entry.ticket, self.client_ticket)
        self.assertEqual(internal_entry.ownership_type, OwnershipType.INTERNAL)
        self.assertIsNone(internal_entry.client)
        self.assertFalse(internal_entry.billable)

    def test_running_timer_is_persistent_and_stops_into_time_entry(self) -> None:
        status, _payload = start_time_timer(
            self._request(self.superuser, "post"),
            TimerStartIn(
                description="Timed task",
                billable=True,
                task_id=self.client_task.id,
            ),
        )
        self.assertEqual(status, 201)
        timer = RunningTimer.objects.get(user=self.superuser)
        timer.started_at = timezone.now() - timedelta(minutes=30)
        timer.save(update_fields=["started_at"])

        current = current_timer(self._request(self.superuser))
        self.assertIsNotNone(current)
        current_payload = cast(Any, current)
        self.assertEqual(current_payload.task_id, self.client_task.id)

        stopped = stop_time_timer(
            self._request(self.superuser, "post"),
            TimerStopIn(description="Timed task completed"),
        )
        detail = cast(TimeEntryOut, stopped)
        entry = TimeEntry.objects.get(id=detail.id)
        self.assertEqual(entry.entry_type, TimeEntry.EntryType.TIMER)
        self.assertEqual(entry.task, self.client_task)
        self.assertGreater(entry.duration_hours, 0)
        self.assertFalse(RunningTimer.objects.filter(user=self.superuser).exists())
        self.assertEqual(detail.description, "Timed task completed")

    def test_only_one_running_timer_is_allowed_per_user(self) -> None:
        first_status, _ = start_time_timer(
            self._request(self.superuser, "post"),
            TimerStartIn(description="First", project_id=self.client_project.id),
        )
        result = start_time_timer(
            self._request(self.superuser, "post"),
            TimerStartIn(description="Second", project_id=self.client_project.id),
        )
        self.assertEqual(first_status, 201)
        self.assertIsInstance(result, tuple)
        status, payload = result
        self.assertEqual(status, 409)
        problem = cast(dict[str, Any], payload)
        self.assertEqual(problem["code"], "timer_already_running")

    def test_client_scope_rejects_hidden_project_context(self) -> None:
        restricted = User.objects.create_user(
            email="time-agent@example.com",
            password="test-password",
            first_name="Time",
            last_name="Agent",
            is_staff=True,
        )
        restricted.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="clients",
                codename="add_timeentry",
            ),
            Permission.objects.get(
                content_type__app_label="clients",
                codename="view_project",
            ),
        )
        profile = StaffAccessProfile.objects.create(user=restricted, all_clients=False)
        ClientAccessGrant.objects.create(profile=profile, client=self.client_record)
        hidden_project = Project.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.other_client,
            name="Hidden Project",
            start_date=timezone.localdate(),
        )

        result = create_time_entry(
            self._request(restricted, "post"),
            TimeEntryIn(
                date=timezone.localdate(),
                duration_hours=Decimal(1),
                description="Should not be allowed",
                project_id=hidden_project.id,
            ),
        )
        self.assertIsInstance(result, tuple)
        status, payload = result
        self.assertEqual(status, 404)
        problem = cast(dict[str, Any], payload)
        self.assertEqual(problem["code"], "not_found")

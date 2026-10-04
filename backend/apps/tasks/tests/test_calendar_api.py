from datetime import date
from typing import cast

from django.contrib.auth.models import Permission
from django.http import HttpRequest
from django.test import RequestFactory, TestCase

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client, Project
from apps.core.ownership import OwnershipType
from apps.tasks.models import Task
from apps.tasks.ninja.calendar_schemas import CalendarOut
from apps.tasks.ninja.calendar_views import work_calendar
from authentication.models import User


class WorkCalendarApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.superuser = User.objects.create_superuser(
            email="calendar-admin@example.com",
            password="test-password",
            first_name="Calendar",
            last_name="Admin",
        )
        self.primary_client = Client.objects.create(
            name="Primary",
            company="Primary Ltd",
            email="primary-calendar@example.com",
        )
        self.hidden_client = Client.objects.create(
            name="Hidden",
            company="Hidden Ltd",
            email="hidden-calendar@example.com",
        )

    def _request(self, user: User) -> HttpRequest:
        request = self.factory.get("/api/admin/calendar")
        request.user = user
        return request

    def test_calendar_includes_task_and_project_spans_that_overlap_range(self) -> None:
        project = Project.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.primary_client,
            name="Website launch",
            start_date=date(2026, 8, 10),
            end_date=date(2026, 9, 4),
        )
        task = Task.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.primary_client,
            project=project,
            title="Launch QA",
            start_date=date(2026, 8, 19),
            due_date=date(2026, 8, 21),
        )
        Task.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.primary_client,
            project=project,
            title="Outside range",
            due_date=date(2026, 10, 1),
        )

        result = work_calendar(
            self._request(self.superuser),
            date_from=date(2026, 8, 17),
            date_to=date(2026, 9, 6),
        )

        calendar = cast(CalendarOut, result)
        self.assertEqual(calendar.project_count, 1)
        self.assertEqual(calendar.task_count, 1)
        task_item = next(item for item in calendar.items if item.kind == "task")
        self.assertEqual(task_item.id, task.id)
        self.assertEqual(task_item.start_date, date(2026, 8, 19))
        self.assertEqual(task_item.end_date, date(2026, 8, 21))
        project_item = next(item for item in calendar.items if item.kind == "project")
        self.assertEqual(project_item.id, project.id)

    def test_calendar_respects_client_scope_and_keeps_internal_work_visible(self) -> None:
        user = User.objects.create_user(
            email="calendar-staff@example.com",
            password="test-password",
            first_name="Calendar",
            last_name="Staff",
            is_staff=True,
        )
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="tasks",
                codename="view_task",
            ),
            Permission.objects.get(
                content_type__app_label="clients",
                codename="view_project",
            ),
        )
        profile = StaffAccessProfile.objects.create(user=user, all_clients=False)
        ClientAccessGrant.objects.create(
            profile=profile,
            client=self.primary_client,
            granted_by=self.superuser,
        )

        visible_project = Project.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.primary_client,
            name="Visible project",
            start_date=date(2026, 8, 20),
        )
        hidden_project = Project.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.hidden_client,
            name="Hidden project",
            start_date=date(2026, 8, 20),
        )
        internal_project = Project.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Internal project",
            start_date=date(2026, 8, 20),
        )
        Task.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.primary_client,
            project=visible_project,
            title="Visible task",
            due_date=date(2026, 8, 20),
        )
        Task.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.hidden_client,
            project=hidden_project,
            title="Hidden task",
            due_date=date(2026, 8, 20),
        )
        Task.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            project=internal_project,
            title="Internal task",
            due_date=date(2026, 8, 20),
        )

        result = work_calendar(
            self._request(user),
            date_from=date(2026, 8, 17),
            date_to=date(2026, 8, 23),
        )

        calendar = cast(CalendarOut, result)
        titles = {item.title for item in calendar.items}
        self.assertIn("Visible project", titles)
        self.assertIn("Visible task", titles)
        self.assertIn("Internal project", titles)
        self.assertIn("Internal task", titles)
        self.assertNotIn("Hidden project", titles)
        self.assertNotIn("Hidden task", titles)

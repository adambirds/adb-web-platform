from decimal import Decimal
from typing import Any, cast

from django.contrib.auth.models import Permission
from django.http import HttpRequest
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client, Project, TimeEntry
from apps.clients.ninja.admin_views import (
    create_project,
    get_project,
    list_projects,
    update_project,
)
from apps.clients.ninja.schemas import ProjectDetailOut, ProjectIn, ProjectSummaryOut
from apps.tasks.models import Task
from authentication.models import User


class ProjectAdminApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="test-password",
            first_name="Admin",
            last_name="User",
        )
        self.client = Client.objects.create(
            name="Primary Client",
            company="Primary Ltd",
            email="primary@example.com",
        )
        self.other_client = Client.objects.create(
            name="Other Client",
            company="Other Ltd",
            email="other@example.com",
        )

    def _request(self, user: User, method: str = "get") -> HttpRequest:
        request = getattr(self.factory, method)("/api/admin/projects")
        request.user = user
        return request

    def _payload(self, **overrides: Any) -> ProjectIn:
        values: dict[str, Any] = {
            "name": "Platform delivery",
            "description": "Operational project",
            "status": "active",
            "ownership_type": "client",
            "client_id": self.client.id,
            "start_date": "2026-08-01",
            "end_date": "2026-10-31",
            "budget": "12000.00",
            "hourly_rate": "95.00",
        }
        values.update(overrides)
        return ProjectIn(**values)

    def _staff_with_permissions(self, *permissions: tuple[str, str]) -> User:
        user = User.objects.create_user(
            email=f"staff-{User.objects.count()}@example.com",
            password="test-password",
            first_name="Project",
            last_name="Staff",
            is_staff=True,
        )
        for app_label, codename in permissions:
            permission = Permission.objects.get(
                content_type__app_label=app_label,
                codename=codename,
            )
            user.user_permissions.add(permission)
        return user

    def _grant_client(self, user: User, client: Client) -> None:
        profile, _ = StaffAccessProfile.objects.get_or_create(
            user=user,
            defaults={"all_clients": False},
        )
        ClientAccessGrant.objects.get_or_create(
            profile=profile,
            client=client,
            defaults={"granted_by": self.superuser},
        )

    def test_superuser_can_create_internal_project(self) -> None:
        result = create_project(
            self._request(self.superuser, "post"),
            self._payload(ownership_type="internal", client_id=None),
        )

        self.assertIsInstance(result, tuple)
        status_code, response = cast(tuple[int, ProjectDetailOut], result)
        self.assertEqual(status_code, 201)
        project = Project.objects.get(id=response.id)
        self.assertEqual(project.ownership_type, "internal")
        self.assertIsNone(project.client_id)

    def test_staff_can_create_project_for_client_in_scope(self) -> None:
        user = self._staff_with_permissions(("clients", "add_project"))
        self._grant_client(user, self.client)

        result = create_project(self._request(user, "post"), self._payload())

        self.assertIsInstance(result, tuple)
        status_code, response = cast(tuple[int, ProjectDetailOut], result)
        self.assertEqual(status_code, 201)
        self.assertEqual(response.client_id, self.client.id)

    def test_staff_cannot_create_project_for_client_outside_scope(self) -> None:
        user = self._staff_with_permissions(("clients", "add_project"))
        StaffAccessProfile.objects.create(user=user, all_clients=False)

        result = create_project(
            self._request(user, "post"),
            self._payload(client_id=self.other_client.id),
        )

        self.assertIsInstance(result, tuple)
        status_code, problem = cast(tuple[int, dict[str, Any]], result)
        self.assertEqual(status_code, 404)
        self.assertEqual(problem["code"], "not_found")

    def test_list_and_detail_respect_client_scope_but_include_internal(self) -> None:
        user = self._staff_with_permissions(("clients", "view_project"))
        self._grant_client(user, self.client)
        visible = Project.objects.create(
            ownership_type="client",
            client=self.client,
            name="Visible",
            start_date=timezone.localdate(),
        )
        hidden = Project.objects.create(
            ownership_type="client",
            client=self.other_client,
            name="Hidden",
            start_date=timezone.localdate(),
        )
        internal = Project.objects.create(
            ownership_type="internal",
            name="Internal",
            start_date=timezone.localdate(),
        )

        rows = list_projects(self._request(user))
        self.assertIsInstance(rows, list)
        project_ids = {row.id for row in cast(list[ProjectSummaryOut], rows)}
        self.assertEqual(project_ids, {visible.id, internal.id})

        detail = get_project(self._request(user), hidden.id)
        self.assertIsInstance(detail, tuple)
        status_code, problem = cast(tuple[int, dict[str, Any]], detail)
        self.assertEqual(status_code, 404)
        self.assertEqual(problem["code"], "not_found")

    def test_update_project_changes_operational_fields(self) -> None:
        project = Project.objects.create(
            ownership_type="client",
            client=self.client,
            name="Original",
            start_date=timezone.localdate(),
        )

        result = update_project(
            self._request(self.superuser, "put"),
            project.id,
            self._payload(name="Updated", status="paused", budget="15000.00"),
        )

        self.assertIsInstance(result, ProjectDetailOut)
        project.refresh_from_db()
        self.assertEqual(project.name, "Updated")
        self.assertEqual(project.status, "paused")
        self.assertEqual(project.budget, Decimal("15000.00"))

    def test_project_validation_rejects_invalid_dates_and_negative_money(self) -> None:
        date_result = create_project(
            self._request(self.superuser, "post"),
            self._payload(start_date="2026-10-01", end_date="2026-09-30"),
        )
        money_result = create_project(
            self._request(self.superuser, "post"),
            self._payload(budget="-1.00"),
        )

        self.assertEqual(cast(tuple[int, dict[str, Any]], date_result)[0], 400)
        self.assertEqual(cast(tuple[int, dict[str, Any]], money_result)[0], 400)

    def test_ownership_change_is_blocked_when_related_work_exists(self) -> None:
        project = Project.objects.create(
            ownership_type="client",
            client=self.client,
            name="In use",
            start_date=timezone.localdate(),
        )
        Task.objects.create(
            ownership_type="client",
            client=self.client,
            project=project,
            title="Linked task",
        )

        result = update_project(
            self._request(self.superuser, "put"),
            project.id,
            self._payload(ownership_type="internal", client_id=None),
        )

        self.assertIsInstance(result, tuple)
        status_code, problem = cast(tuple[int, dict[str, Any]], result)
        self.assertEqual(status_code, 400)
        self.assertEqual(problem["code"], "ownership_in_use")

    def test_project_detail_reports_permitted_task_and_time_totals(self) -> None:
        user = self._staff_with_permissions(
            ("clients", "view_project"),
            ("clients", "view_timeentry"),
            ("tasks", "view_task"),
        )
        self._grant_client(user, self.client)
        project = Project.objects.create(
            ownership_type="client",
            client=self.client,
            name="Measured",
            start_date=timezone.localdate(),
        )
        Task.objects.create(
            ownership_type="client",
            client=self.client,
            project=project,
            title="Open task",
        )
        Task.objects.create(
            ownership_type="client",
            client=self.client,
            project=project,
            title="Completed task",
            completed_at=timezone.now(),
        )
        TimeEntry.objects.create(
            ownership_type="client",
            client=self.client,
            project=project,
            user=user,
            date=timezone.localdate(),
            duration_hours=Decimal("2.50"),
            description="Billable work",
            billable=True,
        )
        TimeEntry.objects.create(
            ownership_type="client",
            client=self.client,
            project=project,
            user=user,
            date=timezone.localdate(),
            duration_hours=Decimal("1.25"),
            description="Non-billable work",
            billable=False,
        )

        detail = get_project(self._request(user), project.id)

        self.assertIsInstance(detail, ProjectDetailOut)
        response = cast(ProjectDetailOut, detail)
        self.assertEqual(response.task_count, 2)
        self.assertEqual(response.open_task_count, 1)
        self.assertEqual(response.time_entry_count, 2)
        self.assertEqual(response.tracked_hours, Decimal("3.75"))
        self.assertEqual(response.billable_hours, Decimal("2.50"))

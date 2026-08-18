from datetime import date

from django.contrib.auth.models import Permission
from django.test import TestCase

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client, Project, TimeEntry
from apps.core.ownership import OwnershipType
from apps.crm.models import Lead
from apps.tasks.models import Task
from authentication.models import User


class AdminOperationsAPITests(TestCase):
    def setUp(self) -> None:
        self.staff = User.objects.create_user(
            email="operations@example.com",
            password="test-password",
            first_name="Operations",
            last_name="Staff",
            is_staff=True,
        )
        self.profile = StaffAccessProfile.objects.create(user=self.staff)

        self.allowed_client = Client.objects.create(
            name="Allowed Contact",
            company="Allowed Client",
            email="allowed@example.test",
        )
        self.hidden_client = Client.objects.create(
            name="Hidden Contact",
            company="Hidden Client",
            email="hidden@example.test",
        )
        ClientAccessGrant.objects.create(
            profile=self.profile,
            client=self.allowed_client,
            granted_by=self.staff,
        )

        self.allowed_project = Project.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.allowed_client,
            name="Allowed Project",
            start_date=date(2026, 1, 1),
        )
        self.hidden_project = Project.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.hidden_client,
            name="Hidden Project",
            start_date=date(2026, 1, 1),
        )
        self.internal_project = Project.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Internal Project",
            start_date=date(2026, 1, 1),
        )

        Task.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.allowed_client,
            project=self.allowed_project,
            title="Allowed Task",
        )
        Task.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.hidden_client,
            project=self.hidden_project,
            title="Hidden Task",
        )
        Task.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            title="Internal Task",
        )

        TimeEntry.objects.create(
            project=self.allowed_project,
            date=date(2026, 2, 1),
            duration_hours="1.50",
            description="Allowed time",
            user=self.staff,
        )
        TimeEntry.objects.create(
            project=self.hidden_project,
            date=date(2026, 2, 1),
            duration_hours="2.00",
            description="Hidden time",
        )
        TimeEntry.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            date=date(2026, 2, 1),
            duration_hours="0.50",
            description="Internal time",
        )

        Lead.objects.create(
            name="Demo Lead",
            email="lead@example.test",
            company="Lead Company",
        )

        self.client.force_login(self.staff)

    def grant(self, app_label: str, codename: str) -> None:
        permission = Permission.objects.get(
            content_type__app_label=app_label,
            codename=codename,
        )
        self.staff.user_permissions.add(permission)

    def test_client_list_requires_capability_permission(self) -> None:
        response = self.client.get("/api/admin/clients")
        self.assertEqual(response.status_code, 403)

    def test_client_list_respects_object_scope(self) -> None:
        self.grant("clients", "view_client")

        response = self.client.get("/api/admin/clients")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [client["company"] for client in response.json()],
            ["Allowed Client"],
        )

    def test_project_list_includes_internal_and_scoped_client_projects(self) -> None:
        self.grant("clients", "view_project")

        response = self.client.get("/api/admin/projects")

        self.assertEqual(response.status_code, 200)
        names = {project["name"] for project in response.json()}
        self.assertSetEqual(names, {"Allowed Project", "Internal Project"})

    def test_task_list_includes_internal_and_scoped_client_tasks(self) -> None:
        self.grant("tasks", "view_task")

        response = self.client.get("/api/admin/tasks")

        self.assertEqual(response.status_code, 200)
        titles = {task["title"] for task in response.json()}
        self.assertSetEqual(titles, {"Allowed Task", "Internal Task"})

    def test_time_entry_list_includes_internal_and_scoped_client_time(self) -> None:
        self.grant("clients", "view_timeentry")

        response = self.client.get("/api/admin/time-entries")

        self.assertEqual(response.status_code, 200)
        descriptions = {entry["description"] for entry in response.json()}
        self.assertSetEqual(descriptions, {"Allowed time", "Internal time"})

    def test_lead_list_requires_permission_then_returns_pipeline(self) -> None:
        denied = self.client.get("/api/admin/leads")
        self.assertEqual(denied.status_code, 403)

        self.grant("crm", "view_lead")
        allowed = self.client.get("/api/admin/leads")

        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(
            [lead["company"] for lead in allowed.json()],
            ["Lead Company"],
        )

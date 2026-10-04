from datetime import timedelta
from typing import Any, cast

from django.contrib.auth.models import Permission
from django.http import HttpRequest
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client, Project
from apps.core.ownership import OwnershipType
from apps.tasks.models import Task, TaskList, TaskStatus
from apps.tasks.ninja.admin_views import (
    complete_task_view,
    create_task,
    create_task_list,
    get_task,
    list_tasks,
)
from apps.tasks.ninja.schemas import (
    TaskDetailOut,
    TaskIn,
    TaskListDetailOut,
    TaskListIn,
    TaskPageOut,
)
from authentication.models import User


class TaskAdminApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.superuser = User.objects.create_superuser(
            email="task-admin@example.com",
            password="test-password",
            first_name="Task",
            last_name="Admin",
        )
        self.primary_client = Client.objects.create(
            name="Primary",
            company="Primary Ltd",
            email="primary@example.com",
        )
        self.other_client = Client.objects.create(
            name="Other",
            company="Other Ltd",
            email="other@example.com",
        )
        self.client_project = Project.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.primary_client,
            name="Client project",
            start_date=timezone.localdate(),
        )
        self.internal_project = Project.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            client=None,
            name="Internal project",
            start_date=timezone.localdate(),
        )
        self.todo = TaskStatus.objects.create(name="To do", color="#38bdf8", order=10)
        self.done = TaskStatus.objects.create(name="Done", color="#22c55e", order=20)

    def _request(self, user: User, method: str = "get") -> HttpRequest:
        request = getattr(self.factory, method)("/api/admin/tasks")
        request.user = user
        return request

    def _restricted_user(self, email: str) -> User:
        user = User.objects.create_user(
            email=email,
            password="test-password",
            first_name="Task",
            last_name="Agent",
            is_staff=True,
        )
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="tasks",
                codename="view_task",
            )
        )
        profile = StaffAccessProfile.objects.create(user=user, all_clients=False)
        ClientAccessGrant.objects.create(profile=profile, client=self.primary_client)
        return user

    def test_project_context_is_authoritative_for_client_task(self) -> None:
        status, payload = create_task(
            self._request(self.superuser, "post"),
            TaskIn(
                title="Client project task",
                ownership_type="internal",
                project_id=self.client_project.id,
                status_id=self.todo.id,
            ),
        )
        self.assertEqual(status, 201)
        detail = cast(TaskDetailOut, payload)
        task = Task.objects.get(id=detail.id)
        self.assertEqual(task.ownership_type, OwnershipType.CLIENT)
        self.assertEqual(task.client, self.primary_client)
        self.assertEqual(task.project, self.client_project)

    def test_internal_project_never_requires_fake_client(self) -> None:
        status, payload = create_task(
            self._request(self.superuser, "post"),
            TaskIn(
                title="Internal project task",
                ownership_type="client",
                project_id=self.internal_project.id,
                client_id=self.primary_client.id,
                status_id=self.todo.id,
            ),
        )
        self.assertEqual(status, 201)
        detail = cast(TaskDetailOut, payload)
        task = Task.objects.get(id=detail.id)
        self.assertEqual(task.ownership_type, OwnershipType.INTERNAL)
        self.assertIsNone(task.client)
        self.assertEqual(task.project, self.internal_project)

    def test_standalone_internal_recurring_task_is_first_class(self) -> None:
        status, payload = create_task(
            self._request(self.superuser, "post"),
            TaskIn(
                title="Send monthly invoices",
                ownership_type="internal",
                status_id=self.todo.id,
                due_date=timezone.localdate(),
                recurrence_frequency="monthly",
            ),
        )
        self.assertEqual(status, 201)
        detail = cast(TaskDetailOut, payload)
        task = Task.objects.get(id=detail.id)
        self.assertIsNone(task.client)
        self.assertIsNone(task.project)
        self.assertEqual(task.recurrence_rule, "FREQ=MONTHLY;INTERVAL=1")

    def test_recurring_completion_creates_one_future_occurrence(self) -> None:
        today = timezone.localdate()
        task = Task.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            title="Daily administration",
            status=self.todo,
            due_date=today,
            recurrence_rule="FREQ=DAILY;INTERVAL=1",
            created_by=self.superuser,
        )

        complete_task_view(self._request(self.superuser, "post"), task.id)
        complete_task_view(self._request(self.superuser, "post"), task.id)

        task.refresh_from_db()
        self.assertIsNotNone(task.completed_at)
        self.assertEqual(task.status, self.done)
        next_task = task.next_occurrence
        self.assertEqual(next_task.due_date, today + timedelta(days=1))
        self.assertIsNone(next_task.completed_at)
        self.assertEqual(next_task.previous_occurrence, task)
        self.assertEqual(Task.objects.filter(previous_occurrence=task).count(), 1)

    def test_recurring_task_requires_due_date(self) -> None:
        result = create_task(
            self._request(self.superuser, "post"),
            TaskIn(
                title="Invalid recurring task",
                ownership_type="internal",
                recurrence_frequency="daily",
            ),
        )
        self.assertIsInstance(result, tuple)
        status, payload = result
        self.assertEqual(status, 400)
        problem = cast(dict[str, Any], payload)
        self.assertEqual(problem["code"], "recurrence_requires_due_date")

    def test_task_lists_support_internal_and_project_contexts(self) -> None:
        internal_status, internal_payload = create_task_list(
            self._request(self.superuser, "post"),
            TaskListIn(name="Monthly admin", ownership_type="internal"),
        )
        project_status, project_payload = create_task_list(
            self._request(self.superuser, "post"),
            TaskListIn(
                name="Delivery",
                ownership_type="internal",
                project_id=self.client_project.id,
            ),
        )
        self.assertEqual(internal_status, 201)
        self.assertEqual(project_status, 201)
        internal_detail = cast(TaskListDetailOut, internal_payload)
        project_detail = cast(TaskListDetailOut, project_payload)
        internal_list = TaskList.objects.get(id=internal_detail.id)
        project_list = TaskList.objects.get(id=project_detail.id)
        self.assertIsNone(internal_list.client)
        self.assertEqual(project_list.ownership_type, OwnershipType.CLIENT)
        self.assertEqual(project_list.client, self.primary_client)

    def test_client_scope_hides_other_client_tasks_but_keeps_internal(self) -> None:
        user = self._restricted_user("task-agent@example.com")
        primary = Task.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.primary_client,
            title="Primary task",
            status=self.todo,
        )
        Task.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.other_client,
            title="Other task",
            status=self.todo,
        )
        internal = Task.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            title="Internal task",
            status=self.todo,
        )

        result = list_tasks(self._request(user))
        page = cast(TaskPageOut, result)
        ids = {task.id for task in page.items}
        self.assertSetEqual(ids, {primary.id, internal.id})

    def test_inaccessible_task_detail_returns_not_found(self) -> None:
        user = self._restricted_user("restricted-agent@example.com")
        task = Task.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.other_client,
            title="Hidden task",
            status=self.todo,
        )
        result = get_task(self._request(user), task.id)
        self.assertIsInstance(result, tuple)
        status, payload = result
        self.assertEqual(status, 404)
        problem = cast(dict[str, Any], payload)
        self.assertEqual(problem["code"], "not_found")

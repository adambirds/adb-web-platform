from datetime import timedelta
from typing import Any, cast

from django.http import HttpRequest
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.core.ownership import OwnershipType
from apps.tasks.models import Task, TaskStatus
from apps.tasks.ninja.quick_schemas import TaskQuickUpdateIn
from apps.tasks.ninja.quick_views import quick_update_task
from apps.tasks.ninja.schemas import TaskDetailOut
from authentication.models import User


class TaskQuickUpdateApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            email="quick-task@example.com",
            password="test-password",
            first_name="Quick",
            last_name="Task",
        )
        self.assignee = User.objects.create_user(
            email="assignee@example.com",
            password="test-password",
            first_name="Assigned",
            last_name="User",
            is_staff=True,
        )
        self.status = TaskStatus.objects.create(name="To do", color="#38bdf8", order=10)
        self.task = Task.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            title="Original task",
            description="Original description",
            status=self.status,
            created_by=self.user,
        )

    def _request(self) -> HttpRequest:
        request = self.factory.patch(f"/api/admin/tasks/{self.task.id}/quick-update")
        request.user = self.user
        return request

    def test_quick_update_changes_everyday_task_fields(self) -> None:
        today = timezone.localdate()
        result = quick_update_task(
            self._request(),
            self.task.id,
            TaskQuickUpdateIn(
                title="Updated task",
                description="Updated description",
                priority=4,
                start_date=today,
                due_date=today + timedelta(days=3),
                assigned_to_id=self.assignee.id,
            ),
        )

        detail = cast(TaskDetailOut, result)
        self.task.refresh_from_db()
        self.assertEqual(detail.title, "Updated task")
        self.assertEqual(self.task.description, "Updated description")
        self.assertEqual(self.task.priority, 4)
        self.assertEqual(self.task.start_date, today)
        self.assertEqual(self.task.due_date, today + timedelta(days=3))
        self.assertEqual(self.task.assigned_to, self.assignee)

    def test_quick_update_can_clear_optional_fields(self) -> None:
        self.task.due_date = timezone.localdate()
        self.task.assigned_to = self.assignee
        self.task.save()

        result = quick_update_task(
            self._request(),
            self.task.id,
            TaskQuickUpdateIn(due_date=None, assigned_to_id=None),
        )

        self.assertIsInstance(result, TaskDetailOut)
        self.task.refresh_from_db()
        self.assertIsNone(self.task.due_date)
        self.assertIsNone(self.task.assigned_to)

    def test_completed_task_must_be_reopened_before_quick_update(self) -> None:
        self.task.completed_at = timezone.now()
        self.task.save()

        result = quick_update_task(
            self._request(),
            self.task.id,
            TaskQuickUpdateIn(title="Should not save"),
        )

        self.assertIsInstance(result, tuple)
        status, payload = result
        self.assertEqual(status, 400)
        problem = cast(dict[str, Any], payload)
        self.assertEqual(problem["code"], "task_completed")

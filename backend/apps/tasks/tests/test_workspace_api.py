from typing import cast

from django.http import HttpRequest
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.clients.models import Project
from apps.core.ownership import OwnershipType
from apps.tasks.models import Task, TaskList, TaskSection
from apps.tasks.ninja.workspace_schemas import TaskMoveIn, TaskWorkspaceTaskOut
from apps.tasks.ninja.workspace_views import move_task
from authentication.models import User


class TaskWorkspaceApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.superuser = User.objects.create_superuser(
            email="task-workspace-admin@example.com",
            password="test-password",
            first_name="Task",
            last_name="Workspace",
        )
        self.project = Project.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            client=None,
            name="Internal delivery",
            start_date=timezone.localdate(),
        )
        self.task_list = TaskList.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            client=None,
            project=self.project,
            name="Delivery",
        )
        self.section = TaskSection.objects.create(
            task_list=self.task_list,
            name="In progress",
        )

    def _request(self) -> HttpRequest:
        request = self.factory.post("/api/admin/task-workspaces/tasks/1/move")
        request.user = self.superuser
        return request

    def test_move_task_can_clear_project_task_list(self) -> None:
        task = Task.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            client=None,
            project=self.project,
            task_list=self.task_list,
            section=self.section,
            title="Move me out of the list",
            created_by=self.superuser,
        )

        result = move_task(
            self._request(),
            task.id,
            TaskMoveIn(task_list_id=None, section_id=None),
        )

        self.assertIsInstance(result, TaskWorkspaceTaskOut)
        output = cast(TaskWorkspaceTaskOut, result)
        self.assertEqual(output.id, task.id)
        task.refresh_from_db()
        self.assertIsNone(task.task_list)
        self.assertIsNone(task.section)
        self.assertEqual(task.project, self.project)

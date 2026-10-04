from datetime import timedelta
from typing import cast

from django.http import HttpRequest
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.clients.models import Project
from apps.core.ownership import OwnershipType
from apps.tasks.models import Task, TaskDependency
from apps.tasks.ninja.timeline_schemas import ProjectTimelineOut
from apps.tasks.ninja.timeline_views import project_timeline
from authentication.models import User


class ProjectTimelineApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            email="timeline@example.com",
            password="test-password",
            first_name="Timeline",
            last_name="Planner",
        )
        self.project = Project.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Timeline project",
            start_date=timezone.localdate(),
        )

    def _request(self) -> HttpRequest:
        request = self.factory.get(f"/api/admin/task-timeline/projects/{self.project.id}")
        request.user = self.user
        return request

    def test_project_timeline_returns_dated_tasks_and_dependency_ids(self) -> None:
        today = timezone.localdate()
        blocking = Task.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            project=self.project,
            title="Design",
            start_date=today,
            due_date=today + timedelta(days=2),
        )
        blocked = Task.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            project=self.project,
            title="Build",
            start_date=today + timedelta(days=3),
            due_date=today + timedelta(days=6),
        )
        Task.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            project=self.project,
            title="Undated",
        )
        TaskDependency.objects.create(blocking_task=blocking, blocked_task=blocked)

        result = cast(ProjectTimelineOut, project_timeline(self._request(), self.project.id))

        self.assertEqual([task.id for task in result.tasks], [blocking.id, blocked.id])
        self.assertEqual(result.tasks[0].blocked_by_ids, [])
        self.assertEqual(result.tasks[1].blocked_by_ids, [blocking.id])

    def test_project_timeline_includes_dated_subtasks(self) -> None:
        today = timezone.localdate()
        parent = Task.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            project=self.project,
            title="Parent",
            due_date=today + timedelta(days=5),
        )
        child = Task.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            project=self.project,
            parent_task=parent,
            title="Child",
            due_date=today + timedelta(days=2),
        )

        result = cast(ProjectTimelineOut, project_timeline(self._request(), self.project.id))

        child_row = next(task for task in result.tasks if task.id == child.id)
        self.assertEqual(child_row.parent_task_id, parent.id)

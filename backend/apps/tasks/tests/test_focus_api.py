from datetime import timedelta
from typing import cast

from django.http import HttpRequest
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.core.ownership import OwnershipType
from apps.tasks.models import Task, TaskStatus
from apps.tasks.ninja.focus_schemas import TaskFocusPageOut
from apps.tasks.ninja.focus_views import task_focus
from authentication.models import User


class TaskFocusApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            email="focus@example.com",
            password="test-password",
            first_name="Focus",
            last_name="User",
        )
        self.other_user = User.objects.create_user(
            email="other-focus@example.com",
            password="test-password",
            first_name="Other",
            last_name="User",
            is_staff=True,
        )
        self.status = TaskStatus.objects.create(name="To do", color="#38bdf8", order=10)

    def _request(self) -> HttpRequest:
        request = self.factory.get("/api/admin/task-focus")
        request.user = self.user
        return request

    def _task(
        self,
        title: str,
        *,
        due_offset: int | None = None,
        assigned_to: User | None = None,
        completed: bool = False,
    ) -> Task:
        today = timezone.localdate()
        return Task.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            title=title,
            status=self.status,
            assigned_to=assigned_to,
            due_date=today + timedelta(days=due_offset) if due_offset is not None else None,
            completed_at=timezone.now() if completed else None,
        )

    def test_focus_buckets_are_scoped_to_current_staff_member(self) -> None:
        overdue = self._task("Overdue", due_offset=-1, assigned_to=self.user)
        today = self._task("Today", due_offset=0, assigned_to=self.user)
        upcoming = self._task("Upcoming", due_offset=3, assigned_to=self.user)
        no_due = self._task("No due date", assigned_to=self.user)
        self._task("Completed", due_offset=-2, assigned_to=self.user, completed=True)
        self._task("Someone else's", due_offset=0, assigned_to=self.other_user)
        self._task("Unassigned", due_offset=0)

        result = cast(TaskFocusPageOut, task_focus(self._request(), focus="my"))

        self.assertSetEqual(
            {task.id for task in result.items},
            {overdue.id, today.id, upcoming.id, no_due.id},
        )
        self.assertEqual(result.counts.my, 4)
        self.assertEqual(result.counts.today, 1)
        self.assertEqual(result.counts.upcoming, 1)
        self.assertEqual(result.counts.overdue, 1)
        self.assertEqual(result.counts.completed, 1)

    def test_due_focus_views_return_the_expected_tasks(self) -> None:
        overdue = self._task("Overdue", due_offset=-1, assigned_to=self.user)
        today = self._task("Today", due_offset=0, assigned_to=self.user)
        upcoming = self._task("Upcoming", due_offset=2, assigned_to=self.user)

        overdue_page = cast(TaskFocusPageOut, task_focus(self._request(), focus="overdue"))
        today_page = cast(TaskFocusPageOut, task_focus(self._request(), focus="today"))
        upcoming_page = cast(TaskFocusPageOut, task_focus(self._request(), focus="upcoming"))

        self.assertEqual([task.id for task in overdue_page.items], [overdue.id])
        self.assertEqual([task.id for task in today_page.items], [today.id])
        self.assertEqual([task.id for task in upcoming_page.items], [upcoming.id])

    def test_all_tasks_focus_is_explicit_and_defaults_to_open_work(self) -> None:
        mine = self._task("Mine", assigned_to=self.user)
        other = self._task("Other", assigned_to=self.other_user)
        unassigned = self._task("Unassigned")
        self._task("Completed", assigned_to=self.user, completed=True)

        result = cast(TaskFocusPageOut, task_focus(self._request(), focus="all"))

        self.assertSetEqual(
            {task.id for task in result.items},
            {mine.id, other.id, unassigned.id},
        )

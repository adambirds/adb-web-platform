from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.core.ownership import OwnershipType
from apps.tasks.models import Task, TaskDependency


class TaskDependencyTests(TestCase):
    def _task(self, title: str) -> Task:
        return Task.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            title=title,
        )

    def test_dependency_cycle_is_rejected(self) -> None:
        first = self._task("First")
        second = self._task("Second")
        third = self._task("Third")
        TaskDependency.objects.create(blocking_task=first, blocked_task=second)
        TaskDependency.objects.create(blocking_task=second, blocked_task=third)

        dependency = TaskDependency(blocking_task=third, blocked_task=first)

        with self.assertRaisesMessage(
            ValidationError,
            "Task dependencies cannot create a circular dependency.",
        ):
            dependency.full_clean()

    def test_reverse_dependency_is_rejected(self) -> None:
        first = self._task("First")
        second = self._task("Second")
        TaskDependency.objects.create(blocking_task=first, blocked_task=second)

        dependency = TaskDependency(blocking_task=second, blocked_task=first)

        with self.assertRaisesMessage(
            ValidationError,
            "Task dependencies cannot create a circular dependency.",
        ):
            dependency.full_clean()

    def test_branching_dependencies_remain_valid(self) -> None:
        first = self._task("First")
        second = self._task("Second")
        third = self._task("Third")
        TaskDependency.objects.create(blocking_task=first, blocked_task=second)

        dependency = TaskDependency(blocking_task=first, blocked_task=third)

        dependency.full_clean()

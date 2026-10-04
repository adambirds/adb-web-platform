from decimal import Decimal
from typing import Any, cast

from django.http import HttpRequest
from django.test import RequestFactory, TestCase

from apps.core.ownership import OwnershipType
from apps.tasks.models import TaskList, TaskSection
from apps.tasks.ninja.section_schemas import (
    TaskSectionMoveIn,
    TaskSectionMutationOut,
    TaskSectionUpdateIn,
)
from apps.tasks.ninja.section_views import move_task_section, update_task_section
from authentication.models import User


class TaskSectionApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            email="section-admin@example.com",
            password="test-password",
            first_name="Section",
            last_name="Admin",
        )
        self.task_list = TaskList.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Delivery",
        )
        self.first = TaskSection.objects.create(
            task_list=self.task_list,
            name="Backlog",
            sort_order=Decimal(1000),
        )
        self.second = TaskSection.objects.create(
            task_list=self.task_list,
            name="Doing",
            sort_order=Decimal(2000),
        )
        self.third = TaskSection.objects.create(
            task_list=self.task_list,
            name="Done",
            sort_order=Decimal(3000),
        )

    def _request(self, method: str = "post") -> HttpRequest:
        request = getattr(self.factory, method)("/api/admin/task-workspaces/sections")
        request.user = self.user
        return request

    def test_section_can_be_renamed_inline(self) -> None:
        result = update_task_section(
            self._request("patch"),
            self.task_list.id,
            self.second.id,
            TaskSectionUpdateIn(name="In progress"),
        )

        self.assertIsInstance(result, TaskSectionMutationOut)
        self.second.refresh_from_db()
        self.assertEqual(self.second.name, "In progress")

    def test_section_can_move_before_another_section(self) -> None:
        result = move_task_section(
            self._request(),
            self.task_list.id,
            self.third.id,
            TaskSectionMoveIn(after_section_id=self.first.id),
        )

        self.assertIsInstance(result, TaskSectionMutationOut)
        ordered = list(self.task_list.sections.values_list("id", flat=True))
        self.assertEqual(ordered, [self.third.id, self.first.id, self.second.id])

    def test_section_move_rejects_neighbour_from_another_list(self) -> None:
        other_list = TaskList.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Other",
        )
        other_section = TaskSection.objects.create(task_list=other_list, name="Other")

        result = move_task_section(
            self._request(),
            self.task_list.id,
            self.second.id,
            TaskSectionMoveIn(after_section_id=other_section.id),
        )

        self.assertIsInstance(result, tuple)
        status, payload = result
        self.assertEqual(status, 400)
        problem = cast(dict[str, Any], payload)
        self.assertEqual(problem["code"], "context_mismatch")

from typing import Any, cast

from django.http import HttpRequest
from django.test import RequestFactory, TestCase

from apps.core.models import AuditEvent
from apps.core.ownership import OwnershipType
from apps.tasks.models import Task, TaskComment
from apps.tasks.ninja.comment_schemas import TaskCommentIn, TaskCommentOut
from apps.tasks.ninja.comment_views import create_task_comment, list_task_comments
from authentication.models import User


class TaskCommentApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            email="task-comment@example.com",
            password="test-password",
            first_name="Comment",
            last_name="Author",
        )
        self.task = Task.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            title="Discuss this task",
            created_by=self.user,
        )

    def _request(self, method: str = "get") -> HttpRequest:
        request = getattr(self.factory, method)(f"/api/admin/task-comments/tasks/{self.task.id}")
        request.user = self.user
        return request

    def test_comment_can_be_added_and_is_audited_without_body(self) -> None:
        result = create_task_comment(
            self._request("post"),
            self.task.id,
            TaskCommentIn(body="  We should ship this after the dependency work.  "),
        )

        status, output = cast(tuple[int, TaskCommentOut], result)
        self.assertEqual(status, 201)
        self.assertEqual(output.body, "We should ship this after the dependency work.")
        comment = TaskComment.objects.get(id=output.id)
        self.assertEqual(comment.author, self.user)

        audit = AuditEvent.objects.get(action="tasks.comment_added")
        self.assertEqual(audit.target_id, str(self.task.id))
        self.assertEqual(audit.metadata, {"comment_id": comment.id})
        self.assertNotIn(comment.body, str(audit.metadata))

    def test_comments_are_returned_in_conversation_order(self) -> None:
        first = TaskComment.objects.create(task=self.task, author=self.user, body="First")
        second = TaskComment.objects.create(task=self.task, author=self.user, body="Second")

        result = list_task_comments(self._request(), self.task.id)

        comments = cast(list[TaskCommentOut], result)
        self.assertEqual([comment.id for comment in comments], [first.id, second.id])

    def test_blank_comment_is_rejected(self) -> None:
        result = create_task_comment(
            self._request("post"),
            self.task.id,
            TaskCommentIn(body="   "),
        )

        self.assertIsInstance(result, tuple)
        status, payload = cast(tuple[int, dict[str, Any]], result)
        self.assertEqual(status, 400)
        self.assertEqual(payload["code"], "validation_error")

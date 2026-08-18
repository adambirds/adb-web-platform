from typing import Any

from django.db.models import Q
from django.http import HttpRequest
from ninja import Router

from apps.access_control.policies import scope_clients_for_user
from apps.tasks.models import Task
from authentication.ninja.schemas import ProblemDetail

from .schemas import TaskSummaryOut

tasks_admin_router = Router(tags=["admin-tasks"])

StaffProblem = tuple[int, dict[str, Any]]


def _staff_problem(request: HttpRequest) -> StaffProblem | None:
    if not request.user.is_authenticated:
        return 401, {
            "message": "User not authenticated",
            "success": False,
            "code": "unauthenticated",
        }
    if not (request.user.is_staff or request.user.is_superuser):
        return 403, {
            "message": "You do not have permission to access this resource.",
            "success": False,
            "code": "forbidden",
        }
    return None


@tasks_admin_router.get(
    "/tasks",
    response={200: list[TaskSummaryOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_tasks(request: HttpRequest) -> list[TaskSummaryOut] | StaffProblem:
    staff_problem = _staff_problem(request)
    if staff_problem:
        return staff_problem
    if not request.user.has_perm("tasks.view_task"):
        return 403, {
            "message": "You do not have permission to view tasks.",
            "success": False,
            "code": "forbidden",
        }

    tasks = Task.objects.select_related("client", "project", "status", "task_list")
    if not request.user.is_superuser:
        clients = scope_clients_for_user(request.user)
        tasks = tasks.filter(Q(ownership_type="internal") | Q(client__in=clients))

    return [
        TaskSummaryOut(
            id=task.id,
            title=task.title,
            status=task.status.name if task.status else "Unassigned",
            priority=task.priority,
            due_date=task.due_date,
            ownership_type=task.ownership_type,
            client_name=str(task.client) if task.client else None,
            project_name=task.project.name if task.project else None,
            task_list_name=task.task_list.name if task.task_list else None,
        )
        for task in tasks.order_by("due_date", "-priority", "-created_at")
    ]

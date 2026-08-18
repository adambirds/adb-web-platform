from typing import Any

from django.db.models import Count, Q
from django.http import HttpRequest
from ninja import Router

from apps.access_control.policies import scope_clients_for_user
from apps.clients.models import Project, TimeEntry
from authentication.ninja.schemas import ProblemDetail

from .schemas import ClientSummaryOut, ProjectSummaryOut, TimeEntrySummaryOut

clients_admin_router = Router(tags=["admin-clients"])

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


@clients_admin_router.get(
    "/clients",
    response={200: list[ClientSummaryOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_clients(request: HttpRequest) -> list[ClientSummaryOut] | StaffProblem:
    staff_problem = _staff_problem(request)
    if staff_problem:
        return staff_problem
    if not request.user.has_perm("clients.view_client"):
        return 403, {
            "message": "You do not have permission to view clients.",
            "success": False,
            "code": "forbidden",
        }

    clients = scope_clients_for_user(request.user).annotate(
        contact_count=Count("contacts", distinct=True),
        project_count=Count("projects", distinct=True),
    )

    return [
        ClientSummaryOut(
            id=client.id,
            name=client.name,
            company=client.company,
            email=client.email,
            status=client.status,
            contact_count=client.contact_count,
            project_count=client.project_count,
        )
        for client in clients.order_by("company", "name")
    ]


@clients_admin_router.get(
    "/projects",
    response={200: list[ProjectSummaryOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_projects(request: HttpRequest) -> list[ProjectSummaryOut] | StaffProblem:
    staff_problem = _staff_problem(request)
    if staff_problem:
        return staff_problem
    if not request.user.has_perm("clients.view_project"):
        return 403, {
            "message": "You do not have permission to view projects.",
            "success": False,
            "code": "forbidden",
        }

    projects = Project.objects.select_related("client")
    if not request.user.is_superuser:
        clients = scope_clients_for_user(request.user)
        projects = projects.filter(Q(ownership_type="internal") | Q(client__in=clients))

    return [
        ProjectSummaryOut(
            id=project.id,
            name=project.name,
            status=project.status,
            ownership_type=project.ownership_type,
            client_id=project.client_id,
            client_name=str(project.client) if project.client else None,
            start_date=project.start_date,
            end_date=project.end_date,
            budget=project.budget,
        )
        for project in projects.order_by("-start_date", "name")
    ]


@clients_admin_router.get(
    "/time-entries",
    response={200: list[TimeEntrySummaryOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_time_entries(request: HttpRequest) -> list[TimeEntrySummaryOut] | StaffProblem:
    staff_problem = _staff_problem(request)
    if staff_problem:
        return staff_problem
    if not request.user.has_perm("clients.view_timeentry"):
        return 403, {
            "message": "You do not have permission to view time entries.",
            "success": False,
            "code": "forbidden",
        }

    entries = TimeEntry.objects.select_related("client", "project", "user")
    if not request.user.is_superuser:
        clients = scope_clients_for_user(request.user)
        entries = entries.filter(Q(ownership_type="internal") | Q(client__in=clients))

    rows: list[TimeEntrySummaryOut] = []
    for entry in entries.order_by("-date", "-created_at"):
        user_name = None
        if entry.user:
            user_name = (
                f"{entry.user.first_name} {entry.user.last_name}".strip() or entry.user.email
            )
        rows.append(
            TimeEntrySummaryOut(
                id=entry.id,
                date=entry.date,
                duration_hours=entry.duration_hours,
                description=entry.description,
                billable=entry.billable,
                ownership_type=entry.ownership_type,
                client_name=str(entry.client) if entry.client else None,
                project_name=entry.project.name if entry.project else None,
                user_name=user_name,
            )
        )
    return rows

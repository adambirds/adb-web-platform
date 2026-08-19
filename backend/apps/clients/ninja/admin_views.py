from typing import Any

from django.db.models import Count, Q
from django.http import HttpRequest
from ninja import Router

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.access_control.policies import scope_clients_for_user
from apps.clients.models import Client, Project, TimeEntry
from authentication.ninja.schemas import ProblemDetail

from .schemas import (
    ClientContactOut,
    ClientDetailOut,
    ClientIn,
    ClientProjectOut,
    ClientSummaryOut,
    ProjectSummaryOut,
    TimeEntrySummaryOut,
)

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


def _permission_problem(request: HttpRequest, permission: str) -> StaffProblem | None:
    staff_problem = _staff_problem(request)
    if staff_problem:
        return staff_problem
    if not request.user.has_perm(permission):
        return 403, {
            "message": "You do not have permission to access this resource.",
            "success": False,
            "code": "forbidden",
        }
    return None


def _build_client_detail(request: HttpRequest, client: Client) -> ClientDetailOut:
    contacts = []
    if request.user.has_perm("clients.view_clientcontact"):
        contacts = [
            ClientContactOut(
                id=contact.id,
                name=contact.name,
                email=contact.email,
                phone=contact.phone,
                role=contact.role,
                is_active=contact.is_active,
                is_primary=contact.is_primary,
                is_billing=contact.is_billing,
                is_technical=contact.is_technical,
            )
            for contact in client.contacts.all()
        ]

    projects = []
    if request.user.has_perm("clients.view_project"):
        projects = [
            ClientProjectOut(
                id=project.id,
                name=project.name,
                status=project.status,
                start_date=project.start_date,
                end_date=project.end_date,
                budget=project.budget,
            )
            for project in client.projects.all()
        ]

    return ClientDetailOut(
        id=client.id,
        name=client.name,
        company=client.company,
        email=client.email,
        phone=client.phone,
        address=client.address,
        city=client.city,
        state=client.state,
        country=client.country,
        postal_code=client.postal_code,
        status=client.status,
        notes=client.notes,
        contacts=contacts,
        projects=projects,
    )


def _apply_client_payload(client: Client, payload: ClientIn) -> None:
    client.name = payload.name.strip()
    client.company = payload.company.strip()
    client.email = str(payload.email).strip().lower()
    client.phone = payload.phone.strip()
    client.address = payload.address.strip()
    client.city = payload.city.strip()
    client.state = payload.state.strip()
    client.country = payload.country.strip()
    client.postal_code = payload.postal_code.strip()
    client.status = payload.status
    client.notes = payload.notes.strip()


def _grant_created_client_to_user(request: HttpRequest, client: Client) -> None:
    if request.user.is_superuser:
        return

    profile, _ = StaffAccessProfile.objects.get_or_create(user=request.user)
    if profile.all_clients:
        return

    ClientAccessGrant.objects.get_or_create(
        profile=profile,
        client=client,
        defaults={"granted_by": request.user},
    )


@clients_admin_router.get(
    "/clients",
    response={200: list[ClientSummaryOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_clients(request: HttpRequest) -> list[ClientSummaryOut] | StaffProblem:
    problem = _permission_problem(request, "clients.view_client")
    if problem:
        return problem

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


@clients_admin_router.post(
    "/clients",
    response={201: ClientDetailOut, 401: ProblemDetail, 403: ProblemDetail},
)
def create_client(request: HttpRequest, payload: ClientIn) -> tuple[int, ClientDetailOut] | StaffProblem:
    problem = _permission_problem(request, "clients.add_client")
    if problem:
        return problem

    client = Client()
    _apply_client_payload(client, payload)
    client.full_clean()
    client.save()
    _grant_created_client_to_user(request, client)

    return 201, _build_client_detail(request, client)


@clients_admin_router.get(
    "/clients/{client_id}",
    response={200: ClientDetailOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def get_client(request: HttpRequest, client_id: int) -> ClientDetailOut | StaffProblem:
    problem = _permission_problem(request, "clients.view_client")
    if problem:
        return problem

    client = (
        scope_clients_for_user(request.user)
        .prefetch_related("contacts", "projects")
        .filter(id=client_id)
        .first()
    )
    if client is None:
        return 404, {
            "message": "Client not found or outside your access scope.",
            "success": False,
            "code": "not_found",
        }

    return _build_client_detail(request, client)


@clients_admin_router.put(
    "/clients/{client_id}",
    response={200: ClientDetailOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def update_client(
    request: HttpRequest,
    client_id: int,
    payload: ClientIn,
) -> ClientDetailOut | StaffProblem:
    problem = _permission_problem(request, "clients.change_client")
    if problem:
        return problem

    client = (
        scope_clients_for_user(request.user)
        .prefetch_related("contacts", "projects")
        .filter(id=client_id)
        .first()
    )
    if client is None:
        return 404, {
            "message": "Client not found or outside your access scope.",
            "success": False,
            "code": "not_found",
        }

    _apply_client_payload(client, payload)
    client.full_clean()
    client.save()
    return _build_client_detail(request, client)


@clients_admin_router.get(
    "/projects",
    response={200: list[ProjectSummaryOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_projects(request: HttpRequest) -> list[ProjectSummaryOut] | StaffProblem:
    problem = _permission_problem(request, "clients.view_project")
    if problem:
        return problem

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
    problem = _permission_problem(request, "clients.view_timeentry")
    if problem:
        return problem

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

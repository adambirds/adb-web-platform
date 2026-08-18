from datetime import timedelta
from typing import Any

from django.db.models import Sum
from django.http import HttpRequest
from django.utils import timezone
from ninja import Router

from apps.access_control.policies import scope_clients_for_user
from apps.clients.models import Project, TimeEntry
from apps.core.models import AuditEvent, Brand
from apps.crm.models import Lead
from apps.infrastructure.models import Domain, Licence
from apps.tasks.models import Task
from authentication.ninja.schemas import ProblemDetail

from .schemas import (
    BrandOut,
    DashboardActivityOut,
    DashboardLeadOut,
    DashboardSummaryOut,
    DashboardTaskOut,
)

core_admin_router = Router(tags=["admin-core"])

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


@core_admin_router.get(
    "/brands",
    response={200: list[BrandOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_brands(request: HttpRequest) -> list[BrandOut] | StaffProblem:
    staff_problem = _staff_problem(request)
    if staff_problem:
        return staff_problem
    if not request.user.has_perm("core.view_brand"):
        return 403, {
            "message": "You do not have permission to view brands.",
            "success": False,
            "code": "forbidden",
        }

    return [
        BrandOut(
            id=brand.id,
            name=brand.name,
            slug=brand.slug,
            domain=brand.domain,
            is_active=brand.is_active,
        )
        for brand in Brand.objects.order_by("name")
    ]


@core_admin_router.get(
    "/dashboard",
    response={200: DashboardSummaryOut, 401: ProblemDetail, 403: ProblemDetail},
)
def dashboard_summary(request: HttpRequest) -> DashboardSummaryOut | StaffProblem:
    staff_problem = _staff_problem(request)
    if staff_problem:
        return staff_problem

    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    warning_date = today + timedelta(days=45)

    clients = scope_clients_for_user(request.user)
    projects = Project.objects.filter(client__in=clients)
    time_entries = TimeEntry.objects.filter(client__in=clients)

    active_clients = (
        clients.filter(status="active").count()
        if request.user.has_perm("clients.view_client")
        else 0
    )
    active_projects = (
        projects.filter(status="active").count()
        if request.user.has_perm("clients.view_project")
        else 0
    )
    hours_this_week = 0.0
    if request.user.has_perm("clients.view_timeentry"):
        hours = time_entries.filter(date__gte=week_start).aggregate(total=Sum("duration_hours"))[
            "total"
        ]
        hours_this_week = float(hours or 0)

    leads = Lead.objects.select_related("status", "brand")
    if request.user.has_perm("crm.view_lead"):
        open_leads = leads.exclude(status__name__in=["Won", "Lost"]).count()
        recent_lead_rows = leads.order_by("-created_at")[:5]
        recent_leads = [
            DashboardLeadOut(
                id=lead.id,
                name=lead.name,
                company=lead.company,
                status=lead.status.name if lead.status else "Unassigned",
                brand=lead.brand.name if lead.brand else "Unassigned",
                created_at=lead.created_at,
            )
            for lead in recent_lead_rows
        ]
    else:
        open_leads = 0
        recent_leads = []

    tasks = Task.objects.select_related("status")
    if request.user.has_perm("tasks.view_task"):
        open_task_queryset = tasks.exclude(status__name="Done")
        open_tasks = open_task_queryset.count()
        overdue_tasks = open_task_queryset.filter(due_date__lt=today).count()
        task_rows = open_task_queryset.filter(due_date__isnull=False).order_by(
            "due_date",
            "-priority",
        )[:6]
        upcoming_tasks = [
            DashboardTaskOut(
                id=task.id,
                title=task.title,
                status=task.status.name if task.status else "Unassigned",
                priority=task.priority,
                due_date=task.due_date,
            )
            for task in task_rows
        ]
    else:
        open_tasks = 0
        overdue_tasks = 0
        upcoming_tasks = []

    expiring_domains = 0
    renewing_licences = 0
    if request.user.has_perm("infrastructure.view_domain"):
        expiring_domains = Domain.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=warning_date,
        ).count()
    if request.user.has_perm("infrastructure.view_licence"):
        renewing_licences = Licence.objects.filter(
            renewal_date__gte=today,
            renewal_date__lte=warning_date,
        ).count()

    recent_activity = []
    if request.user.has_perm("core.view_auditevent"):
        recent_activity = [
            DashboardActivityOut(
                id=event.id,
                action=event.action,
                target_label=event.target_label,
                created_at=event.created_at,
            )
            for event in AuditEvent.objects.order_by("-created_at")[:8]
        ]

    return DashboardSummaryOut(
        active_clients=active_clients,
        active_projects=active_projects,
        open_leads=open_leads,
        open_tasks=open_tasks,
        overdue_tasks=overdue_tasks,
        hours_this_week=hours_this_week,
        expiring_domains=expiring_domains,
        renewing_licences=renewing_licences,
        recent_leads=recent_leads,
        upcoming_tasks=upcoming_tasks,
        recent_activity=recent_activity,
    )

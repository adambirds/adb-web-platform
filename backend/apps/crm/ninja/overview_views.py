import math
from datetime import timedelta
from typing import Any
from uuid import UUID

from django.db.models import Q, QuerySet
from django.http import HttpRequest
from django.utils import timezone
from ninja import Router

from apps.crm.models import Lead, LeadStatus
from authentication.ninja.schemas import ProblemDetail

from .overview_schemas import LeadOverviewItemOut, LeadOverviewOut, LeadOverviewStatsOut

lead_overview_router = Router(tags=["admin-lead-overview"])
StaffProblem = tuple[int, dict[str, Any]]
LEAD_VIEWS = {"my", "unassigned", "active", "won", "lost", "all"}


def _permission_problem(request: HttpRequest) -> StaffProblem | None:
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
    if not request.user.has_perm("crm.view_lead"):
        return 403, {
            "message": "You do not have permission to view leads.",
            "success": False,
            "code": "forbidden",
        }
    return None


def _lead_queryset() -> QuerySet[Lead]:
    return Lead.objects.select_related("brand", "status", "source", "assigned_to")


def _active_leads() -> QuerySet[Lead]:
    return (
        _lead_queryset()
        .filter(converted_at__isnull=True)
        .filter(Q(status__isnull=True) | Q(status__outcome=LeadStatus.Outcome.OPEN))
    )


def _user_label(user: Any | None) -> str | None:
    if user is None:
        return None
    return user.get_full_name().strip() or user.email


@lead_overview_router.get(
    "/lead-overview",
    response={200: LeadOverviewOut, 401: ProblemDetail, 403: ProblemDetail},
)
def lead_overview(
    request: HttpRequest,
    view: str = "my",
    page: int = 1,
    page_size: int = 25,
    status_id: int | None = None,
    source_id: int | None = None,
    brand_id: int | None = None,
    assigned_to_id: UUID | None = None,
    search: str | None = None,
) -> LeadOverviewOut | StaffProblem:
    problem = _permission_problem(request)
    if problem:
        return problem

    selected_view = view if view in LEAD_VIEWS else "my"
    active = _active_leads()
    cutoff = timezone.now() - timedelta(days=30)
    stats = LeadOverviewStatsOut(
        active=active.count(),
        mine=active.filter(assigned_to_id=request.user.id).count(),
        unassigned=active.filter(assigned_to__isnull=True).count(),
        new_last_30_days=active.filter(created_at__gte=cutoff).count(),
    )

    if selected_view == "my":
        leads = active.filter(assigned_to_id=request.user.id)
    elif selected_view == "unassigned":
        leads = active.filter(assigned_to__isnull=True)
    elif selected_view == "active":
        leads = active
    elif selected_view == "won":
        leads = _lead_queryset().filter(status__outcome=LeadStatus.Outcome.WON)
    elif selected_view == "lost":
        leads = _lead_queryset().filter(status__outcome=LeadStatus.Outcome.LOST)
    else:
        leads = _lead_queryset()

    if status_id is not None:
        leads = leads.filter(status_id=status_id)
    if source_id is not None:
        leads = leads.filter(source_id=source_id)
    if brand_id is not None:
        leads = leads.filter(brand_id=brand_id)
    if assigned_to_id is not None:
        leads = leads.filter(assigned_to_id=assigned_to_id)
    if search:
        term = search.strip()
        if term:
            leads = leads.filter(
                Q(name__icontains=term)
                | Q(company__icontains=term)
                | Q(email__icontains=term)
                | Q(message__icontains=term)
            )

    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    total = leads.count()
    total_pages = math.ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    if selected_view in {"my", "unassigned", "active"}:
        leads = leads.order_by("status__order", "-created_at")
    else:
        leads = leads.order_by("-updated_at", "-created_at")
    rows = leads[start : start + page_size]

    return LeadOverviewOut(
        items=[
            LeadOverviewItemOut(
                id=lead.id,
                name=lead.name,
                company=lead.company,
                email=lead.email,
                status=lead.status.name if lead.status else "No sales stage",
                outcome=lead.status.outcome if lead.status else LeadStatus.Outcome.OPEN,
                source=lead.source.name if lead.source else "Unknown",
                brand=lead.brand.name if lead.brand else "Unassigned",
                assigned_to_name=_user_label(lead.assigned_to),
                converted_at=lead.converted_at,
                created_at=lead.created_at,
            )
            for lead in rows
        ],
        stats=stats,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )

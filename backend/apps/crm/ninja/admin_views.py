from typing import Any

from django.http import HttpRequest
from ninja import Router

from apps.crm.models import Lead
from authentication.ninja.schemas import ProblemDetail

from .schemas import LeadSummaryOut

crm_admin_router = Router(tags=["admin-crm"])

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


@crm_admin_router.get(
    "/leads",
    response={200: list[LeadSummaryOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_leads(request: HttpRequest) -> list[LeadSummaryOut] | StaffProblem:
    staff_problem = _staff_problem(request)
    if staff_problem:
        return staff_problem
    if not request.user.has_perm("crm.view_lead"):
        return 403, {
            "message": "You do not have permission to view leads.",
            "success": False,
            "code": "forbidden",
        }

    leads = Lead.objects.select_related("brand", "source", "status").order_by("-created_at")
    return [
        LeadSummaryOut(
            id=lead.id,
            name=lead.name,
            company=lead.company,
            email=lead.email,
            status=lead.status.name if lead.status else "Unassigned",
            source=lead.source.name if lead.source else "Unknown",
            brand=lead.brand.name if lead.brand else "Unassigned",
            created_at=lead.created_at,
        )
        for lead in leads
    ]

from django.http import HttpRequest
from ninja import Router

from apps.infrastructure.summary import inventory_summary
from authentication.ninja.schemas import ProblemDetail

from .resource_views import StaffProblem, _staff_problem
from .schemas import InfrastructureSummaryOut

infrastructure_admin_router = Router(tags=["admin-infrastructure"])


@infrastructure_admin_router.get(
    "/infrastructure/summary",
    response={200: InfrastructureSummaryOut, 401: ProblemDetail, 403: ProblemDetail},
)
def infrastructure_summary(request: HttpRequest) -> InfrastructureSummaryOut | StaffProblem:
    staff_problem = _staff_problem(request)
    if staff_problem:
        return staff_problem

    return InfrastructureSummaryOut(**inventory_summary(request))

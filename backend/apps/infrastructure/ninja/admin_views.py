from datetime import timedelta
from typing import Any

from django.http import HttpRequest
from django.utils import timezone
from ninja import Router

from apps.infrastructure.models import (
    API,
    Application,
    Bot,
    Database,
    Domain,
    EmailSystem,
    Licence,
    MobileApp,
    Server,
    SSLCertificate,
    Website,
)
from authentication.ninja.schemas import ProblemDetail

from .schemas import InfrastructureSummaryOut

infrastructure_admin_router = Router(tags=["admin-infrastructure"])

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


def _count_if_permitted(request: HttpRequest, permission: str, model: Any) -> int:
    if not request.user.has_perm(permission):
        return 0
    return model.objects.count()


@infrastructure_admin_router.get(
    "/infrastructure/summary",
    response={
        200: InfrastructureSummaryOut,
        401: ProblemDetail,
        403: ProblemDetail,
    },
)
def infrastructure_summary(
    request: HttpRequest,
) -> InfrastructureSummaryOut | StaffProblem:
    staff_problem = _staff_problem(request)
    if staff_problem:
        return staff_problem

    today = timezone.localdate()
    warning_date = today + timedelta(days=45)

    expiring_domain_count = 0
    if request.user.has_perm("infrastructure.view_domain"):
        expiring_domain_count = Domain.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=warning_date,
        ).count()

    expiring_certificate_count = 0
    if request.user.has_perm("infrastructure.view_sslcertificate"):
        expiring_certificate_count = SSLCertificate.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=warning_date,
        ).count()

    renewing_licence_count = 0
    if request.user.has_perm("infrastructure.view_licence"):
        renewing_licence_count = Licence.objects.filter(
            renewal_date__gte=today,
            renewal_date__lte=warning_date,
        ).count()

    return InfrastructureSummaryOut(
        server_count=_count_if_permitted(
            request,
            "infrastructure.view_server",
            Server,
        ),
        database_count=_count_if_permitted(
            request,
            "infrastructure.view_database",
            Database,
        ),
        website_count=_count_if_permitted(
            request,
            "infrastructure.view_website",
            Website,
        ),
        domain_count=_count_if_permitted(
            request,
            "infrastructure.view_domain",
            Domain,
        ),
        expiring_domain_count=expiring_domain_count,
        ssl_certificate_count=_count_if_permitted(
            request,
            "infrastructure.view_sslcertificate",
            SSLCertificate,
        ),
        expiring_certificate_count=expiring_certificate_count,
        licence_count=_count_if_permitted(
            request,
            "infrastructure.view_licence",
            Licence,
        ),
        renewing_licence_count=renewing_licence_count,
        application_count=_count_if_permitted(
            request,
            "infrastructure.view_application",
            Application,
        ),
        mobile_app_count=_count_if_permitted(
            request,
            "infrastructure.view_mobileapp",
            MobileApp,
        ),
        api_count=_count_if_permitted(
            request,
            "infrastructure.view_api",
            API,
        ),
        bot_count=_count_if_permitted(
            request,
            "infrastructure.view_bot",
            Bot,
        ),
        email_system_count=_count_if_permitted(
            request,
            "infrastructure.view_emailsystem",
            EmailSystem,
        ),
    )

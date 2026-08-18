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

from .schemas import (
    DatabaseSummaryOut,
    DomainSummaryOut,
    InfrastructureSummaryOut,
    LicenceSummaryOut,
    ServerSummaryOut,
    WebsiteSummaryOut,
)

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


def _count_if_permitted(request: HttpRequest, permission: str, model: Any) -> int:
    if not request.user.has_perm(permission):
        return 0
    return model.objects.count()


@infrastructure_admin_router.get(
    "/infrastructure/summary",
    response={200: InfrastructureSummaryOut, 401: ProblemDetail, 403: ProblemDetail},
)
def infrastructure_summary(request: HttpRequest) -> InfrastructureSummaryOut | StaffProblem:
    staff_problem = _staff_problem(request)
    if staff_problem:
        return staff_problem

    today = timezone.localdate()
    warning_date = today + timedelta(days=45)

    expiring_domain_count = 0
    if request.user.has_perm("infrastructure.view_domain"):
        expiring_domain_count = Domain.objects.filter(
            expiry_date__gte=today, expiry_date__lte=warning_date
        ).count()

    expiring_certificate_count = 0
    if request.user.has_perm("infrastructure.view_sslcertificate"):
        expiring_certificate_count = SSLCertificate.objects.filter(
            expiry_date__gte=today, expiry_date__lte=warning_date
        ).count()

    renewing_licence_count = 0
    if request.user.has_perm("infrastructure.view_licence"):
        renewing_licence_count = Licence.objects.filter(
            renewal_date__gte=today, renewal_date__lte=warning_date
        ).count()

    return InfrastructureSummaryOut(
        server_count=_count_if_permitted(request, "infrastructure.view_server", Server),
        database_count=_count_if_permitted(request, "infrastructure.view_database", Database),
        website_count=_count_if_permitted(request, "infrastructure.view_website", Website),
        domain_count=_count_if_permitted(request, "infrastructure.view_domain", Domain),
        expiring_domain_count=expiring_domain_count,
        ssl_certificate_count=_count_if_permitted(
            request, "infrastructure.view_sslcertificate", SSLCertificate
        ),
        expiring_certificate_count=expiring_certificate_count,
        licence_count=_count_if_permitted(request, "infrastructure.view_licence", Licence),
        renewing_licence_count=renewing_licence_count,
        application_count=_count_if_permitted(
            request, "infrastructure.view_application", Application
        ),
        mobile_app_count=_count_if_permitted(request, "infrastructure.view_mobileapp", MobileApp),
        api_count=_count_if_permitted(request, "infrastructure.view_api", API),
        bot_count=_count_if_permitted(request, "infrastructure.view_bot", Bot),
        email_system_count=_count_if_permitted(
            request, "infrastructure.view_emailsystem", EmailSystem
        ),
    )


@infrastructure_admin_router.get(
    "/infrastructure/servers",
    response={200: list[ServerSummaryOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_servers(request: HttpRequest) -> list[ServerSummaryOut] | StaffProblem:
    problem = _permission_problem(request, "infrastructure.view_server")
    if problem:
        return problem
    return [
        ServerSummaryOut(
            id=server.id,
            hostname=server.hostname,
            role=server.role,
            provider=server.provider,
            region=server.region,
            os=server.os,
            public_ip=str(server.public_ip) if server.public_ip else None,
            ram_gb=server.ram_gb,
        )
        for server in Server.objects.all()
    ]


@infrastructure_admin_router.get(
    "/infrastructure/databases",
    response={200: list[DatabaseSummaryOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_databases(request: HttpRequest) -> list[DatabaseSummaryOut] | StaffProblem:
    problem = _permission_problem(request, "infrastructure.view_database")
    if problem:
        return problem
    return [
        DatabaseSummaryOut(
            id=database.id,
            name=database.name,
            db_type=database.db_type,
            provider=database.provider,
            version=database.version,
            server_hostname=database.server.hostname if database.server else None,
        )
        for database in Database.objects.select_related("server")
    ]


@infrastructure_admin_router.get(
    "/infrastructure/websites",
    response={200: list[WebsiteSummaryOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_websites(request: HttpRequest) -> list[WebsiteSummaryOut] | StaffProblem:
    problem = _permission_problem(request, "infrastructure.view_website")
    if problem:
        return problem
    return [
        WebsiteSummaryOut(
            id=website.id,
            name=website.name,
            primary_url=website.primary_url,
            environment_type=website.environment_type,
            database_name=website.database.name if website.database else None,
            server_count=website.servers.count(),
            domain_count=website.domains.count(),
        )
        for website in Website.objects.select_related("database").prefetch_related(
            "servers", "domains"
        )
    ]


@infrastructure_admin_router.get(
    "/infrastructure/domains",
    response={200: list[DomainSummaryOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_domains(request: HttpRequest) -> list[DomainSummaryOut] | StaffProblem:
    problem = _permission_problem(request, "infrastructure.view_domain")
    if problem:
        return problem
    return [
        DomainSummaryOut(
            id=domain.id,
            domain_name=domain.domain_name,
            registrar=domain.registrar,
            expiry_date=domain.expiry_date,
            auto_renew=domain.auto_renew,
            website_count=domain.websites.count(),
        )
        for domain in Domain.objects.prefetch_related("websites")
    ]


@infrastructure_admin_router.get(
    "/infrastructure/licences",
    response={200: list[LicenceSummaryOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_licences(request: HttpRequest) -> list[LicenceSummaryOut] | StaffProblem:
    problem = _permission_problem(request, "infrastructure.view_licence")
    if problem:
        return problem
    return [
        LicenceSummaryOut(
            id=licence.id,
            name=licence.name,
            licence_type=licence.licence_type,
            vendor=licence.vendor,
            renewal_date=licence.renewal_date,
            renewal_cost=licence.renewal_cost,
            auto_renew=licence.auto_renew,
            website_count=licence.websites.count(),
        )
        for licence in Licence.objects.prefetch_related("websites")
    ]

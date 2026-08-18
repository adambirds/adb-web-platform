from datetime import date
from decimal import Decimal
from typing import Any

from django.http import HttpRequest
from ninja import Router, Schema

from apps.infrastructure.models import (
    API,
    Application,
    Bot,
    EmailSystem,
    MobileApp,
    SSLCertificate,
    WebsiteTechStack,
)
from authentication.ninja.schemas import ProblemDetail

infrastructure_extended_router = Router(tags=["admin-infrastructure"])

StaffProblem = tuple[int, dict[str, Any]]


class SSLCertificateOut(Schema):
    id: int
    domain: str
    provider: str
    cert_type: str
    expiry_date: date


class ApplicationOut(Schema):
    id: int
    name: str
    app_type: str
    status: str
    website_count: int
    server_count: int
    database_count: int


class MobileAppOut(Schema):
    id: int
    name: str
    platform: str
    framework: str
    current_version: str
    release_status: str
    bundle_id: str


class APIOut(Schema):
    id: int
    name: str
    api_type: str
    base_url: str
    visibility: str
    authentication: str


class BotOut(Schema):
    id: int
    name: str
    platform: str
    bot_type: str
    runtime: str
    hosting_location: str


class EmailSystemOut(Schema):
    id: int
    provider: str
    domains: str
    spf_status: str
    dkim_status: str
    dmarc_status: str


class WebsiteTechStackOut(Schema):
    id: int
    website: str
    technology: str
    category: str
    version: str


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
            "message": "You do not have permission to view this infrastructure register.",
            "success": False,
            "code": "forbidden",
        }
    return None


@infrastructure_extended_router.get(
    "/infrastructure/ssl-certificates",
    response={200: list[SSLCertificateOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_ssl_certificates(
    request: HttpRequest,
) -> list[SSLCertificateOut] | StaffProblem:
    problem = _permission_problem(request, "infrastructure.view_sslcertificate")
    if problem:
        return problem
    return [
        SSLCertificateOut(
            id=certificate.id,
            domain=certificate.domain.domain_name,
            provider=certificate.get_provider_display(),
            cert_type=certificate.cert_type,
            expiry_date=certificate.expiry_date,
        )
        for certificate in SSLCertificate.objects.select_related("domain").order_by(
            "expiry_date"
        )
    ]


@infrastructure_extended_router.get(
    "/infrastructure/applications",
    response={200: list[ApplicationOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_applications(request: HttpRequest) -> list[ApplicationOut] | StaffProblem:
    problem = _permission_problem(request, "infrastructure.view_application")
    if problem:
        return problem
    return [
        ApplicationOut(
            id=application.id,
            name=application.name,
            app_type=application.get_app_type_display(),
            status=application.get_status_display(),
            website_count=application.websites.count(),
            server_count=application.servers.count(),
            database_count=application.databases.count(),
        )
        for application in Application.objects.prefetch_related(
            "websites",
            "servers",
            "databases",
        ).order_by("name")
    ]


@infrastructure_extended_router.get(
    "/infrastructure/mobile-apps",
    response={200: list[MobileAppOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_mobile_apps(request: HttpRequest) -> list[MobileAppOut] | StaffProblem:
    problem = _permission_problem(request, "infrastructure.view_mobileapp")
    if problem:
        return problem
    return [
        MobileAppOut(
            id=app.id,
            name=app.name,
            platform=app.get_platform_display(),
            framework=app.get_framework_display(),
            current_version=app.current_version,
            release_status=app.get_release_status_display(),
            bundle_id=app.bundle_id,
        )
        for app in MobileApp.objects.order_by("name")
    ]


@infrastructure_extended_router.get(
    "/infrastructure/apis",
    response={200: list[APIOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_apis(request: HttpRequest) -> list[APIOut] | StaffProblem:
    problem = _permission_problem(request, "infrastructure.view_api")
    if problem:
        return problem
    return [
        APIOut(
            id=api.id,
            name=api.name,
            api_type=api.get_api_type_display(),
            base_url=api.base_url,
            visibility=api.get_visibility_display(),
            authentication=api.get_authentication_display(),
        )
        for api in API.objects.order_by("name")
    ]


@infrastructure_extended_router.get(
    "/infrastructure/bots",
    response={200: list[BotOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_bots(request: HttpRequest) -> list[BotOut] | StaffProblem:
    problem = _permission_problem(request, "infrastructure.view_bot")
    if problem:
        return problem
    return [
        BotOut(
            id=bot.id,
            name=bot.name,
            platform=bot.get_platform_display(),
            bot_type=bot.get_bot_type_display(),
            runtime=bot.get_runtime_display(),
            hosting_location=bot.hosting_location,
        )
        for bot in Bot.objects.order_by("name")
    ]


@infrastructure_extended_router.get(
    "/infrastructure/email-systems",
    response={200: list[EmailSystemOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_email_systems(request: HttpRequest) -> list[EmailSystemOut] | StaffProblem:
    problem = _permission_problem(request, "infrastructure.view_emailsystem")
    if problem:
        return problem
    return [
        EmailSystemOut(
            id=email_system.id,
            provider=email_system.get_provider_display(),
            domains=email_system.domains,
            spf_status=email_system.spf_status,
            dkim_status=email_system.dkim_status,
            dmarc_status=email_system.dmarc_status,
        )
        for email_system in EmailSystem.objects.order_by("provider")
    ]


@infrastructure_extended_router.get(
    "/infrastructure/tech-stack",
    response={200: list[WebsiteTechStackOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_tech_stack(request: HttpRequest) -> list[WebsiteTechStackOut] | StaffProblem:
    problem = _permission_problem(request, "infrastructure.view_websitetechstack")
    if problem:
        return problem
    return [
        WebsiteTechStackOut(
            id=stack.id,
            website=stack.website.name,
            technology=stack.technology,
            category=stack.get_category_display(),
            version=stack.version,
        )
        for stack in WebsiteTechStack.objects.select_related("website").order_by(
            "website__name",
            "category",
            "technology",
        )
    ]

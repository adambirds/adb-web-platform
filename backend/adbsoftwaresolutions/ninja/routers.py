import logging

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from ninja import NinjaAPI, Router
from ninja.errors import HttpError
from pydantic import ValidationError

from apps.access_control.ninja.views import staff_access_router
from apps.analytics.api import router as analytics_router
from apps.analytics.google import ProviderError
from apps.clients.ninja.admin_views import clients_admin_router
from apps.clients.ninja.command_centre_views import client_command_centre_router
from apps.clients.ninja.overview_views import client_overview_router
from apps.clients.ninja.time_report_views import time_report_router
from apps.clients.ninja.time_views import time_tracking_router
from apps.core.celery_dashboard.views import celery_dashboard_router
from apps.core.ninja.admin_views import core_admin_router
from apps.core.ninja.dashboard_views import dashboard_router
from apps.core.ninja.operational_views import operational_polish_router
from apps.core.ninja.resource_views import resource_admin_router
from apps.core.ninja.search_views import operational_search_router
from apps.credentials.ninja.lifecycle_views import credential_lifecycle_router
from apps.credentials.ninja.views import credential_router
from apps.crm.ninja.admin_views import crm_admin_router
from apps.crm.ninja.email_views import lead_email_router
from apps.crm.ninja.overview_views import lead_overview_router
from apps.crm.ninja.retention_views import retention_router
from apps.github_integration.ninja.views import github_router
from apps.infrastructure.ninja.admin_views import infrastructure_admin_router
from apps.infrastructure.ninja.application_repository_views import application_repository_router
from apps.infrastructure.ninja.catalogue_views import catalogue_router
from apps.infrastructure.ninja.data_application_views import data_application_specialist_router
from apps.infrastructure.ninja.operational_nested_views import operational_nested_router
from apps.infrastructure.ninja.operational_views import operational_specialist_router
from apps.infrastructure.ninja.resource_views import infrastructure_resource_router
from apps.infrastructure.ninja.specialist_edit_views import infrastructure_specialist_edit_router
from apps.infrastructure.ninja.specialist_views import infrastructure_specialist_router
from apps.infrastructure.ninja.tag_views import tag_router
from apps.infrastructure.ninja.technology_views import technology_router
from apps.infrastructure.ninja.topology_views import topology_router
from apps.infrastructure.ninja.web_domain_nested_views import web_domain_nested_router
from apps.infrastructure.ninja.web_domain_views import web_domain_specialist_router
from apps.knowledge_base.ninja.attachment_views import knowledge_attachment_router
from apps.knowledge_base.ninja.views import knowledge_base_router
from apps.monitoring.ninja.views import monitoring_router
from apps.tasks.ninja.admin_views import tasks_admin_router
from apps.tasks.ninja.calendar_views import calendar_router
from apps.tasks.ninja.comment_views import comment_router
from apps.tasks.ninja.focus_views import focus_router
from apps.tasks.ninja.quick_views import quick_router
from apps.tasks.ninja.relations_views import relations_router
from apps.tasks.ninja.section_views import section_router
from apps.tasks.ninja.timeline_views import timeline_router
from apps.tasks.ninja.workspace_views import workspace_router
from apps.ticketing.ninja.admin_views import ticketing_admin_router
from apps.ticketing.ninja.attachment_views import attachment_router
from apps.ticketing.ninja.focus_views import ticket_focus_router
from apps.ticketing.ninja.operations_views import operations_router
from apps.ticketing.ninja.settings_views import ticketing_settings_router
from apps.ticketing.ninja.sla_views import sla_router
from apps.ticketing.ninja.vendor_settings_views import vendor_settings_router
from apps.website.ninja.admin_views import website_admin_router
from apps.website.ninja.media_views import website_media_router
from apps.website.ninja.views import website_misc_router, website_public_router
from authentication.auth_service.views import auth_service_router
from authentication.ninja.views import auth_router
from authentication.sessions.views import sessions_router

logger = logging.getLogger(__name__)

api = NinjaAPI(
    title="ADB Business Platform API",
    version="1.0",
    description="Shared API for the ADB Business Platform and public ADB websites.",
)

api.add_router("/analytics", analytics_router)
api.add_router("/auth", auth_router)
api.add_router("/auth-service", auth_service_router)
api.add_router("/sessions", sessions_router)

public_router = Router(tags=["public"])
public_router.add_router("", website_public_router)
api.add_router("/public", public_router)

website_router = Router(tags=["website"])
website_router.add_router("", website_misc_router)
api.add_router("/website", website_router)

admin_router = Router(tags=["admin"])
admin_router.add_router("", website_media_router)
admin_router.add_router("", staff_access_router)
admin_router.add_router("", dashboard_router)
admin_router.add_router("", operational_search_router)
admin_router.add_router("", operational_polish_router)
admin_router.add_router("", core_admin_router)
admin_router.add_router("", clients_admin_router)
admin_router.add_router("", client_overview_router)
admin_router.add_router("", client_command_centre_router)
admin_router.add_router("", time_tracking_router)
admin_router.add_router("", time_report_router)
admin_router.add_router("", crm_admin_router)
admin_router.add_router("", retention_router)
admin_router.add_router("", lead_email_router)
admin_router.add_router("", lead_overview_router)
admin_router.add_router("", tasks_admin_router)
admin_router.add_router("", calendar_router)
admin_router.add_router("", focus_router)
admin_router.add_router("", quick_router)
admin_router.add_router("", workspace_router)
admin_router.add_router("", relations_router)
admin_router.add_router("", section_router)
admin_router.add_router("", comment_router)
admin_router.add_router("", timeline_router)
admin_router.add_router("", ticketing_admin_router)
admin_router.add_router("", ticket_focus_router)
admin_router.add_router("", attachment_router)
admin_router.add_router("", operations_router)
admin_router.add_router("", ticketing_settings_router)
admin_router.add_router("", vendor_settings_router)
admin_router.add_router("", sla_router)
admin_router.add_router("", infrastructure_admin_router)
admin_router.add_router("", catalogue_router)
admin_router.add_router("", tag_router)
admin_router.add_router("", infrastructure_resource_router)
admin_router.add_router("", infrastructure_specialist_router)
admin_router.add_router("", infrastructure_specialist_edit_router)
admin_router.add_router("", data_application_specialist_router)
admin_router.add_router("", application_repository_router)
admin_router.add_router("", web_domain_specialist_router)
admin_router.add_router("", web_domain_nested_router)
admin_router.add_router("", operational_specialist_router)
admin_router.add_router("", operational_nested_router)
admin_router.add_router("", topology_router)
admin_router.add_router("", technology_router)
admin_router.add_router("", monitoring_router)
admin_router.add_router("", credential_router)
admin_router.add_router("", credential_lifecycle_router)
admin_router.add_router("", knowledge_base_router)
admin_router.add_router("", knowledge_attachment_router)
admin_router.add_router("", resource_admin_router)
admin_router.add_router("/website", website_admin_router)
admin_router.add_router("", github_router)
admin_router.add_router("", celery_dashboard_router)
api.add_router("/admin", admin_router)


@api.get("/csrf", auth=None)
@ensure_csrf_cookie
def get_csrf_token(request: HttpRequest) -> JsonResponse:
    """Return a CSRF token while ensuring the CSRF cookie is set."""
    token = get_token(request)
    return JsonResponse({"csrf_token": token})


@api.exception_handler(ValidationError)
def custom_validation_errors(request: HttpRequest, exc: ValidationError) -> HttpResponse:
    """Return validation details without logging potentially sensitive request bodies."""
    logger.info("Validation error on %s %s: %s", request.method, request.path, exc.errors())

    return api.create_response(
        request,
        {"detail": exc.errors()},
        status=422,
    )


@api.exception_handler(HttpError)
def custom_http_errors(request: HttpRequest, exc: HttpError) -> HttpResponse:
    """Return Django Ninja HTTP errors without logging request bodies."""
    logger.info("HTTP error on %s %s: %s", request.method, request.path, exc)

    return api.create_response(
        request,
        {"detail": str(exc)},
        status=exc.status_code,
    )


@api.exception_handler(ProviderError)
def analytics_provider_error(request: HttpRequest, exc: ProviderError) -> JsonResponse:
    return JsonResponse(
        {"detail": exc.code, "retryable": exc.retryable}, status=503 if exc.retryable else 400
    )

import logging

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from ninja import NinjaAPI, Router
from ninja.errors import HttpError
from pydantic import ValidationError

from apps.website.ninja.admin_views import website_admin_router
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

# Register nested routers.
api.add_router("/auth", auth_router)  # Staff/admin authentication.
api.add_router("/auth-service", auth_service_router)  # General account authentication.
api.add_router("/sessions", sessions_router)  # Session/device management.

# Public content, website ingestion and internal administration APIs.
public_router = Router(tags=["public"])
public_router.add_router("", website_public_router)
api.add_router("/public", public_router)

website_router = Router(tags=["website"])
website_router.add_router("", website_misc_router)
api.add_router("/website", website_router)

admin_router = Router(tags=["admin"])
admin_router.add_router("", website_admin_router)
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

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
    title="Project Template API",
    version="1.0",
    description="API for the Project Template",
)

# Register nested routers
api.add_router("/auth", auth_router)  # Admin auth (staff/superuser only)
api.add_router("/auth-service", auth_service_router)  # User auth (registration, login, 2FA, etc.)
api.add_router("/sessions", sessions_router)  # Session/device management

# Grouped routers for public, website, admin areas
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
    """Get CSRF token - this endpoint doesn't require CSRF validation.

    The @ensure_csrf_cookie decorator ensures the CSRF cookie is set in the response.
    """
    # This will set the CSRF cookie and return the token value
    token = get_token(request)
    return JsonResponse({"csrf_token": token})


@api.exception_handler(ValidationError)
def custom_validation_errors(request: HttpRequest, exc: ValidationError) -> HttpResponse:
    logger.info("Validation error on %s %s", request.method, request.path)
    logger.info("Request body: %s", request.body.decode("utf-8"))
    logger.info("Validation errors: %s", exc.errors())

    return api.create_response(
        request,
        {"detail": exc.errors()},
        status=422,
    )


@api.exception_handler(HttpError)
def custom_http_errors(request: HttpRequest, exc: HttpError) -> HttpResponse:
    logger.info("HTTP error on %s %s", request.method, request.path)
    logger.info("Request body: %s", request.body.decode("utf-8"))
    logger.info("HTTP error: %s", exc)

    return api.create_response(
        request,
        {"detail": str(exc)},
        status=exc.status_code,
    )

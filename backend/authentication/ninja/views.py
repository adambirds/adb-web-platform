"""Authentication views for the internal ADB Business Platform."""

import logging
from typing import Any

from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest
from django.middleware.csrf import get_token
from ninja import Router

from apps.access_control.policies import get_access_profile
from authentication.models import User
from authentication.ninja.schemas import (
    AccessScopeResponse,
    AuthResponse,
    LoginRequest,
    ObjectScopeResponse,
    ProblemDetail,
    StatusResponse,
    UserResponse,
)
from authentication.passkeys.security_logs_views import security_logs_router

logger = logging.getLogger(__name__)

auth_router = Router(tags=["auth"])
auth_router.add_router("/security-logs", security_logs_router)


def transform_user_to_response(user: User) -> UserResponse:
    """Build the current staff user's effective capability and object scopes."""
    profile = get_access_profile(user)

    if user.is_superuser:
        client_scope = ObjectScopeResponse(all=True, ids=[])
        ticket_queue_scope = ObjectScopeResponse(all=True, ids=[])
    elif profile is None:
        client_scope = ObjectScopeResponse()
        ticket_queue_scope = ObjectScopeResponse()
    else:
        client_scope = ObjectScopeResponse(
            all=profile.all_clients,
            ids=[]
            if profile.all_clients
            else list(profile.client_grants.values_list("client_id", flat=True)),
        )
        ticket_queue_scope = ObjectScopeResponse(
            all=profile.all_ticket_queues,
            ids=[],
        )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_staff=user.is_staff,
        is_superuser=user.is_superuser,
        permissions=sorted(user.get_all_permissions()),
        scope=AccessScopeResponse(
            clients=client_scope,
            ticket_queues=ticket_queue_scope,
        ),
    )


@auth_router.get(
    "/csrf",
    response={200: StatusResponse, 500: ProblemDetail},
)
def get_csrf_token(request: HttpRequest) -> tuple[int, dict[str, Any]]:
    try:
        token = get_token(request)
        return 200, {"message": "CSRF token set", "success": True, "token": token}
    except Exception as exc:
        logger.exception("Failed to issue a CSRF token: %s", exc)
        return 500, {"message": "An error has occurred.", "success": False, "code": "server_error"}


@auth_router.post(
    "/login",
    response={
        200: dict,
        401: ProblemDetail,
        403: ProblemDetail,
        500: ProblemDetail,
    },
)
def login_user(request: HttpRequest, login_data: LoginRequest) -> tuple[int, dict[str, Any]]:
    """Authenticate a staff user, optionally requiring a 2FA challenge."""
    from authentication.twofactor.utils import create_2fa_challenge, is_2fa_enabled

    try:
        user = authenticate(request, username=login_data.email, password=login_data.password)

        if user is None:
            return 401, {
                "message": "The username and password entered are incorrect.",
                "success": False,
                "code": "invalid_credentials",
            }

        if not (user.is_staff or user.is_superuser):
            return 403, {
                "message": "You do not have permission to access this resource.",
                "success": False,
                "code": "forbidden",
            }

        if is_2fa_enabled(user):
            token = create_2fa_challenge(user, request)
            return 200, {
                "success": True,
                "requires_2fa": True,
                "challenge_token": token,
                "message": "Two-factor authentication is required",
            }

        login(request, user)
        get_token(request)
        return 200, {
            "user": transform_user_to_response(user),
            "message": "Login successful",
            "success": True,
            "requires_2fa": False,
        }

    except Exception as exc:
        logger.exception("Staff login failed unexpectedly: %s", exc)
        return 500, {"message": "An error has occurred.", "success": False, "code": "server_error"}


@auth_router.post(
    "/logout",
    response={200: StatusResponse, 401: ProblemDetail, 500: ProblemDetail},
)
def logout_user(request: HttpRequest) -> tuple[int, dict[str, Any]]:
    try:
        if not request.user.is_authenticated:
            return 401, {
                "message": "User not authenticated",
                "success": False,
                "code": "unauthenticated",
            }

        logout(request)
        return 200, {"message": "Logout successful", "success": True}

    except Exception as exc:
        logger.exception("Staff logout failed unexpectedly: %s", exc)
        return 500, {"message": "An error has occurred.", "success": False, "code": "server_error"}


@auth_router.get(
    "/me",
    response={200: AuthResponse, 401: ProblemDetail, 403: ProblemDetail, 500: ProblemDetail},
)
def get_current_user(request: HttpRequest) -> tuple[int, dict[str, Any]]:
    try:
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

        return 200, {
            "user": transform_user_to_response(request.user),
            "message": "User authenticated",
            "success": True,
        }

    except Exception as exc:
        logger.exception("Failed to resolve the current staff user: %s", exc)
        return 500, {"message": "An error has occurred.", "success": False, "code": "server_error"}

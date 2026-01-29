"""Authentication views for Django Ninja API with proper HTTP status codes and response mapping."""

import logging
from typing import Any

from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest
from django.middleware.csrf import get_token
from ninja import Router

from authentication.models import User
from authentication.ninja.schemas import (
    AuthResponse,
    LoginRequest,
    ProblemDetail,
    StatusResponse,
    UserResponse,
)
from authentication.passkeys.security_logs_views import security_logs_router

logger = logging.getLogger(__name__)

auth_router = Router(tags=["auth"])

# Add security logs routes
auth_router.add_router("/security-logs", security_logs_router)


def transform_user_to_response(user: User) -> UserResponse:
    author = None
    if hasattr(user, "author") and user.author:
        author = {
            "avatar": getattr(user.author, "avatar", None),
            "bio": getattr(user.author, "bio", None),
        }

    return UserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_staff=user.is_staff,
        author=author,
    )


@auth_router.get(
    "/csrf",
    response={200: StatusResponse, 500: ProblemDetail},
)
def get_csrf_token(request: HttpRequest) -> tuple[int, dict[str, Any]]:
    try:
        # Explicitly get and set the CSRF token
        token = get_token(request)
        # The middleware will set the cookie, but let's ensure it's there
        return 200, {"message": "CSRF token set", "success": True, "token": token}
    except Exception as e:
        logger.error("CSRF error: %s", str(e))
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
    """
    200: success (or 2FA required)
    401: invalid credentials
    403: authenticated but not staff/superuser
    500: server error
    """
    from authentication.twofactor.utils import create_2fa_challenge, is_2fa_enabled

    try:
        logger.info("[LOGIN] Attempting login for email: %s", login_data.email)
        user = authenticate(request, username=login_data.email, password=login_data.password)
        logger.info("[LOGIN] Authentication result: %s", user is not None)

        if user is None:
            logger.warning("[LOGIN] Invalid credentials for email: %s", login_data.email)
            return 401, {
                "message": "The username and password entered are incorrect.",
                "success": False,
                "code": "invalid_credentials",
            }

        logger.info(
            "[LOGIN] User authenticated: %s, is_staff: %s, is_superuser: %s",
            user.email,
            user.is_staff,
            user.is_superuser,
        )
        if not (user.is_staff or user.is_superuser):
            logger.warning("[LOGIN] User not staff/superuser: %s", user.email)
            return 403, {
                "message": "You do not have permission to access this resource.",
                "success": False,
                "code": "forbidden",
            }

        # Check if 2FA is enabled
        logger.info("[LOGIN] Checking 2FA status for: %s", user.email)
        if is_2fa_enabled(user):
            logger.info("[LOGIN] 2FA required for: %s", user.email)
            # Create a 2FA challenge instead of logging in
            token = create_2fa_challenge(user, request)
            return 200, {
                "success": True,
                "requires_2fa": True,
                "challenge_token": token,
                "message": "Two-factor authentication is required",
            }

        logger.info("[LOGIN] Calling Django login for: %s", user.email)
        login(request, user)
        logger.info("[LOGIN] Getting CSRF token")
        get_token(request)  # rotate/ensure CSRF with new session
        logger.info("[LOGIN] Login successful for: %s", user.email)
        return 200, {
            "user": transform_user_to_response(user),
            "message": "Login successful",
            "success": True,
            "requires_2fa": False,
        }

    except Exception as e:
        logger.error("Login error: %s", str(e))
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

    except Exception as e:
        logger.error("Logout error: %s", str(e))
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

    except Exception as e:
        logger.error("Get current user error: %s", str(e))
        return 500, {"message": "An error has occurred.", "success": False, "code": "server_error"}

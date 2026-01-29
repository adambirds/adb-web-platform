"""API views for session and device management."""

import logging
from typing import Any

from django.http import HttpRequest
from ninja import Router, Schema

from authentication.sessions.models import UserSession
from authentication.sessions.utils import revoke_all_other_sessions, revoke_user_session

logger = logging.getLogger(__name__)

sessions_router = Router(tags=["sessions"])


class SessionResponse(Schema):
    """Schema for a single session."""

    id: str
    device_type: str
    device_name: str
    browser: str
    operating_system: str
    ip_address: str | None
    location: str
    created_at: str
    last_activity: str
    auth_method: str
    is_current: bool


class SessionListResponse(Schema):
    """Response schema for session list."""

    success: bool
    sessions: list[SessionResponse]
    message: str = ""


class RevokeSessionRequest(Schema):
    """Request schema for revoking a session."""

    session_id: str


class RevokeSessionResponse(Schema):
    """Response schema for session revocation."""

    success: bool
    message: str


@sessions_router.get("/list", response={200: dict})
def list_sessions(request: HttpRequest) -> tuple[int, dict[str, Any]]:
    """
    List all active sessions for the current user.

    Returns a list of sessions with device and location information.
    The current session is marked with is_current=True.
    """
    if not request.user.is_authenticated:
        return 200, {
            "success": False,
            "message": "Not authenticated",
            "sessions": [],
        }

    try:
        current_session_key = request.session.session_key
        sessions = UserSession.objects.filter(
            user=request.user,
            expires_at__isnull=False,
        ).exclude(expires_at__lt=__import__("django.utils.timezone", fromlist=["now"]).now())

        session_list = [
            {
                "id": str(session.id),
                "device_type": session.device_type,
                "device_name": session.device_name,
                "browser": session.browser,
                "operating_system": session.operating_system,
                "ip_address": session.ip_address,
                "location": session.location or "Unknown location",
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "auth_method": session.auth_method,
                "is_current": session.session_key == current_session_key,
            }
            for session in sessions
        ]

        return 200, {
            "success": True,
            "sessions": session_list,
            "message": "",
        }
    except Exception as e:
        logger.error("Error listing sessions: %s", e)
        return 200, {
            "success": False,
            "message": "Failed to list sessions",
            "sessions": [],
        }


@sessions_router.post("/revoke", response={200: dict})
def revoke_session(
    request: HttpRequest,
    data: RevokeSessionRequest,
) -> tuple[int, dict[str, Any]]:
    """
    Revoke (log out) a specific session.

    Users cannot revoke their current session (use logout instead).
    """
    if not request.user.is_authenticated:
        return 200, {
            "success": False,
            "message": "Not authenticated",
        }

    try:
        # Check if trying to revoke current session
        session = UserSession.objects.filter(
            id=data.session_id,
            user=request.user,
        ).first()

        if not session:
            return 200, {
                "success": False,
                "message": "Session not found",
            }

        if session.session_key == request.session.session_key:
            return 200, {
                "success": False,
                "message": "Cannot revoke current session. Use logout instead.",
            }

        success = revoke_user_session(data.session_id, request.user)

        if success:
            return 200, {
                "success": True,
                "message": "Session revoked successfully",
            }
        else:
            return 200, {
                "success": False,
                "message": "Failed to revoke session",
            }
    except Exception as e:
        logger.error("Error revoking session: %s", e)
        return 200, {
            "success": False,
            "message": "An error occurred",
        }


@sessions_router.post("/revoke-all", response={200: dict})
def revoke_all_sessions(request: HttpRequest) -> tuple[int, dict[str, Any]]:
    """
    Revoke all sessions except the current one.

    This is useful when a user suspects their account may be compromised.
    """
    if not request.user.is_authenticated:
        return 200, {
            "success": False,
            "message": "Not authenticated",
        }

    try:
        current_session_key = request.session.session_key
        if current_session_key is None:
            return 200, {
                "success": False,
                "message": "No active session",
            }
        count = revoke_all_other_sessions(request.user, current_session_key)

        return 200, {
            "success": True,
            "message": f"Revoked {count} session(s)",
            "revoked_count": count,
        }
    except Exception as e:
        logger.error("Error revoking all sessions: %s", e)
        return 200, {
            "success": False,
            "message": "An error occurred",
        }

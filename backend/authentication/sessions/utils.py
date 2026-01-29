"""Utilities for session and device management."""

import logging
import re
from datetime import timedelta
from typing import TYPE_CHECKING

from django.conf import settings
from django.http import HttpRequest
from django.utils import timezone

if TYPE_CHECKING:
    from authentication.models import User
    from authentication.sessions.models import UserSession

logger = logging.getLogger(__name__)


def get_client_ip(request: HttpRequest) -> str | None:
    """Extract client IP address from request headers."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # Take the first IP in the chain (original client)
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def parse_user_agent(user_agent: str) -> dict[str, str]:
    """
    Parse user agent string to extract device, browser, and OS information.

    Returns a dictionary with:
    - device_type: desktop, mobile, tablet, or unknown
    - device_name: Human-readable device description
    - browser: Browser name and version
    - operating_system: OS name and version
    """
    result = {
        "device_type": "unknown",
        "device_name": "Unknown Device",
        "browser": "Unknown",
        "operating_system": "Unknown",
    }

    if not user_agent:
        return result

    ua_lower = user_agent.lower()

    # Detect device type
    if any(x in ua_lower for x in ["iphone", "android", "mobile", "phone"]):
        result["device_type"] = "mobile"
    elif any(x in ua_lower for x in ["ipad", "tablet"]):
        result["device_type"] = "tablet"
    else:
        result["device_type"] = "desktop"

    # Detect operating system
    if "windows nt 10" in ua_lower or "windows nt 11" in ua_lower:
        result["operating_system"] = "Windows"
    elif "windows" in ua_lower:
        result["operating_system"] = "Windows"
    elif "mac os x" in ua_lower or "macos" in ua_lower:
        result["operating_system"] = "macOS"
    elif "iphone" in ua_lower or "ipad" in ua_lower:
        result["operating_system"] = "iOS"
    elif "android" in ua_lower:
        result["operating_system"] = "Android"
    elif "linux" in ua_lower:
        result["operating_system"] = "Linux"
    elif "chrome os" in ua_lower:
        result["operating_system"] = "Chrome OS"

    # Detect browser (order matters - check specific before generic)
    if "edg/" in ua_lower or "edge/" in ua_lower:
        result["browser"] = "Microsoft Edge"
    elif "opr/" in ua_lower or "opera" in ua_lower:
        result["browser"] = "Opera"
    elif "brave" in ua_lower:
        result["browser"] = "Brave"
    elif "firefox" in ua_lower:
        # Extract version
        match = re.search(r"firefox[/\s]?(\d+)", ua_lower)
        version = match.group(1) if match else ""
        result["browser"] = f"Firefox {version}".strip()
    elif "chrome" in ua_lower and "safari" in ua_lower:
        # Chrome includes Safari in UA
        match = re.search(r"chrome[/\s]?(\d+)", ua_lower)
        version = match.group(1) if match else ""
        result["browser"] = f"Chrome {version}".strip()
    elif "safari" in ua_lower and "chrome" not in ua_lower:
        match = re.search(r"version[/\s]?(\d+)", ua_lower)
        version = match.group(1) if match else ""
        result["browser"] = f"Safari {version}".strip()

    # Create device name
    device_parts = []
    if result["browser"] != "Unknown":
        device_parts.append(result["browser"])
    if result["operating_system"] != "Unknown":
        device_parts.append(f"on {result['operating_system']}")

    if device_parts:
        result["device_name"] = " ".join(device_parts)
    else:
        result["device_name"] = result["device_type"].title()

    return result


def create_user_session(
    user: "User",
    request: HttpRequest,
    auth_method: str = "password",
) -> "UserSession":
    """
    Create a new UserSession record for a user login.

    Args:
        user: The authenticated user
        request: The HTTP request object
        auth_method: How the user authenticated (password, passkey, 2fa)

    Returns:
        The created UserSession instance
    """
    from authentication.sessions.models import UserSession

    # Get session key (create session if needed)
    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key
    assert session_key is not None, "Session key should exist after create()"

    # Check if session already exists
    existing = UserSession.objects.filter(session_key=session_key).first()
    if existing:
        existing.last_activity = timezone.now()
        existing.save(update_fields=["last_activity"])
        return existing

    # Parse user agent
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    device_info = parse_user_agent(user_agent)

    # Get client IP
    ip_address = get_client_ip(request)

    # Calculate session expiry
    session_age = getattr(settings, "SESSION_COOKIE_AGE", 864000)
    expires_at = timezone.now() + timedelta(seconds=session_age)

    # Create the session record
    session = UserSession.objects.create(
        user=user,
        session_key=session_key,
        device_type=device_info["device_type"],
        device_name=device_info["device_name"],
        browser=device_info["browser"],
        operating_system=device_info["operating_system"],
        user_agent=user_agent,
        ip_address=ip_address,
        auth_method=auth_method,
        expires_at=expires_at,
    )

    logger.info(
        "Created session for user %s from %s (%s)",
        user.email,
        ip_address,
        device_info["device_name"],
    )

    return session


def revoke_user_session(session_id: str, user: "User") -> bool:
    """
    Revoke (delete) a user session.

    Args:
        session_id: The UUID of the session to revoke
        user: The user who owns the session (for authorization)

    Returns:
        True if session was revoked, False if not found or unauthorized
    """
    from django.contrib.sessions.models import Session as DjangoSession

    from authentication.sessions.models import UserSession

    try:
        session = UserSession.objects.get(id=session_id, user=user)

        # Delete the Django session to actually log them out
        try:
            DjangoSession.objects.filter(session_key=session.session_key).delete()
        except Exception as e:
            logger.warning("Could not delete Django session: %s", e)

        # Delete our session record
        session.delete()

        logger.info("Revoked session %s for user %s", session_id, user.email)
        return True
    except UserSession.DoesNotExist:
        return False


def revoke_all_other_sessions(user: "User", current_session_key: str) -> int:
    """
    Revoke all sessions for a user except the current one.

    Args:
        user: The user whose sessions to revoke
        current_session_key: The session key to keep active

    Returns:
        Number of sessions revoked
    """
    from django.contrib.sessions.models import Session as DjangoSession

    from authentication.sessions.models import UserSession

    other_sessions = UserSession.objects.filter(user=user).exclude(session_key=current_session_key)

    count = other_sessions.count()

    # Delete Django sessions
    session_keys = list(other_sessions.values_list("session_key", flat=True))
    DjangoSession.objects.filter(session_key__in=session_keys).delete()

    # Delete our session records
    other_sessions.delete()

    logger.info("Revoked %d sessions for user %s", count, user.email)
    return count


def cleanup_expired_sessions() -> int:
    """
    Delete expired session records.

    Should be run periodically via a celery task or management command.

    Returns:
        Number of sessions deleted
    """
    from authentication.sessions.models import UserSession

    expired = UserSession.objects.filter(expires_at__lt=timezone.now())
    count = expired.count()
    expired.delete()

    logger.info("Cleaned up %d expired sessions", count)
    return count

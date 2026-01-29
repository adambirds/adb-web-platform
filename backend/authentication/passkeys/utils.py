"""WebAuthn utility functions for passkey authentication."""

import base64
import os
import secrets
from typing import Any

from django.conf import settings

# WebAuthn RP (Relying Party) configuration
# These should be set in Django settings


def get_rp_id() -> str:
    """Get the Relying Party ID from settings."""
    return getattr(settings, "WEBAUTHN_RP_ID", settings.SITE_DOMAIN)


def get_rp_name() -> str:
    """Get the Relying Party name from settings."""
    return getattr(settings, "WEBAUTHN_RP_NAME", getattr(settings, "SITE_NAME", "App"))


def get_origin() -> str:
    """Get the primary origin URL for WebAuthn verification."""
    return getattr(settings, "WEBAUTHN_ORIGIN", settings.FRONTEND_URL)


def get_allowed_origins() -> list[str]:
    """Get all allowed origins for WebAuthn verification."""
    origins = getattr(settings, "WEBAUTHN_ALLOWED_ORIGINS", None)
    if origins:
        return origins
    # Default to frontend URL, admin frontend URL, and docs frontend URL
    allowed = [settings.FRONTEND_URL]
    admin_url = getattr(settings, "ADMIN_FRONTEND_URL", None)
    if admin_url:
        allowed.append(admin_url)
    docs_url = getattr(settings, "DOCS_FRONTEND_URL", None)
    if docs_url:
        allowed.append(docs_url)
    return allowed


def generate_challenge() -> bytes:
    """Generate a random challenge for WebAuthn ceremonies."""
    return secrets.token_bytes(32)


def bytes_to_base64url(data: bytes) -> str:
    """Convert bytes to base64url encoding (no padding)."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def base64url_to_bytes(data: str) -> bytes:
    """Convert base64url encoding to bytes."""
    # Add padding if needed
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def generate_user_handle() -> bytes:
    """Generate a random user handle for WebAuthn."""
    return os.urandom(32)


def create_registration_options(
    user_id: str,
    user_email: str,
    user_name: str,
    challenge: bytes,
    exclude_credentials: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Create WebAuthn registration options.

    Args:
        user_id: Unique identifier for the user
        user_email: User's email address
        user_name: User's display name
        challenge: The challenge bytes
        exclude_credentials: List of existing credentials to exclude

    Returns:
        Registration options dictionary for the WebAuthn API
    """
    options: dict[str, Any] = {
        "rp": {
            "name": get_rp_name(),
            "id": get_rp_id(),
        },
        "user": {
            "id": bytes_to_base64url(user_id.encode("utf-8")),
            "name": user_email,
            "displayName": user_name,
        },
        "challenge": bytes_to_base64url(challenge),
        "pubKeyCredParams": [
            {"type": "public-key", "alg": -7},  # ES256
            {"type": "public-key", "alg": -257},  # RS256
        ],
        "timeout": 60000,
        "attestation": "none",
        "authenticatorSelection": {
            # Allow both platform (built-in) and cross-platform (security key) authenticators
            # Removed "authenticatorAttachment": "platform" to support YubiKey and other roaming authenticators
            "residentKey": "required",  # Required for discoverable credentials
            "requireResidentKey": True,  # Ensure credentials are discoverable
            "userVerification": "preferred",
        },
    }

    if exclude_credentials:
        options["excludeCredentials"] = exclude_credentials

    return options


def create_authentication_options(
    challenge: bytes,
    allow_credentials: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Create WebAuthn authentication options.

    Args:
        challenge: The challenge bytes
        allow_credentials: List of allowed credentials (empty for discoverable credentials)

    Returns:
        Authentication options dictionary for the WebAuthn API
    """
    options: dict[str, Any] = {
        "challenge": bytes_to_base64url(challenge),
        "rpId": get_rp_id(),
        "timeout": 60000,
        "userVerification": "preferred",
    }

    if allow_credentials:
        options["allowCredentials"] = allow_credentials

    return options

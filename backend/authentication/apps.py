from typing import TYPE_CHECKING
from urllib.parse import urlparse

from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured


class AuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "authentication"

    def ready(self) -> None:
        """Validate WebAuthn configuration on startup."""
        from django.conf import settings

        # Skip validation during type checking or in test environment
        if TYPE_CHECKING or getattr(settings, "TESTING", False):
            return

        # Validate WebAuthn origins against RP ID
        rp_id = getattr(settings, "WEBAUTHN_RP_ID", None)
        allowed_origins = getattr(settings, "WEBAUTHN_ALLOWED_ORIGINS", [])

        if rp_id and allowed_origins:
            for origin in allowed_origins:
                if not origin:
                    continue
                # Remove trailing slash if present
                origin = origin.rstrip("/")
                parsed = urlparse(origin)
                hostname = parsed.hostname or ""

                # RP ID must be equal to or a registrable domain suffix of the origin
                if not (hostname == rp_id or hostname.endswith(f".{rp_id}")):
                    raise ImproperlyConfigured(
                        f"WebAuthn origin '{origin}' hostname '{hostname}' is not valid "
                        f"for RP ID '{rp_id}'. The origin's hostname must be equal to "
                        "or a subdomain of the RP ID."
                    )

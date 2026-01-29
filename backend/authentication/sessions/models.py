"""Models for tracking user sessions and devices."""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class UserSession(models.Model):
    """
    Tracks user login sessions with device and location information.

    This model stores metadata about each session, allowing users to:
    - View all active sessions/devices
    - See last activity time and location
    - Revoke sessions remotely
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    session_key = models.CharField(
        max_length=40,
        unique=True,
        db_index=True,
        help_text="Django session key for this session",
    )

    # Device information
    device_type = models.CharField(
        max_length=50,
        default="unknown",
        help_text="Type of device: desktop, mobile, tablet, etc.",
    )
    device_name = models.CharField(
        max_length=255,
        default="Unknown Device",
        help_text="Human-readable device name",
    )
    browser = models.CharField(
        max_length=100,
        default="Unknown",
        help_text="Browser name and version",
    )
    operating_system = models.CharField(
        max_length=100,
        default="Unknown",
        help_text="Operating system name and version",
    )
    user_agent = models.TextField(
        blank=True,
        default="",
        help_text="Full user agent string",
    )

    # Location information
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the session",
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Approximate location based on IP",
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this session expires",
    )

    # Authentication method used
    auth_method = models.CharField(
        max_length=50,
        default="password",
        choices=[
            ("password", "Password"),
            ("passkey", "Passkey"),
            ("2fa", "Two-Factor Authentication"),
        ],
        help_text="How the user authenticated for this session",
    )

    # Current session flag
    is_current = models.BooleanField(
        default=False,
        help_text="Whether this is the user's current session (set dynamically)",
    )

    class Meta:
        ordering = ["-last_activity"]
        verbose_name = "User Session"
        verbose_name_plural = "User Sessions"
        indexes = [
            models.Index(fields=["user", "-last_activity"]),
            models.Index(fields=["session_key"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.device_name} ({self.ip_address})"

    @property
    def is_expired(self) -> bool:
        """Check if this session has expired."""
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at

    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = timezone.now()
        self.save(update_fields=["last_activity"])

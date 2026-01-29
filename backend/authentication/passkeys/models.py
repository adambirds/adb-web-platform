"""Passkey model for WebAuthn passkey authentication."""

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Passkey(models.Model):
    """
    Stores WebAuthn credentials (passkeys) for passwordless authentication.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="passkeys",
        verbose_name=_("user"),
    )
    credential_id = models.BinaryField(
        verbose_name=_("credential ID"),
        unique=True,
        help_text=_("The unique identifier for this credential from the authenticator."),
    )
    public_key = models.BinaryField(
        verbose_name=_("public key"),
        help_text=_("The public key from the authenticator."),
    )
    sign_count = models.PositiveIntegerField(
        verbose_name=_("sign count"),
        default=0,
        help_text=_("The number of times this credential has been used."),
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("name"),
        help_text=_("A user-friendly name for this passkey."),
    )
    device_type = models.CharField(
        max_length=50,
        verbose_name=_("device type"),
        default="",
        blank=True,
        help_text=_("The type of authenticator device."),
    )
    backed_up = models.BooleanField(
        verbose_name=_("backed up"),
        default=False,
        help_text=_("Whether this credential is backed up."),
    )
    transports = models.JSONField(
        verbose_name=_("transports"),
        default=list,
        blank=True,
        help_text=_("The list of transports supported by this credential."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("created at"),
    )
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("last used at"),
    )

    class Meta:
        verbose_name = _("passkey")
        verbose_name_plural = _("passkeys")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.user.email})"


class PasskeyChallenge(models.Model):
    """
    Temporary storage for WebAuthn challenges during registration and authentication.
    Challenges are short-lived and should be cleaned up regularly.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="passkey_challenges",
        verbose_name=_("user"),
        null=True,
        blank=True,
        help_text=_("The user this challenge is for. Null for authentication challenges."),
    )
    challenge = models.BinaryField(
        verbose_name=_("challenge"),
        help_text=_("The challenge bytes."),
    )
    challenge_type = models.CharField(
        max_length=20,
        choices=[
            ("registration", "Registration"),
            ("authentication", "Authentication"),
        ],
        verbose_name=_("challenge type"),
    )
    email = models.EmailField(
        verbose_name=_("email"),
        null=True,
        blank=True,
        help_text=_("Email for authentication challenges when user is not yet identified."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("created at"),
    )

    class Meta:
        verbose_name = _("passkey challenge")
        verbose_name_plural = _("passkey challenges")
        indexes = [
            models.Index(fields=["user", "challenge_type", "created_at"]),
            models.Index(fields=["email", "challenge_type", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.challenge_type} challenge ({self.created_at})"


class PasskeyAuthenticationLog(models.Model):
    """
    Audit log for passkey authentication attempts.
    Stores security events for compliance and monitoring.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="passkey_auth_logs",
        verbose_name=_("user"),
        null=True,
        blank=True,
        help_text=_("The user associated with this authentication attempt."),
    )
    email = models.EmailField(
        verbose_name=_("email"),
        null=True,
        blank=True,
        help_text=_("Email used for authentication attempt."),
    )
    event_type = models.CharField(
        max_length=50,
        choices=[
            ("auth_started", "Authentication Started"),
            ("auth_success", "Authentication Successful"),
            ("auth_failed", "Authentication Failed"),
            ("auth_error", "Authentication Error"),
            ("passkey_not_found", "Passkey Not Found"),
            ("challenge_expired", "Challenge Expired"),
            ("verification_failed", "Verification Failed"),
        ],
        verbose_name=_("event type"),
    )
    passkey = models.ForeignKey(
        Passkey,
        on_delete=models.SET_NULL,
        related_name="auth_logs",
        verbose_name=_("passkey"),
        null=True,
        blank=True,
        help_text=_("The passkey used in this authentication attempt."),
    )
    ip_address = models.GenericIPAddressField(
        verbose_name=_("IP address"),
        null=True,
        blank=True,
        help_text=_("IP address of the authentication attempt."),
    )
    user_agent = models.TextField(
        verbose_name=_("user agent"),
        blank=True,
        default="",
        help_text=_("User agent string from the request."),
    )
    error_message = models.TextField(
        verbose_name=_("error message"),
        blank=True,
        default="",
        help_text=_("Error message if authentication failed."),
    )
    metadata = models.JSONField(
        verbose_name=_("metadata"),
        default=dict,
        blank=True,
        help_text=_("Additional metadata about the authentication attempt."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("created at"),
    )

    class Meta:
        verbose_name = _("passkey authentication log")
        verbose_name_plural = _("passkey authentication logs")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["email", "created_at"]),
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["ip_address", "created_at"]),
        ]

    def __str__(self) -> str:
        user_str = self.user.email if self.user else self.email or "Unknown"
        return f"{self.event_type} - {user_str} ({self.created_at})"

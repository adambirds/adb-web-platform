"""Two-factor authentication models."""

import secrets
import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class TwoFactorMethod(models.Model):
    """
    Stores two-factor authentication methods for users.
    Supports TOTP (authenticator apps) and recovery codes.
    """

    class MethodType(models.TextChoices):
        TOTP = "totp", _("Authenticator App (TOTP)")
        RECOVERY = "recovery", _("Recovery Codes")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="two_factor_methods",
        verbose_name=_("user"),
    )
    method_type = models.CharField(
        max_length=20,
        choices=MethodType.choices,
        verbose_name=_("method type"),
    )
    # For TOTP: base32-encoded secret key (encrypted)
    # For recovery codes: not used (codes stored separately)
    secret = models.CharField(
        max_length=512,
        verbose_name=_("secret"),
        blank=True,
        help_text=_("Encrypted secret for TOTP methods."),
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("name"),
        default="",
        blank=True,
        help_text=_("A user-friendly name for this 2FA method."),
    )
    is_primary = models.BooleanField(
        verbose_name=_("is primary"),
        default=False,
        help_text=_("Whether this is the primary 2FA method."),
    )
    is_verified = models.BooleanField(
        verbose_name=_("is verified"),
        default=False,
        help_text=_("Whether this method has been verified by the user."),
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
        verbose_name = _("two-factor method")
        verbose_name_plural = _("two-factor methods")
        ordering = ["-is_primary", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "method_type"],
                condition=models.Q(method_type="totp"),
                name="unique_totp_per_user",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_method_type_display()} for {self.user.email}"


class RecoveryCode(models.Model):
    """
    Stores recovery codes for two-factor authentication backup.
    Each user gets a set of one-time use recovery codes.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recovery_codes",
        verbose_name=_("user"),
    )
    # Hashed recovery code (we never store plaintext)
    code_hash = models.CharField(
        max_length=128,
        verbose_name=_("code hash"),
        help_text=_("SHA-256 hash of the recovery code."),
    )
    is_used = models.BooleanField(
        verbose_name=_("is used"),
        default=False,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("created at"),
    )
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("used at"),
    )

    class Meta:
        verbose_name = _("recovery code")
        verbose_name_plural = _("recovery codes")
        ordering = ["created_at"]

    def __str__(self) -> str:
        status = "used" if self.is_used else "available"
        return f"Recovery code for {self.user.email} ({status})"

    @classmethod
    def generate_code(cls) -> str:
        """Generate a random recovery code in format XXXX-XXXX-XXXX."""
        # Generate 12 random alphanumeric characters (excluding confusing chars)
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # No I, O, 0, 1
        code_parts = []
        for _i in range(3):
            part = "".join(secrets.choice(chars) for _j in range(4))
            code_parts.append(part)
        return "-".join(code_parts)


class TwoFactorChallenge(models.Model):
    """
    Temporary storage for 2FA challenges during login.
    Tracks pending 2FA verifications before completing authentication.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="two_factor_challenges",
        verbose_name=_("user"),
    )
    # Token to identify this challenge session
    challenge_token = models.CharField(
        max_length=64,
        unique=True,
        verbose_name=_("challenge token"),
    )
    # Whether the password has been verified
    password_verified = models.BooleanField(
        verbose_name=_("password verified"),
        default=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("created at"),
    )
    ip_address = models.GenericIPAddressField(
        verbose_name=_("IP address"),
        null=True,
        blank=True,
    )
    user_agent = models.TextField(
        verbose_name=_("user agent"),
        blank=True,
        default="",
    )

    class Meta:
        verbose_name = _("two-factor challenge")
        verbose_name_plural = _("two-factor challenges")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"2FA challenge for {self.user.email}"

    @classmethod
    def generate_token(cls) -> str:
        """Generate a secure random token for the challenge."""
        return secrets.token_urlsafe(48)

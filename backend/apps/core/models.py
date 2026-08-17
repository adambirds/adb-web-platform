from __future__ import annotations

from typing import Any

from django.conf import settings
from django.db import models


class Brand(models.Model):
    """Public ADB brand served by the shared business platform."""

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=80, unique=True)
    domain = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class AuditEvent(models.Model):
    """Append-only record of security-sensitive and operational actions."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    action = models.CharField(max_length=150)
    target_type = models.CharField(max_length=150, blank=True)
    target_id = models.CharField(max_length=255, blank=True)
    target_label = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("view_sensitive_audit_metadata", "Can view sensitive audit metadata"),
        ]

    def __str__(self) -> str:
        actor = self.actor.email if self.actor else "system"
        target = f" {self.target_type}:{self.target_id}" if self.target_type else ""
        return f"{actor} {self.action}{target}"

    @classmethod
    def record(
        cls,
        *,
        action: str,
        actor: Any | None = None,
        target: Any | None = None,
        target_label: str = "",
        metadata: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str = "",
    ) -> "AuditEvent":
        """Create an audit event without serialising sensitive target fields."""
        return cls.objects.create(
            actor=actor if getattr(actor, "is_authenticated", False) else None,
            action=action,
            target_type=target._meta.label_lower if target is not None else "",
            target_id=str(target.pk) if target is not None else "",
            target_label=target_label or (str(target) if target is not None else ""),
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )

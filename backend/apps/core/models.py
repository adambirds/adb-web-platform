from __future__ import annotations

from typing import Any

from django.conf import settings
from django.db import models
from django.utils import timezone


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


class DashboardPreference(models.Model):
    """Server-persisted personal Dashboard/My Work layout for one staff user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dashboard_preference",
    )
    layout = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user_id"]

    def __str__(self) -> str:
        return f"Dashboard preferences for {self.user}"


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
    client_id = models.PositiveBigIntegerField(null=True, blank=True, db_index=True)
    resource_id = models.PositiveBigIntegerField(null=True, blank=True, db_index=True)
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

    @staticmethod
    def _target_context(target: Any | None) -> tuple[int | None, int | None]:
        if target is None:
            return None, None

        client_id = getattr(target, "client_id", None)
        resource_id: int | None = None
        meta = getattr(target, "_meta", None)
        label = getattr(meta, "label_lower", "") if meta is not None else ""
        if label == "clients.client":
            client_id = getattr(target, "pk", client_id)
        if label == "infrastructure.infrastructureresource":
            resource_id = getattr(target, "pk", None)

        resource = getattr(target, "resource", None)
        if resource is not None:
            resource_id = getattr(resource, "pk", resource_id)
            client_id = getattr(resource, "client_id", client_id)

        monitor_check = getattr(target, "monitor_check", None)
        monitor_resource = getattr(monitor_check, "resource", None)
        if monitor_resource is not None:
            resource_id = getattr(monitor_resource, "pk", resource_id)
            client_id = getattr(monitor_resource, "client_id", client_id)

        return client_id, resource_id

    @classmethod
    def record(
        cls,
        *,
        action: str,
        actor: Any | None = None,
        target: Any | None = None,
        target_label: str = "",
        metadata: dict[str, Any] | None = None,
        client_id: int | None = None,
        resource_id: int | None = None,
        ip_address: str | None = None,
        user_agent: str = "",
    ) -> AuditEvent:
        """Create an audit event without serialising sensitive target fields."""
        inferred_client_id, inferred_resource_id = cls._target_context(target)
        return cls.objects.create(
            actor=actor if getattr(actor, "is_authenticated", False) else None,
            action=action,
            target_type=target._meta.label_lower if target is not None else "",
            target_id=str(target.pk) if target is not None else "",
            target_label=target_label or (str(target) if target is not None else ""),
            client_id=client_id if client_id is not None else inferred_client_id,
            resource_id=resource_id if resource_id is not None else inferred_resource_id,
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )


class Notification(models.Model):
    """Server-backed operational alert/read state for one staff user."""

    class Category(models.TextChoices):
        TASK = "task", "Task"
        TICKET = "ticket", "Ticket"
        CREDENTIAL = "credential", "Credential"
        MONITORING = "monitoring", "Monitoring"
        SECURITY = "security", "Security"
        CALENDAR = "calendar", "Calendar"
        GENERAL = "general", "General"

    class Severity(models.TextChoices):
        INFO = "info", "Information"
        WARNING = "warning", "Warning"
        CRITICAL = "critical", "Critical"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="operational_notifications",
    )
    category = models.CharField(max_length=24, choices=Category.choices)
    severity = models.CharField(
        max_length=16,
        choices=Severity.choices,
        default=Severity.INFO,
    )
    source_key = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    href = models.CharField(max_length=500, blank=True)
    client_id = models.PositiveBigIntegerField(null=True, blank=True, db_index=True)
    resource_id = models.PositiveBigIntegerField(null=True, blank=True, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "source_key"],
                name="unique_operational_notification_source",
            )
        ]
        indexes = [
            models.Index(
                fields=["user", "resolved_at", "dismissed_at", "created_at"],
                name="notification_user_state_idx",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user}: {self.title}"


class CeleryTaskExecution(models.Model):
    """Safe execution metadata only; never arguments, results or exception messages."""

    class State(models.TextChoices):
        QUEUED = "QUEUED", "Queued"
        STARTED = "STARTED", "Running"
        RETRY = "RETRY", "Retrying"
        SUCCESS = "SUCCESS", "Succeeded"
        FAILURE = "FAILURE", "Failed"
        REVOKED = "REVOKED", "Revoked"
        IGNORED = "IGNORED", "Ignored"

    id = models.CharField(primary_key=True, max_length=255)
    task_name = models.CharField(max_length=255, db_index=True)
    state = models.CharField(
        max_length=16, choices=State.choices, default=State.QUEUED, db_index=True
    )
    queue = models.CharField(max_length=255, blank=True)
    worker = models.CharField(max_length=255, blank=True)
    retries = models.PositiveIntegerField(default=0)
    error_type = models.CharField(max_length=150, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True, db_index=True)
    runtime_seconds = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    revoke_requested_at = models.DateTimeField(null=True, blank=True)
    log_count = models.PositiveIntegerField(default=0)
    logs_truncated = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at", "-id"]


class CeleryTaskLog(models.Model):
    """Redacted task diagnostics, visible only through administrator-only APIs."""

    execution = models.ForeignKey(
        CeleryTaskExecution, on_delete=models.CASCADE, related_name="logs"
    )
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    level = models.PositiveSmallIntegerField(default=20)
    logger_name = models.CharField(max_length=150)
    message = models.TextField()
    attempt = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["id"]
        indexes = [models.Index(fields=["execution", "id"])]

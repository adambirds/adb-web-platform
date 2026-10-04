from __future__ import annotations

from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from apps.core.ownership import OwnershipType
from apps.credentials.models import StoredCredential
from apps.infrastructure.models import InfrastructureResource


class MonitorCheck(models.Model):
    """A scheduled technical-health check attached to one structured resource."""

    class CheckType(models.TextChoices):
        ICMP = "icmp", "ICMP/ping"
        TCP = "tcp", "TCP port"
        HTTP = "http", "HTTP/HTTPS"
        CONTENT = "content", "Expected/forbidden content"
        TLS = "tls", "TLS certificate"
        DNS = "dns", "DNS record"
        CERTIFICATE_EXPIRY = "certificate_expiry", "Stored certificate expiry"
        DOMAIN_EXPIRY = "domain_expiry", "Domain registration expiry"

    class Severity(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        HEALTHY = "healthy", "Healthy"
        DEGRADED = "degraded", "Degraded"
        FAILING = "failing", "Failing"
        PAUSED = "paused", "Paused"

    resource = models.ForeignKey(
        InfrastructureResource,
        on_delete=models.CASCADE,
        related_name="monitor_checks",
    )
    name = models.CharField(max_length=200)
    check_type = models.CharField(max_length=30, choices=CheckType.choices)
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.ERROR,
    )
    enabled = models.BooleanField(default=True, db_index=True)
    target = models.CharField(max_length=500)
    port = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
    )
    expected_value = models.TextField(blank=True)
    forbidden_value = models.TextField(blank=True)
    interval_seconds = models.PositiveIntegerField(
        default=300,
        validators=[MinValueValidator(30)],
    )
    timeout_seconds = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(300)],
    )
    failure_threshold = models.PositiveSmallIntegerField(
        default=3,
        validators=[MinValueValidator(1)],
    )
    recovery_threshold = models.PositiveSmallIntegerField(
        default=2,
        validators=[MinValueValidator(1)],
    )
    expiry_warning_days = models.PositiveSmallIntegerField(
        default=30,
        validators=[MinValueValidator(1)],
    )
    credential = models.ForeignKey(
        StoredCredential,
        on_delete=models.SET_NULL,
        related_name="monitor_checks",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    consecutive_failures = models.PositiveIntegerField(default=0)
    consecutive_successes = models.PositiveIntegerField(default=0)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True, db_index=True)
    last_duration_ms = models.PositiveIntegerField(null=True, blank=True)
    last_message = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["resource__name", "name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["resource", "name"],
                name="unique_monitor_check_name_per_resource",
            )
        ]
        indexes = [
            models.Index(fields=["enabled", "next_run_at"], name="monitor_due_check_idx"),
            models.Index(fields=["resource", "status"], name="monitor_resource_status_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        self.name = self.name.strip()
        self.target = self.target.strip()
        if not self.target:
            raise ValidationError({"target": "A monitoring target is required."})
        if self.resource.lifecycle_status in [
            InfrastructureResource.LifecycleStatus.RETIRED,
            InfrastructureResource.LifecycleStatus.ARCHIVED,
        ]:
            raise ValidationError(
                {"resource": "Monitoring checks require a current infrastructure resource."}
            )
        if self.check_type in [self.CheckType.HTTP, self.CheckType.CONTENT]:
            parsed_target = urlparse(self.target)
            if parsed_target.scheme not in {"http", "https"} or not parsed_target.hostname:
                raise ValidationError(
                    {"target": "HTTP monitoring targets must use http:// or https://."}
                )
        if self.check_type == self.CheckType.DOMAIN_EXPIRY and (
            self.resource.resource_type != InfrastructureResource.ResourceType.DOMAIN
        ):
            raise ValidationError({"resource": "Domain expiry checks require a Domain resource."})
        if self.check_type == self.CheckType.CERTIFICATE_EXPIRY and (
            self.resource.resource_type != InfrastructureResource.ResourceType.TLS_CERTIFICATE
        ):
            raise ValidationError(
                {"resource": "Certificate expiry checks require a TLS Certificate resource."}
            )
        if self.check_type == self.CheckType.TCP and self.port is None:
            raise ValidationError({"port": "TCP checks require a port."})
        if self.check_type == self.CheckType.CONTENT and not (
            self.expected_value.strip() or self.forbidden_value.strip()
        ):
            raise ValidationError(
                {"expected_value": "Content checks require expected or forbidden content."}
            )
        if self.credential_id:
            credential = self.credential
            if credential is None or credential.status != StoredCredential.Status.ACTIVE:
                raise ValidationError({"credential": "Monitoring requires an active credential."})
            if self.resource.ownership_type == OwnershipType.CLIENT and (
                credential.ownership_type != OwnershipType.CLIENT
                or credential.client_id != self.resource.client_id
            ):
                raise ValidationError(
                    {"credential": "Client monitoring can use only that Client's credential."}
                )

    def __str__(self) -> str:
        return f"{self.resource.name}: {self.name}"


class MonitorResult(models.Model):
    """Immutable safe observation produced by one MonitorCheck execution."""

    class Outcome(models.TextChoices):
        SUCCESS = "success", "Success"
        FAILURE = "failure", "Failure"
        ERROR = "error", "Execution error"

    monitor_check = models.ForeignKey(
        MonitorCheck,
        on_delete=models.CASCADE,
        related_name="results",
    )
    outcome = models.CharField(max_length=20, choices=Outcome.choices)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField()
    duration_ms = models.PositiveIntegerField()
    status_code = models.PositiveIntegerField(null=True, blank=True)
    observed_value = models.CharField(max_length=500, blank=True)
    message = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-started_at", "-id"]
        indexes = [
            models.Index(
                fields=["monitor_check", "-started_at"],
                name="monitor_result_history_idx",
            )
        ]

    def clean(self) -> None:
        super().clean()
        if self.finished_at < self.started_at:
            raise ValidationError({"finished_at": "Result finish cannot precede start."})


class MonitorIncident(models.Model):
    """A failure period opened and recovered by threshold-aware result processing."""

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        RESOLVED = "resolved", "Resolved"

    monitor_check = models.ForeignKey(
        MonitorCheck,
        on_delete=models.CASCADE,
        related_name="incidents",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    severity = models.CharField(max_length=20, choices=MonitorCheck.Severity.choices)
    opened_at = models.DateTimeField()
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    failure_count = models.PositiveIntegerField(default=1)
    summary = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["status", "-opened_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["monitor_check"],
                condition=Q(status__in=["open", "acknowledged"]),
                name="unique_active_monitor_incident",
            )
        ]
        indexes = [models.Index(fields=["status", "-opened_at"], name="monitor_incident_idx")]

    def clean(self) -> None:
        super().clean()
        if self.status == self.Status.RESOLVED and self.resolved_at is None:
            raise ValidationError({"resolved_at": "Resolved incidents require a resolution time."})

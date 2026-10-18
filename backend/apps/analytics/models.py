"""Tenant-owned analytics metadata; provider tokens live in the shared Vault."""

from django.conf import settings
from django.db import models
from django.db.models import Q


class Business(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = [("view_report", "Can view analytics reports")]

    def __str__(self) -> str:
        return self.name


class BusinessMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        VIEWER = "viewer", "Viewer"

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="analytics_memberships"
    )
    role = models.CharField(max_length=12, choices=Role.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business", "user"], name="analytics_unique_business_user"
            )
        ]

    def __str__(self) -> str:
        return f"{self.business_id}:{self.user_id}:{self.role}"


class Website(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="websites")
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=253)
    timezone = models.CharField(max_length=64, default="Europe/London")
    is_active = models.BooleanField(default=True)
    tracking_schema = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business", "domain"], name="analytics_unique_business_domain"
            )
        ]

    def __str__(self) -> str:
        return self.name


class GoogleConnection(models.Model):
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="google_connections"
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    credential = models.OneToOneField("credentials.StoredCredential", on_delete=models.PROTECT)
    email = models.EmailField(blank=True)
    subject = models.CharField(max_length=255, blank=True)
    scopes = models.JSONField(default=list)
    status = models.CharField(max_length=24, default="connected")
    expires_at = models.DateTimeField(null=True, blank=True)
    last_validated_at = models.DateTimeField(null=True, blank=True)
    error_code = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Google connection {self.pk} ({self.status})"


class ProviderProperty(models.Model):
    class Provider(models.TextChoices):
        GA4 = "ga4", "Google Analytics 4"
        SEARCH_CONSOLE = "gsc", "Google Search Console"

    website = models.ForeignKey(
        Website, on_delete=models.CASCADE, related_name="provider_properties"
    )
    connection = models.ForeignKey(
        GoogleConnection, on_delete=models.PROTECT, related_name="properties"
    )
    provider = models.CharField(max_length=8, choices=Provider.choices)
    external_id = models.CharField(max_length=512)
    metadata = models.JSONField(default=dict, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    synced_through = models.DateField(null=True, blank=True)
    error_code = models.CharField(max_length=64, blank=True)
    revision = models.PositiveIntegerField(default=0)

    class Meta:
        permissions = [("sync_providerproperty", "Can synchronize analytics properties")]
        constraints = [
            models.UniqueConstraint(
                fields=["website", "provider"], name="analytics_one_property_per_provider"
            )
        ]

    def __str__(self) -> str:
        return f"{self.website_id}:{self.provider}"


class ReportSnapshot(models.Model):
    """Exact provider aggregates for a date window; unique users are never summed across days."""

    property = models.ForeignKey(
        ProviderProperty, on_delete=models.CASCADE, related_name="snapshots"
    )
    report = models.CharField(max_length=32)
    start = models.DateField()
    end = models.DateField()
    payload = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["property", "report", "start", "end"], name="analytics_unique_report_window"
            )
        ]

    def __str__(self) -> str:
        return f"{self.property_id}:{self.report}:{self.start}:{self.end}"


class SyncJob(models.Model):
    property = models.ForeignKey(ProviderProperty, on_delete=models.CASCADE, related_name="jobs")
    start = models.DateField()
    end = models.DateField()
    status = models.CharField(max_length=16, default="queued")
    progress = models.PositiveSmallIntegerField(default=0)
    attempts = models.PositiveSmallIntegerField(default=0)
    error_code = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["property"],
                condition=Q(status__in=["queued", "running", "retrying"]),
                name="analytics_one_active_sync",
            )
        ]

    def __str__(self) -> str:
        return f"Sync {self.pk}: {self.status}"


class EventDefinition(models.Model):
    property = models.ForeignKey(
        ProviderProperty, on_delete=models.CASCADE, related_name="definitions"
    )
    kind = models.CharField(max_length=24)
    external_name = models.CharField(max_length=255)
    payload = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["property", "kind", "external_name"], name="analytics_unique_definition"
            )
        ]

    def __str__(self) -> str:
        return self.external_name


class AnalyticsPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    website = models.ForeignKey(Website, on_delete=models.SET_NULL, null=True, blank=True)
    settings = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"Analytics preferences for {self.user_id}"

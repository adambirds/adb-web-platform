from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from apps.core.ownership import OwnershipType, ownership_constraint, validate_ownership


class InfrastructureTag(models.Model):
    """Reusable tag for grouping and discovering structured technical resources."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    colour = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class InfrastructureResource(models.Model):
    """Shared identity and ownership record for structured technical resources."""

    class ResourceType(models.TextChoices):
        SERVER = "server", "Server"
        NETWORK = "network", "Network"
        SUBNET = "subnet", "Subnet"
        DATABASE_INSTANCE = "database_instance", "Database instance"
        LOGICAL_DATABASE = "logical_database", "Logical database"
        APPLICATION = "application", "Application"
        APPLICATION_ENVIRONMENT = "application_environment", "Application environment"
        SOURCE_REPOSITORY = "source_repository", "Source repository"
        WEBSITE = "website", "Website"
        WEBSITE_ENDPOINT = "website_endpoint", "Website endpoint"
        DOMAIN = "domain", "Domain"
        DNS_ZONE = "dns_zone", "DNS zone"
        TLS_CERTIFICATE = "tls_certificate", "TLS certificate"
        PROVIDER_ACCOUNT = "provider_account", "Provider account"
        STORAGE = "storage", "Storage"
        BACKUP_PLAN = "backup_plan", "Backup plan"
        CONTAINER_STACK = "container_stack", "Container stack"
        KUBERNETES_CLUSTER = "kubernetes_cluster", "Kubernetes cluster"
        KUBERNETES_NAMESPACE = "kubernetes_namespace", "Kubernetes namespace"
        KUBERNETES_WORKLOAD = "kubernetes_workload", "Kubernetes workload"
        SYSTEM_SERVICE = "system_service", "System service"
        SCHEDULED_JOB = "scheduled_job", "Scheduled job"
        API = "api", "API"
        BOT = "bot", "Bot"
        MOBILE_APP = "mobile_app", "Mobile app"
        LICENCE = "licence", "Licence"
        EMAIL_SYSTEM = "email_system", "Email system"
        NETWORK_DEVICE = "network_device", "Network device"
        OTHER = "other", "Other"

    class LifecycleStatus(models.TextChoices):
        PLANNED = "planned", "Planned"
        ACTIVE = "active", "Active"
        MAINTENANCE = "maintenance", "Maintenance"
        DEPRECATED = "deprecated", "Deprecated"
        RETIRED = "retired", "Retired"
        ARCHIVED = "archived", "Archived"

    class Environment(models.TextChoices):
        PRODUCTION = "production", "Production"
        STAGING = "staging", "Staging"
        DEVELOPMENT = "development", "Development"
        TESTING = "testing", "Testing"
        SHARED = "shared", "Shared"
        NOT_APPLICABLE = "not_applicable", "Not applicable"

    class Criticality(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    ownership_type = models.CharField(
        max_length=20,
        choices=OwnershipType.choices,
        default=OwnershipType.INTERNAL,
    )
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="infrastructure_resources",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=200)
    resource_type = models.CharField(max_length=50, choices=ResourceType.choices)
    lifecycle_status = models.CharField(
        max_length=30,
        choices=LifecycleStatus.choices,
        default=LifecycleStatus.ACTIVE,
    )
    environment = models.CharField(
        max_length=30,
        choices=Environment.choices,
        default=Environment.NOT_APPLICABLE,
    )
    criticality = models.CharField(
        max_length=20,
        choices=Criticality.choices,
        default=Criticality.NORMAL,
    )
    description = models.TextField(blank=True)
    is_portal_visible = models.BooleanField(
        default=False,
        help_text="Reserved for future client-portal visibility. Private by default.",
    )
    tags = models.ManyToManyField(
        InfrastructureTag,
        related_name="resources",
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="infrastructure_resources_created",
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="infrastructure_resources_updated",
        null=True,
        blank=True,
    )
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [ownership_constraint("infrastructure_resource_valid_ownership")]
        indexes = [
            models.Index(
                fields=["ownership_type", "client", "resource_type"],
                name="infra_res_owner_type_idx",
            ),
            models.Index(
                fields=["lifecycle_status", "resource_type"],
                name="infra_res_lifecycle_idx",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        validate_ownership(self)

    def __str__(self) -> str:
        return self.name


class ServiceProvider(models.Model):
    """Reusable external or internal provider/vendor catalogue entry."""

    class Category(models.TextChoices):
        CLOUD = "cloud", "Cloud"
        HOSTING = "hosting", "Hosting"
        REGISTRAR = "registrar", "Registrar"
        DNS = "dns", "DNS"
        CDN = "cdn", "CDN"
        SAAS = "saas", "SaaS"
        SOURCE_CONTROL = "source_control", "Source control"
        MONITORING = "monitoring", "Monitoring"
        HARDWARE = "hardware", "Hardware"
        OTHER = "other", "Other"

    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.CharField(max_length=30, choices=Category.choices)
    website_url = models.URLField(blank=True)
    support_url = models.URLField(blank=True)
    status_page_url = models.URLField(blank=True)
    documentation_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ProviderAccount(models.Model):
    """Structured account/tenant held with a service provider."""

    resource = models.OneToOneField(
        InfrastructureResource,
        on_delete=models.CASCADE,
        related_name="provider_account",
    )
    provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.PROTECT,
        related_name="accounts",
    )
    account_identifier = models.CharField(max_length=200, blank=True)
    tenant_id = models.CharField(max_length=200, blank=True)
    project_id = models.CharField(max_length=200, blank=True)
    portal_url = models.URLField(blank=True)
    default_region = models.CharField(max_length=100, blank=True)
    support_plan = models.CharField(max_length=100, blank=True)
    billing_reference = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["resource__name"]

    def clean(self) -> None:
        super().clean()
        if (
            self.resource_id
            and self.resource.resource_type != InfrastructureResource.ResourceType.PROVIDER_ACCOUNT
        ):
            raise ValidationError(
                {"resource": "Provider accounts require a provider-account resource."}
            )

    def __str__(self) -> str:
        return f"{self.resource.name} ({self.provider.name})"


class ResourceRelationship(models.Model):
    """Typed directed relationship between two structured resources."""

    class RelationshipType(models.TextChoices):
        DEPENDS_ON = "depends_on", "Depends on"
        HOSTED_ON = "hosted_on", "Hosted on"
        CONNECTS_TO = "connects_to", "Connects to"
        MANAGED_BY = "managed_by", "Managed by"
        BACKED_UP_TO = "backed_up_to", "Backed up to"
        PROTECTED_BY = "protected_by", "Protected by"
        ROUTES_TO = "routes_to", "Routes to"
        USES = "uses", "Uses"
        CONTAINS = "contains", "Contains"
        RELATED_TO = "related_to", "Related to"

    source_resource = models.ForeignKey(
        InfrastructureResource,
        on_delete=models.CASCADE,
        related_name="outgoing_relationships",
    )
    target_resource = models.ForeignKey(
        InfrastructureResource,
        on_delete=models.CASCADE,
        related_name="incoming_relationships",
    )
    relationship_type = models.CharField(max_length=30, choices=RelationshipType.choices)
    label = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="infrastructure_relationships_created",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["source_resource__name", "target_resource__name", "id"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(source_resource=F("target_resource")),
                name="infrastructure_relationship_not_self",
            ),
            models.UniqueConstraint(
                fields=["source_resource", "target_resource", "relationship_type"],
                name="unique_infrastructure_resource_relationship",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        if not self.source_resource_id or not self.target_resource_id:
            return
        if self.source_resource_id == self.target_resource_id:
            raise ValidationError("A resource cannot be related to itself.")

        source = self.source_resource
        target = self.target_resource
        if (
            source.ownership_type == OwnershipType.CLIENT
            and target.ownership_type == OwnershipType.CLIENT
            and source.client_id != target.client_id
        ):
            raise ValidationError(
                "Client-owned resources cannot be related across different clients."
            )

    def __str__(self) -> str:
        return (
            f"{self.source_resource} {self.get_relationship_type_display().lower()} "
            f"{self.target_resource}"
        )

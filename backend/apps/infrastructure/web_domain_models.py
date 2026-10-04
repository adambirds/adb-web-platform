from __future__ import annotations

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from apps.core.ownership import OwnershipType

from .data_application_models import ApplicationEnvironment
from .resource_models import InfrastructureResource, ProviderAccount


def _validate_resource_type(
    resource: InfrastructureResource,
    expected_type: str,
    label: str,
) -> None:
    if resource.resource_type != expected_type:
        raise ValidationError(
            {"resource": f"{label} requires an InfrastructureResource of type '{expected_type}'."}
        )


def _validate_resource_boundary(
    source: InfrastructureResource,
    target: InfrastructureResource,
    field_name: str,
) -> None:
    if (
        source.ownership_type == OwnershipType.CLIENT
        and target.ownership_type == OwnershipType.CLIENT
        and source.client_id != target.client_id
    ):
        raise ValidationError(
            {field_name: "Client-owned infrastructure cannot reference another Client's resource."}
        )


def _validate_parent_boundary(
    child: InfrastructureResource,
    parent: InfrastructureResource,
    field_name: str,
) -> None:
    _validate_resource_boundary(child, parent, field_name)
    if (
        child.ownership_type == OwnershipType.INTERNAL
        and parent.ownership_type == OwnershipType.CLIENT
    ):
        raise ValidationError(
            {field_name: "Internal infrastructure cannot belong to a Client-owned parent resource."}
        )


def _normalise_dns_name(value: str) -> str:
    return value.strip().rstrip(".").lower()


class WebsiteProfile(models.Model):
    """Logical website or web property attached to a structured Website resource."""

    class WebsiteType(models.TextChoices):
        MARKETING = "marketing", "Marketing site"
        WEB_APP = "web_app", "Web application"
        ECOMMERCE = "ecommerce", "E-commerce"
        CMS = "cms", "CMS site"
        PORTAL = "portal", "Portal"
        STATIC = "static", "Static site"
        OTHER = "other", "Other"

    resource = models.OneToOneField(
        InfrastructureResource,
        on_delete=models.CASCADE,
        related_name="website_profile",
    )
    website_type = models.CharField(
        max_length=30,
        choices=WebsiteType.choices,
        default=WebsiteType.WEB_APP,
    )
    admin_url = models.URLField(blank=True)
    cms = models.CharField(max_length=100, blank=True)
    cms_version = models.CharField(max_length=100, blank=True)
    hosting_provider_account = models.ForeignKey(
        ProviderAccount,
        on_delete=models.SET_NULL,
        related_name="hosted_websites",
        null=True,
        blank=True,
    )
    cdn_provider_account = models.ForeignKey(
        ProviderAccount,
        on_delete=models.SET_NULL,
        related_name="cdn_websites",
        null=True,
        blank=True,
    )
    waf_provider_account = models.ForeignKey(
        ProviderAccount,
        on_delete=models.SET_NULL,
        related_name="waf_websites",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["resource__name", "id"]

    def clean(self) -> None:
        super().clean()
        if not self.resource_id:
            return
        _validate_resource_type(
            self.resource,
            InfrastructureResource.ResourceType.WEBSITE,
            "Website",
        )
        for field_name in (
            "hosting_provider_account",
            "cdn_provider_account",
            "waf_provider_account",
        ):
            account = getattr(self, field_name)
            if account is not None:
                _validate_resource_boundary(self.resource, account.resource, field_name)

    def __str__(self) -> str:
        return self.resource.name


class DomainProfile(models.Model):
    """Registered or managed DNS domain attached to a structured Domain resource."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PENDING = "pending", "Pending"
        TRANSFERRING = "transferring", "Transferring"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"
        UNKNOWN = "unknown", "Unknown"

    resource = models.OneToOneField(
        InfrastructureResource,
        on_delete=models.CASCADE,
        related_name="domain_profile",
    )
    domain_name = models.CharField(max_length=253, unique=True)
    registrar_account = models.ForeignKey(
        ProviderAccount,
        on_delete=models.SET_NULL,
        related_name="registered_domains",
        null=True,
        blank=True,
    )
    provider_domain_id = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNKNOWN)
    registered_on = models.DateField(null=True, blank=True)
    expires_on = models.DateField(null=True, blank=True)
    auto_renew = models.BooleanField(null=True, blank=True)
    transfer_lock_enabled = models.BooleanField(null=True, blank=True)
    privacy_enabled = models.BooleanField(null=True, blank=True)
    last_metadata_checked_at = models.DateTimeField(null=True, blank=True)
    metadata_refresh_error = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["domain_name", "id"]

    def clean(self) -> None:
        super().clean()
        self.domain_name = _normalise_dns_name(self.domain_name)
        if self.resource_id:
            _validate_resource_type(
                self.resource,
                InfrastructureResource.ResourceType.DOMAIN,
                "Domain",
            )
        if self.resource_id and self.registrar_account is not None:
            _validate_resource_boundary(
                self.resource,
                self.registrar_account.resource,
                "registrar_account",
            )
        if self.registered_on and self.expires_on and self.expires_on < self.registered_on:
            raise ValidationError({"expires_on": "Domain expiry cannot precede registration."})

    def __str__(self) -> str:
        return self.domain_name


class DNSZone(models.Model):
    """Authoritative DNS zone associated with a Domain."""

    resource = models.OneToOneField(
        InfrastructureResource,
        on_delete=models.CASCADE,
        related_name="dns_zone",
    )
    domain = models.ForeignKey(
        DomainProfile,
        on_delete=models.CASCADE,
        related_name="dns_zones",
    )
    provider_account = models.ForeignKey(
        ProviderAccount,
        on_delete=models.SET_NULL,
        related_name="dns_zones",
        null=True,
        blank=True,
    )
    zone_name = models.CharField(max_length=253)
    provider_zone_id = models.CharField(max_length=200, blank=True)
    dnssec_enabled = models.BooleanField(null=True, blank=True)
    is_primary = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["zone_name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["domain", "zone_name"],
                name="unique_dns_zone_name_per_domain",
            ),
            models.UniqueConstraint(
                fields=["domain"],
                condition=Q(is_primary=True),
                name="unique_primary_dns_zone",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.zone_name = _normalise_dns_name(self.zone_name)
        if self.resource_id:
            _validate_resource_type(
                self.resource,
                InfrastructureResource.ResourceType.DNS_ZONE,
                "DNS zone",
            )
        if self.resource_id and self.domain_id:
            _validate_parent_boundary(self.resource, self.domain.resource, "domain")
        if self.resource_id and self.provider_account is not None:
            _validate_resource_boundary(
                self.resource,
                self.provider_account.resource,
                "provider_account",
            )

    def __str__(self) -> str:
        return self.zone_name


class DNSRecord(models.Model):
    """Individual DNS record within a DNSZone; records are not resource-backed."""

    class RecordType(models.TextChoices):
        A = "A", "A"
        AAAA = "AAAA", "AAAA"
        CNAME = "CNAME", "CNAME"
        MX = "MX", "MX"
        TXT = "TXT", "TXT"
        NS = "NS", "NS"
        SRV = "SRV", "SRV"
        CAA = "CAA", "CAA"
        PTR = "PTR", "PTR"
        ALIAS = "ALIAS", "ALIAS"
        OTHER = "OTHER", "Other"

    zone = models.ForeignKey(DNSZone, on_delete=models.CASCADE, related_name="records")
    name = models.CharField(max_length=253)
    record_type = models.CharField(max_length=10, choices=RecordType.choices)
    value = models.TextField()
    ttl = models.PositiveIntegerField(default=300, validators=[MinValueValidator(1)])
    priority = models.PositiveIntegerField(null=True, blank=True)
    weight = models.PositiveIntegerField(null=True, blank=True)
    port = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
    )
    proxied = models.BooleanField(null=True, blank=True)
    provider_record_id = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["zone__zone_name", "name", "record_type", "id"]
        indexes = [
            models.Index(fields=["zone", "name", "record_type"], name="infra_dns_record_idx")
        ]

    def clean(self) -> None:
        super().clean()
        if self.name != "@":
            self.name = _normalise_dns_name(self.name)
        if self.record_type == self.RecordType.MX and self.priority is None:
            raise ValidationError({"priority": "MX records require a priority."})
        if self.record_type == self.RecordType.SRV:
            missing = [
                field_name
                for field_name in ("priority", "weight", "port")
                if getattr(self, field_name) is None
            ]
            if missing:
                raise ValidationError(
                    dict.fromkeys(
                        missing,
                        "SRV records require priority, weight and port.",
                    )
                )

    def __str__(self) -> str:
        return f"{self.name} {self.record_type} {self.value}"


class TLSCertificate(models.Model):
    """Non-secret TLS certificate metadata attached to a structured TLS resource."""

    class CertificateType(models.TextChoices):
        MANAGED = "managed", "Managed"
        ACME = "acme", "ACME"
        IMPORTED = "imported", "Imported"
        SELF_SIGNED = "self_signed", "Self-signed"
        OTHER = "other", "Other"

    resource = models.OneToOneField(
        InfrastructureResource,
        on_delete=models.CASCADE,
        related_name="tls_certificate",
    )
    provider_account = models.ForeignKey(
        ProviderAccount,
        on_delete=models.SET_NULL,
        related_name="tls_certificates",
        null=True,
        blank=True,
    )
    certificate_type = models.CharField(
        max_length=20,
        choices=CertificateType.choices,
        default=CertificateType.MANAGED,
    )
    issuer = models.CharField(max_length=255, blank=True)
    subject_common_name = models.CharField(max_length=253, blank=True)
    provider_certificate_id = models.CharField(max_length=200, blank=True)
    serial_number = models.CharField(max_length=200, blank=True)
    fingerprint_sha256 = models.CharField(max_length=95, blank=True)
    issued_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(null=True, blank=True)
    metadata_source = models.CharField(max_length=500, blank=True)
    last_metadata_checked_at = models.DateTimeField(null=True, blank=True)
    metadata_refresh_error = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["resource__name", "id"]
        indexes = [models.Index(fields=["expires_at"], name="infra_tls_expiry_idx")]

    def clean(self) -> None:
        super().clean()
        if self.resource_id:
            _validate_resource_type(
                self.resource,
                InfrastructureResource.ResourceType.TLS_CERTIFICATE,
                "TLS certificate",
            )
        if self.resource_id and self.provider_account is not None:
            _validate_resource_boundary(
                self.resource,
                self.provider_account.resource,
                "provider_account",
            )
        if self.issued_at and self.expires_at and self.expires_at <= self.issued_at:
            raise ValidationError({"expires_at": "TLS expiry must be after the issue time."})

    def __str__(self) -> str:
        return self.resource.name


class TLSCertificateDomain(models.Model):
    """Domain coverage carried by a TLS certificate without storing key material."""

    certificate = models.ForeignKey(
        TLSCertificate,
        on_delete=models.CASCADE,
        related_name="domain_links",
    )
    domain = models.ForeignKey(
        DomainProfile,
        on_delete=models.CASCADE,
        related_name="tls_certificate_links",
    )
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["certificate__resource__name", "domain__domain_name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["certificate", "domain"],
                name="unique_tls_certificate_domain",
            ),
            models.UniqueConstraint(
                fields=["certificate"],
                condition=Q(is_primary=True),
                name="unique_primary_tls_domain",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        if self.certificate_id and self.domain_id:
            _validate_resource_boundary(
                self.certificate.resource,
                self.domain.resource,
                "domain",
            )

    def __str__(self) -> str:
        return f"{self.certificate.resource.name} -> {self.domain.domain_name}"


class WebsiteEndpoint(models.Model):
    """Concrete URL/endpoint belonging to a logical Website."""

    class Role(models.TextChoices):
        PRIMARY = "primary", "Primary"
        ALIAS = "alias", "Alias"
        STAGING = "staging", "Staging"
        DEVELOPMENT = "development", "Development"
        ADMIN = "admin", "Admin"
        API = "api", "API"
        HEALTH = "health", "Health"
        OTHER = "other", "Other"

    resource = models.OneToOneField(
        InfrastructureResource,
        on_delete=models.CASCADE,
        related_name="website_endpoint",
    )
    website = models.ForeignKey(
        WebsiteProfile,
        on_delete=models.CASCADE,
        related_name="endpoints",
    )
    application_environment = models.ForeignKey(
        ApplicationEnvironment,
        on_delete=models.SET_NULL,
        related_name="website_endpoints",
        null=True,
        blank=True,
    )
    domain = models.ForeignKey(
        DomainProfile,
        on_delete=models.SET_NULL,
        related_name="website_endpoints",
        null=True,
        blank=True,
    )
    tls_certificate = models.ForeignKey(
        TLSCertificate,
        on_delete=models.SET_NULL,
        related_name="website_endpoints",
        null=True,
        blank=True,
    )
    url = models.URLField(max_length=500)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PRIMARY)
    is_primary = models.BooleanField(default=False)
    redirects_to = models.URLField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["website__resource__name", "role", "url", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["website", "url"],
                name="unique_website_endpoint_url",
            ),
            models.UniqueConstraint(
                fields=["website"],
                condition=Q(is_primary=True),
                name="unique_primary_website_endpoint",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        if self.resource_id:
            _validate_resource_type(
                self.resource,
                InfrastructureResource.ResourceType.WEBSITE_ENDPOINT,
                "Website endpoint",
            )
        if self.resource_id and self.website_id:
            _validate_parent_boundary(self.resource, self.website.resource, "website")
        if self.resource_id and self.application_environment is not None:
            _validate_resource_boundary(
                self.resource,
                self.application_environment.resource,
                "application_environment",
            )
        if self.resource_id and self.domain is not None:
            _validate_resource_boundary(self.resource, self.domain.resource, "domain")
        if self.resource_id and self.tls_certificate is not None:
            _validate_resource_boundary(
                self.resource,
                self.tls_certificate.resource,
                "tls_certificate",
            )

    def __str__(self) -> str:
        return self.url

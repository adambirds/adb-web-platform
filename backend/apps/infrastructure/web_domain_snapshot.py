from __future__ import annotations

from typing import Any

from .models import (
    DNSZone,
    DomainProfile,
    InfrastructureResource,
    TLSCertificate,
    WebsiteEndpoint,
    WebsiteProfile,
)
from .snapshot_types import SpecialistField, SpecialistFieldKind


def _value(value: Any) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _field(
    key: str,
    label: str,
    value: Any,
    kind: SpecialistFieldKind = "text",
) -> SpecialistField | None:
    rendered = _value(value)
    if not rendered:
        return None
    return SpecialistField(key=key, label=label, value=rendered, kind=kind)


def _fields(*fields: SpecialistField | None) -> tuple[SpecialistField, ...]:
    return tuple(field for field in fields if field is not None)


def _website_fields(resource: InfrastructureResource) -> tuple[SpecialistField, ...]:
    website = (
        WebsiteProfile.objects.select_related(
            "hosting_provider_account__resource",
            "hosting_provider_account__provider",
            "cdn_provider_account__resource",
            "cdn_provider_account__provider",
            "waf_provider_account__resource",
            "waf_provider_account__provider",
        )
        .prefetch_related(
            "endpoints__resource",
            "endpoints__domain__resource",
            "endpoints__application_environment__resource",
        )
        .filter(resource=resource)
        .first()
    )
    if website is None:
        return ()

    endpoint_rows: list[str] = []
    for endpoint in website.endpoints.all():
        parts = [endpoint.get_role_display(), endpoint.url]
        if endpoint.is_primary:
            parts.append("Primary")
        if endpoint.domain:
            parts.append(endpoint.domain.domain_name)
        endpoint_rows.append(" · ".join(parts))

    hosting = website.hosting_provider_account
    cdn = website.cdn_provider_account
    waf = website.waf_provider_account
    return _fields(
        _field("website_type", "Website type", website.get_website_type_display()),
        _field("admin_url", "Admin URL", website.admin_url, "url"),
        _field("cms", "CMS", website.cms),
        _field("cms_version", "CMS version", website.cms_version, "code"),
        _field(
            "hosting_provider_account",
            "Hosting provider account",
            hosting.resource.name if hosting else "",
        ),
        _field("hosting_provider", "Hosting provider", hosting.provider.name if hosting else ""),
        _field(
            "cdn_provider_account",
            "CDN provider account",
            cdn.resource.name if cdn else "",
        ),
        _field("cdn_provider", "CDN provider", cdn.provider.name if cdn else ""),
        _field(
            "waf_provider_account",
            "WAF provider account",
            waf.resource.name if waf else "",
        ),
        _field("waf_provider", "WAF provider", waf.provider.name if waf else ""),
        _field("endpoints", "Website endpoints", "\n".join(endpoint_rows), "multiline"),
    )


def _website_endpoint_fields(
    resource: InfrastructureResource,
) -> tuple[SpecialistField, ...]:
    endpoint = (
        WebsiteEndpoint.objects.select_related(
            "website__resource",
            "application_environment__resource",
            "domain__resource",
            "tls_certificate__resource",
        )
        .filter(resource=resource)
        .first()
    )
    if endpoint is None:
        return ()
    return _fields(
        _field("website", "Website", endpoint.website.resource.name),
        _field("url", "URL", endpoint.url, "url"),
        _field("role", "Endpoint role", endpoint.get_role_display()),
        _field("is_primary", "Primary endpoint", endpoint.is_primary),
        _field(
            "application_environment",
            "Application environment",
            endpoint.application_environment.resource.name
            if endpoint.application_environment
            else "",
        ),
        _field("domain", "Domain", endpoint.domain.domain_name if endpoint.domain else ""),
        _field(
            "tls_certificate",
            "TLS certificate",
            endpoint.tls_certificate.resource.name if endpoint.tls_certificate else "",
        ),
        _field("redirects_to", "Redirect target", endpoint.redirects_to, "url"),
    )


def _domain_fields(resource: InfrastructureResource) -> tuple[SpecialistField, ...]:
    domain = (
        DomainProfile.objects.select_related(
            "registrar_account__resource",
            "registrar_account__provider",
        )
        .filter(resource=resource)
        .first()
    )
    if domain is None:
        return ()
    registrar = domain.registrar_account
    return _fields(
        _field("domain_name", "Domain", domain.domain_name, "code"),
        _field(
            "registrar_account",
            "Registrar account",
            registrar.resource.name if registrar else "",
        ),
        _field("registrar", "Registrar", registrar.provider.name if registrar else ""),
        _field("provider_domain_id", "Provider domain ID", domain.provider_domain_id, "code"),
        _field("status", "Registration status", domain.get_status_display()),
        _field("registered_on", "Registered", domain.registered_on),
        _field(
            "last_metadata_checked_at", "Metadata last checked", domain.last_metadata_checked_at
        ),
        _field("metadata_refresh_error", "Metadata refresh error", domain.metadata_refresh_error),
        _field("expires_on", "Expires", domain.expires_on),
        _field("auto_renew", "Auto-renew", domain.auto_renew),
        _field("transfer_lock_enabled", "Transfer lock", domain.transfer_lock_enabled),
        _field("privacy_enabled", "WHOIS privacy", domain.privacy_enabled),
    )


def _dns_zone_fields(resource: InfrastructureResource) -> tuple[SpecialistField, ...]:
    zone = (
        DNSZone.objects.select_related(
            "domain__resource",
            "provider_account__resource",
            "provider_account__provider",
        )
        .prefetch_related("records")
        .filter(resource=resource)
        .first()
    )
    if zone is None:
        return ()
    provider = zone.provider_account
    record_rows = [
        f"{record.name} · {record.record_type} · {record.value} · TTL {record.ttl}"
        for record in zone.records.all()
    ]
    return _fields(
        _field("domain", "Domain", zone.domain.domain_name, "code"),
        _field("zone_name", "Zone", zone.zone_name, "code"),
        _field(
            "provider_account",
            "DNS provider account",
            provider.resource.name if provider else "",
        ),
        _field("provider", "DNS provider", provider.provider.name if provider else ""),
        _field("provider_zone_id", "Provider zone ID", zone.provider_zone_id, "code"),
        _field("dnssec_enabled", "DNSSEC", zone.dnssec_enabled),
        _field("is_primary", "Primary zone", zone.is_primary),
        _field("records", "DNS records", "\n".join(record_rows), "multiline"),
    )


def _tls_certificate_fields(
    resource: InfrastructureResource,
) -> tuple[SpecialistField, ...]:
    certificate = (
        TLSCertificate.objects.select_related(
            "provider_account__resource",
            "provider_account__provider",
        )
        .prefetch_related("domain_links__domain__resource")
        .filter(resource=resource)
        .first()
    )
    if certificate is None:
        return ()
    provider = certificate.provider_account
    covered_domains = [
        f"{link.domain.domain_name}{' · Primary' if link.is_primary else ''}"
        for link in certificate.domain_links.all()
    ]
    return _fields(
        _field("certificate_type", "Certificate type", certificate.get_certificate_type_display()),
        _field(
            "provider_account",
            "TLS provider account",
            provider.resource.name if provider else "",
        ),
        _field("provider", "TLS provider", provider.provider.name if provider else ""),
        _field("issuer", "Issuer", certificate.issuer),
        _field(
            "subject_common_name", "Subject common name", certificate.subject_common_name, "code"
        ),
        _field(
            "provider_certificate_id",
            "Provider certificate ID",
            certificate.provider_certificate_id,
            "code",
        ),
        _field("serial_number", "Serial number", certificate.serial_number, "code"),
        _field("fingerprint_sha256", "SHA-256 fingerprint", certificate.fingerprint_sha256, "code"),
        _field("issued_at", "Issued", certificate.issued_at),
        _field(
            "last_metadata_checked_at",
            "Metadata last checked",
            certificate.last_metadata_checked_at,
        ),
        _field(
            "metadata_refresh_error", "Metadata refresh error", certificate.metadata_refresh_error
        ),
        _field("metadata_source", "Metadata source", certificate.metadata_source, "url"),
        _field("expires_at", "Expires", certificate.expires_at),
        _field("auto_renew", "Auto-renew", certificate.auto_renew),
        _field("domains", "Covered domains", "\n".join(covered_domains), "multiline"),
    )


def web_domain_resource_snapshot(
    resource: InfrastructureResource,
) -> tuple[SpecialistField, ...]:
    """Return safe native web/domain/DNS/TLS specialist fields for one resource."""

    if resource.resource_type == InfrastructureResource.ResourceType.WEBSITE:
        return _website_fields(resource)
    if resource.resource_type == InfrastructureResource.ResourceType.WEBSITE_ENDPOINT:
        return _website_endpoint_fields(resource)
    if resource.resource_type == InfrastructureResource.ResourceType.DOMAIN:
        return _domain_fields(resource)
    if resource.resource_type == InfrastructureResource.ResourceType.DNS_ZONE:
        return _dns_zone_fields(resource)
    if resource.resource_type == InfrastructureResource.ResourceType.TLS_CERTIFICATE:
        return _tls_certificate_fields(resource)
    return ()

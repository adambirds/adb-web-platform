from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Prefetch
from django.http import HttpRequest
from ninja import Router

from apps.access_control.policies import scope_clients_for_user
from apps.clients.models import Client
from apps.core.models import AuditEvent
from apps.infrastructure.models import (
    ApplicationEnvironment,
    DNSRecord,
    DNSZone,
    DomainProfile,
    InfrastructureResource,
    ProviderAccount,
    TLSCertificate,
    TLSCertificateDomain,
    WebsiteEndpoint,
    WebsiteProfile,
)
from apps.infrastructure.policies import scope_infrastructure_resources_for_user
from authentication.ninja.schemas import ProblemDetail

from .specialist_schemas import ClientOptionOut, ProviderAccountOptionOut
from .specialist_views import (
    CURRENT_LIFECYCLE_STATUSES,
    StaffProblem,
    _archive_resource,
    _new_resource,
    _permission_problem,
    _problem,
    _update_resource,
    _validation_problem,
)
from .web_domain_schemas import (
    ApplicationEnvironmentOptionOut,
    DNSRecordCreateIn,
    DNSRecordOut,
    DNSRecordUpdateIn,
    DNSZoneCreateIn,
    DNSZoneOut,
    DNSZoneUpdateIn,
    DomainCreateIn,
    DomainOptionOut,
    DomainOut,
    DomainUpdateIn,
    TLSCertificateCreateIn,
    TLSCertificateDomainCreateIn,
    TLSCertificateDomainOut,
    TLSCertificateOptionOut,
    TLSCertificateOut,
    TLSCertificateUpdateIn,
    WebDomainSpecialistOptionsOut,
    WebsiteCreateIn,
    WebsiteEndpointCreateIn,
    WebsiteEndpointOut,
    WebsiteEndpointUpdateIn,
    WebsiteOptionOut,
    WebsiteOut,
    WebsiteUpdateIn,
)

web_domain_specialist_router = Router(tags=["admin-infrastructure-web-domains"])


def _visible_queryset(request: HttpRequest) -> Any:
    return scope_infrastructure_resources_for_user(request.user)


def _visible_resource_ids(request: HttpRequest) -> set[int]:
    return set(_visible_queryset(request).values_list("id", flat=True))


def _visible_provider_account(
    request: HttpRequest,
    resource_id: int | None,
) -> ProviderAccount | None:
    if resource_id is None:
        return None
    return (
        ProviderAccount.objects.select_related("resource", "resource__client", "provider")
        .filter(resource__in=_visible_queryset(request), resource_id=resource_id)
        .first()
    )


def _visible_application_environment(
    request: HttpRequest,
    resource_id: int | None,
) -> ApplicationEnvironment | None:
    if resource_id is None:
        return None
    return (
        ApplicationEnvironment.objects.select_related(
            "resource",
            "resource__client",
            "application__resource",
        )
        .filter(resource__in=_visible_queryset(request), resource_id=resource_id)
        .first()
    )


def _endpoint_queryset(request: HttpRequest) -> Any:
    visible = _visible_queryset(request)
    return WebsiteEndpoint.objects.select_related(
        "resource",
        "resource__client",
        "website__resource",
        "application_environment__resource",
        "domain__resource",
        "tls_certificate__resource",
    ).filter(resource__in=visible)


def _website_queryset(request: HttpRequest) -> Any:
    visible = _visible_queryset(request)
    endpoints = WebsiteEndpoint.objects.select_related(
        "resource",
        "resource__client",
        "application_environment__resource",
        "domain__resource",
        "tls_certificate__resource",
    ).filter(resource__in=visible)
    return (
        WebsiteProfile.objects.select_related(
            "resource",
            "resource__client",
            "hosting_provider_account__resource",
            "cdn_provider_account__resource",
            "waf_provider_account__resource",
        )
        .prefetch_related(Prefetch("endpoints", queryset=endpoints))
        .filter(resource__in=visible)
    )


def _visible_website(request: HttpRequest, resource_id: int | None) -> WebsiteProfile | None:
    if resource_id is None:
        return None
    return _website_queryset(request).filter(resource_id=resource_id).first()


def _visible_domain(request: HttpRequest, resource_id: int | None) -> DomainProfile | None:
    if resource_id is None:
        return None
    return (
        DomainProfile.objects.select_related(
            "resource",
            "resource__client",
            "registrar_account__resource",
            "registrar_account__provider",
        )
        .filter(resource__in=_visible_queryset(request), resource_id=resource_id)
        .first()
    )


def _dns_zone_queryset(request: HttpRequest) -> Any:
    return (
        DNSZone.objects.select_related(
            "resource",
            "resource__client",
            "domain__resource",
            "provider_account__resource",
            "provider_account__provider",
        )
        .prefetch_related("records")
        .filter(resource__in=_visible_queryset(request))
    )


def _visible_dns_zone(request: HttpRequest, resource_id: int | None) -> DNSZone | None:
    if resource_id is None:
        return None
    return _dns_zone_queryset(request).filter(resource_id=resource_id).first()


def _tls_certificate_queryset(request: HttpRequest) -> Any:
    visible = _visible_queryset(request)
    domain_links = TLSCertificateDomain.objects.select_related("domain__resource").filter(
        domain__resource__in=visible
    )
    return (
        TLSCertificate.objects.select_related(
            "resource",
            "resource__client",
            "provider_account__resource",
            "provider_account__provider",
        )
        .prefetch_related(Prefetch("domain_links", queryset=domain_links))
        .filter(resource__in=visible)
    )


def _visible_tls_certificate(
    request: HttpRequest,
    resource_id: int | None,
) -> TLSCertificate | None:
    if resource_id is None:
        return None
    return _tls_certificate_queryset(request).filter(resource_id=resource_id).first()


def _provider_fields(
    provider_account: ProviderAccount | None,
    visible_ids: set[int],
) -> tuple[int | None, str | None, str | None]:
    if provider_account is None or provider_account.resource_id not in visible_ids:
        return None, None, None
    return (
        provider_account.resource_id,
        provider_account.resource.name,
        provider_account.provider.name,
    )


def _endpoint_out(
    endpoint: WebsiteEndpoint,
    visible_ids: set[int],
) -> WebsiteEndpointOut:
    resource = endpoint.resource
    application_environment = endpoint.application_environment
    domain = endpoint.domain
    certificate = endpoint.tls_certificate
    if application_environment is not None and application_environment.resource_id in visible_ids:
        application_environment_resource_id = application_environment.resource_id
        application_environment_name = application_environment.resource.name
    else:
        application_environment_resource_id = None
        application_environment_name = None
    if domain is not None and domain.resource_id in visible_ids:
        domain_resource_id = domain.resource_id
        domain_name = domain.domain_name
    else:
        domain_resource_id = None
        domain_name = None
    if certificate is not None and certificate.resource_id in visible_ids:
        tls_certificate_resource_id = certificate.resource_id
        tls_certificate_name = certificate.resource.name
    else:
        tls_certificate_resource_id = None
        tls_certificate_name = None
    return WebsiteEndpointOut(
        resource_id=resource.id,
        name=resource.name,
        ownership_type=resource.ownership_type,
        client_id=resource.client_id,
        client_name=str(resource.client) if resource.client else None,
        lifecycle_status=resource.lifecycle_status,
        environment=resource.environment,
        criticality=resource.criticality,
        description=resource.description,
        website_resource_id=endpoint.website.resource_id,
        website_name=endpoint.website.resource.name,
        application_environment_resource_id=application_environment_resource_id,
        application_environment_name=application_environment_name,
        domain_resource_id=domain_resource_id,
        domain_name=domain_name,
        tls_certificate_resource_id=tls_certificate_resource_id,
        tls_certificate_name=tls_certificate_name,
        url=endpoint.url,
        role=endpoint.role,
        is_primary=endpoint.is_primary,
        redirects_to=endpoint.redirects_to,
        updated_at=resource.updated_at,
    )


def _website_out(request: HttpRequest, website: WebsiteProfile) -> WebsiteOut:
    resource = website.resource
    visible_ids = _visible_resource_ids(request)
    hosting_id, hosting_name, _ = _provider_fields(
        website.hosting_provider_account,
        visible_ids,
    )
    cdn_id, cdn_name, _ = _provider_fields(website.cdn_provider_account, visible_ids)
    waf_id, waf_name, _ = _provider_fields(website.waf_provider_account, visible_ids)
    return WebsiteOut(
        resource_id=resource.id,
        name=resource.name,
        ownership_type=resource.ownership_type,
        client_id=resource.client_id,
        client_name=str(resource.client) if resource.client else None,
        lifecycle_status=resource.lifecycle_status,
        environment=resource.environment,
        criticality=resource.criticality,
        description=resource.description,
        website_type=website.website_type,
        admin_url=website.admin_url,
        cms=website.cms,
        cms_version=website.cms_version,
        hosting_provider_account_resource_id=hosting_id,
        hosting_provider_account_name=hosting_name,
        cdn_provider_account_resource_id=cdn_id,
        cdn_provider_account_name=cdn_name,
        waf_provider_account_resource_id=waf_id,
        waf_provider_account_name=waf_name,
        endpoints=[_endpoint_out(item, visible_ids) for item in website.endpoints.all()],
        updated_at=resource.updated_at,
    )


def _domain_out(request: HttpRequest, domain: DomainProfile) -> DomainOut:
    resource = domain.resource
    visible_ids = _visible_resource_ids(request)
    registrar_id, registrar_name, provider_name = _provider_fields(
        domain.registrar_account,
        visible_ids,
    )
    return DomainOut(
        resource_id=resource.id,
        name=resource.name,
        ownership_type=resource.ownership_type,
        client_id=resource.client_id,
        client_name=str(resource.client) if resource.client else None,
        lifecycle_status=resource.lifecycle_status,
        environment=resource.environment,
        criticality=resource.criticality,
        description=resource.description,
        domain_name=domain.domain_name,
        registrar_account_resource_id=registrar_id,
        registrar_account_name=registrar_name,
        registrar_name=provider_name,
        provider_domain_id=domain.provider_domain_id,
        status=domain.status,
        registered_on=domain.registered_on,
        expires_on=domain.expires_on,
        auto_renew=domain.auto_renew,
        transfer_lock_enabled=domain.transfer_lock_enabled,
        privacy_enabled=domain.privacy_enabled,
        updated_at=resource.updated_at,
    )


def _dns_record_out(record: DNSRecord) -> DNSRecordOut:
    return DNSRecordOut(
        id=record.id,
        name=record.name,
        record_type=record.record_type,
        value=record.value,
        ttl=record.ttl,
        priority=record.priority,
        weight=record.weight,
        port=record.port,
        proxied=record.proxied,
        provider_record_id=record.provider_record_id,
    )


def _dns_zone_out(request: HttpRequest, zone: DNSZone) -> DNSZoneOut:
    resource = zone.resource
    visible_ids = _visible_resource_ids(request)
    provider_id, provider_name, service_name = _provider_fields(
        zone.provider_account,
        visible_ids,
    )
    domain_visible = zone.domain.resource_id in visible_ids
    return DNSZoneOut(
        resource_id=resource.id,
        name=resource.name,
        ownership_type=resource.ownership_type,
        client_id=resource.client_id,
        client_name=str(resource.client) if resource.client else None,
        lifecycle_status=resource.lifecycle_status,
        environment=resource.environment,
        criticality=resource.criticality,
        description=resource.description,
        domain_resource_id=zone.domain.resource_id if domain_visible else None,
        domain_name=zone.domain.domain_name if domain_visible else None,
        provider_account_resource_id=provider_id,
        provider_account_name=provider_name,
        provider_name=service_name,
        zone_name=zone.zone_name,
        provider_zone_id=zone.provider_zone_id,
        dnssec_enabled=zone.dnssec_enabled,
        is_primary=zone.is_primary,
        records=[_dns_record_out(item) for item in zone.records.all()],
        updated_at=resource.updated_at,
    )


def _tls_domain_out(link: TLSCertificateDomain) -> TLSCertificateDomainOut:
    return TLSCertificateDomainOut(
        id=link.id,
        domain_resource_id=link.domain.resource_id,
        domain_name=link.domain.domain_name,
        is_primary=link.is_primary,
    )


def _tls_certificate_out(
    request: HttpRequest,
    certificate: TLSCertificate,
) -> TLSCertificateOut:
    resource = certificate.resource
    visible_ids = _visible_resource_ids(request)
    provider_id, provider_name, service_name = _provider_fields(
        certificate.provider_account,
        visible_ids,
    )
    return TLSCertificateOut(
        resource_id=resource.id,
        name=resource.name,
        ownership_type=resource.ownership_type,
        client_id=resource.client_id,
        client_name=str(resource.client) if resource.client else None,
        lifecycle_status=resource.lifecycle_status,
        environment=resource.environment,
        criticality=resource.criticality,
        description=resource.description,
        provider_account_resource_id=provider_id,
        provider_account_name=provider_name,
        provider_name=service_name,
        certificate_type=certificate.certificate_type,
        issuer=certificate.issuer,
        subject_common_name=certificate.subject_common_name,
        provider_certificate_id=certificate.provider_certificate_id,
        serial_number=certificate.serial_number,
        fingerprint_sha256=certificate.fingerprint_sha256,
        issued_at=certificate.issued_at,
        expires_at=certificate.expires_at,
        auto_renew=certificate.auto_renew,
        domains=[_tls_domain_out(item) for item in certificate.domain_links.all()],
        updated_at=resource.updated_at,
    )


def _populate_website(
    website: WebsiteProfile,
    payload: WebsiteCreateIn | WebsiteUpdateIn,
) -> None:
    website.website_type = payload.website_type
    website.admin_url = payload.admin_url.strip()
    website.cms = payload.cms.strip()
    website.cms_version = payload.cms_version.strip()


def _populate_endpoint(
    endpoint: WebsiteEndpoint,
    payload: WebsiteEndpointCreateIn | WebsiteEndpointUpdateIn,
) -> None:
    endpoint.url = payload.url.strip()
    endpoint.role = payload.role
    endpoint.is_primary = payload.is_primary
    endpoint.redirects_to = payload.redirects_to.strip()


def _populate_domain(
    domain: DomainProfile,
    payload: DomainCreateIn | DomainUpdateIn,
) -> None:
    domain.domain_name = payload.domain_name.strip()
    domain.provider_domain_id = payload.provider_domain_id.strip()
    domain.status = payload.status
    domain.registered_on = payload.registered_on
    domain.expires_on = payload.expires_on
    domain.auto_renew = payload.auto_renew
    domain.transfer_lock_enabled = payload.transfer_lock_enabled
    domain.privacy_enabled = payload.privacy_enabled


def _populate_dns_zone(
    zone: DNSZone,
    payload: DNSZoneCreateIn | DNSZoneUpdateIn,
) -> None:
    zone.zone_name = payload.zone_name.strip()
    zone.provider_zone_id = payload.provider_zone_id.strip()
    zone.dnssec_enabled = payload.dnssec_enabled
    zone.is_primary = payload.is_primary


def _populate_dns_record(
    record: DNSRecord,
    payload: DNSRecordCreateIn | DNSRecordUpdateIn,
) -> None:
    record.name = payload.name.strip()
    record.record_type = payload.record_type
    record.value = payload.value.strip()
    record.ttl = payload.ttl
    record.priority = payload.priority
    record.weight = payload.weight
    record.port = payload.port
    record.proxied = payload.proxied
    record.provider_record_id = payload.provider_record_id.strip()


def _populate_tls_certificate(
    certificate: TLSCertificate,
    payload: TLSCertificateCreateIn | TLSCertificateUpdateIn,
) -> None:
    certificate.certificate_type = payload.certificate_type
    certificate.issuer = payload.issuer.strip()
    certificate.subject_common_name = payload.subject_common_name.strip()
    certificate.provider_certificate_id = payload.provider_certificate_id.strip()
    certificate.serial_number = payload.serial_number.strip()
    certificate.fingerprint_sha256 = payload.fingerprint_sha256.strip()
    certificate.issued_at = payload.issued_at
    certificate.expires_at = payload.expires_at
    certificate.auto_renew = payload.auto_renew


@web_domain_specialist_router.get(
    "/infrastructure/web-domain-options",
    response={200: WebDomainSpecialistOptionsOut, 401: ProblemDetail, 403: ProblemDetail},
)
def web_domain_options(
    request: HttpRequest,
) -> WebDomainSpecialistOptionsOut | StaffProblem:
    problem = _permission_problem(request, "infrastructure.view_infrastructureresource")
    if problem:
        return problem
    clients = scope_clients_for_user(request.user, Client.objects.filter(status="active"))
    visible = _visible_queryset(request)
    current = {"resource__lifecycle_status__in": CURRENT_LIFECYCLE_STATUSES}
    provider_accounts = ProviderAccount.objects.select_related(
        "resource", "resource__client", "provider"
    ).filter(resource__in=visible, **current)
    environments = ApplicationEnvironment.objects.select_related(
        "resource", "resource__client", "application__resource"
    ).filter(resource__in=visible, **current)
    websites = WebsiteProfile.objects.select_related("resource", "resource__client").filter(
        resource__in=visible, **current
    )
    domains = DomainProfile.objects.select_related("resource", "resource__client").filter(
        resource__in=visible, **current
    )
    certificates = TLSCertificate.objects.select_related("resource", "resource__client").filter(
        resource__in=visible, **current
    )
    return WebDomainSpecialistOptionsOut(
        clients=[
            ClientOptionOut(id=item.id, name=str(item))
            for item in clients.order_by("company", "name")
        ],
        provider_accounts=[
            ProviderAccountOptionOut(
                resource_id=item.resource_id,
                name=item.resource.name,
                provider_name=item.provider.name,
                ownership_type=item.resource.ownership_type,
                client_id=item.resource.client_id,
                client_name=str(item.resource.client) if item.resource.client else None,
            )
            for item in provider_accounts.order_by("resource__name")
        ],
        application_environments=[
            ApplicationEnvironmentOptionOut(
                resource_id=item.resource_id,
                name=item.resource.name,
                application_name=item.application.resource.name,
                environment=item.resource.environment,
                ownership_type=item.resource.ownership_type,
                client_id=item.resource.client_id,
                client_name=str(item.resource.client) if item.resource.client else None,
            )
            for item in environments.order_by("application__resource__name", "resource__name")
        ],
        websites=[
            WebsiteOptionOut(
                resource_id=item.resource_id,
                name=item.resource.name,
                website_type=item.website_type,
                ownership_type=item.resource.ownership_type,
                client_id=item.resource.client_id,
                client_name=str(item.resource.client) if item.resource.client else None,
            )
            for item in websites.order_by("resource__name")
        ],
        domains=[
            DomainOptionOut(
                resource_id=item.resource_id,
                name=item.resource.name,
                domain_name=item.domain_name,
                ownership_type=item.resource.ownership_type,
                client_id=item.resource.client_id,
                client_name=str(item.resource.client) if item.resource.client else None,
            )
            for item in domains.order_by("domain_name")
        ],
        tls_certificates=[
            TLSCertificateOptionOut(
                resource_id=item.resource_id,
                name=item.resource.name,
                subject_common_name=item.subject_common_name,
                ownership_type=item.resource.ownership_type,
                client_id=item.resource.client_id,
                client_name=str(item.resource.client) if item.resource.client else None,
            )
            for item in certificates.order_by("resource__name")
        ],
    )


@web_domain_specialist_router.post(
    "/infrastructure/websites",
    response={
        201: WebsiteOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def create_website(
    request: HttpRequest,
    payload: WebsiteCreateIn,
) -> tuple[int, WebsiteOut | dict[str, object]]:
    problem = _permission_problem(
        request,
        "infrastructure.add_infrastructureresource",
        "infrastructure.add_websiteprofile",
    )
    if problem:
        return problem
    hosting = _visible_provider_account(request, payload.hosting_provider_account_resource_id)
    cdn = _visible_provider_account(request, payload.cdn_provider_account_resource_id)
    waf = _visible_provider_account(request, payload.waf_provider_account_resource_id)
    if payload.hosting_provider_account_resource_id is not None and hosting is None:
        return _problem(404, "Hosting provider account not found.", "not_found")
    if payload.cdn_provider_account_resource_id is not None and cdn is None:
        return _problem(404, "CDN provider account not found.", "not_found")
    if payload.waf_provider_account_resource_id is not None and waf is None:
        return _problem(404, "WAF provider account not found.", "not_found")
    try:
        with transaction.atomic():
            resource, resource_problem = _new_resource(
                request,
                payload,
                InfrastructureResource.ResourceType.WEBSITE,
            )
            if resource_problem:
                transaction.set_rollback(True)
                return resource_problem
            assert resource is not None
            website = WebsiteProfile(
                resource=resource,
                hosting_provider_account=hosting,
                cdn_provider_account=cdn,
                waf_provider_account=waf,
            )
            _populate_website(website, payload)
            website.full_clean()
            website.save()
    except ValidationError as error:
        return _validation_problem(error)
    created = _visible_website(request, resource.id)
    assert created is not None
    return 201, _website_out(request, created)


@web_domain_specialist_router.put(
    "/infrastructure/websites/{resource_id}",
    response={
        200: WebsiteOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_website(
    request: HttpRequest,
    resource_id: int,
    payload: WebsiteUpdateIn,
) -> WebsiteOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.change_infrastructureresource",
        "infrastructure.change_websiteprofile",
    )
    if problem:
        return problem
    website = _visible_website(request, resource_id)
    if website is None:
        return _problem(404, "Website not found.", "not_found")
    hosting = _visible_provider_account(request, payload.hosting_provider_account_resource_id)
    cdn = _visible_provider_account(request, payload.cdn_provider_account_resource_id)
    waf = _visible_provider_account(request, payload.waf_provider_account_resource_id)
    if payload.hosting_provider_account_resource_id is not None and hosting is None:
        return _problem(404, "Hosting provider account not found.", "not_found")
    if payload.cdn_provider_account_resource_id is not None and cdn is None:
        return _problem(404, "CDN provider account not found.", "not_found")
    if payload.waf_provider_account_resource_id is not None and waf is None:
        return _problem(404, "WAF provider account not found.", "not_found")
    try:
        with transaction.atomic():
            resource_problem = _update_resource(request, website.resource, payload)
            if resource_problem:
                transaction.set_rollback(True)
                return resource_problem
            website.hosting_provider_account = hosting
            website.cdn_provider_account = cdn
            website.waf_provider_account = waf
            _populate_website(website, payload)
            website.full_clean()
            website.save()
    except ValidationError as error:
        return _validation_problem(error)
    refreshed = _visible_website(request, resource_id)
    assert refreshed is not None
    return _website_out(request, refreshed)


@web_domain_specialist_router.post(
    "/infrastructure/websites/{resource_id}/archive",
    response={200: WebsiteOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def archive_website(request: HttpRequest, resource_id: int) -> WebsiteOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.change_infrastructureresource",
        "infrastructure.change_websiteprofile",
    )
    if problem:
        return problem
    website = _visible_website(request, resource_id)
    if website is None:
        return _problem(404, "Website not found.", "not_found")
    _archive_resource(request, website.resource)
    return _website_out(request, website)


@web_domain_specialist_router.post(
    "/infrastructure/website-endpoints",
    response={
        201: WebsiteEndpointOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def create_website_endpoint(
    request: HttpRequest,
    payload: WebsiteEndpointCreateIn,
) -> tuple[int, WebsiteEndpointOut | dict[str, object]]:
    problem = _permission_problem(
        request,
        "infrastructure.add_infrastructureresource",
        "infrastructure.add_websiteendpoint",
    )
    if problem:
        return problem
    website = _visible_website(request, payload.website_resource_id)
    environment = _visible_application_environment(
        request,
        payload.application_environment_resource_id,
    )
    domain = _visible_domain(request, payload.domain_resource_id)
    certificate = _visible_tls_certificate(request, payload.tls_certificate_resource_id)
    if website is None:
        return _problem(404, "Website not found.", "not_found")
    if payload.application_environment_resource_id is not None and environment is None:
        return _problem(404, "Application environment not found.", "not_found")
    if payload.domain_resource_id is not None and domain is None:
        return _problem(404, "Domain not found.", "not_found")
    if payload.tls_certificate_resource_id is not None and certificate is None:
        return _problem(404, "TLS certificate not found.", "not_found")
    try:
        with transaction.atomic():
            resource, resource_problem = _new_resource(
                request,
                payload,
                InfrastructureResource.ResourceType.WEBSITE_ENDPOINT,
            )
            if resource_problem:
                transaction.set_rollback(True)
                return resource_problem
            assert resource is not None
            endpoint = WebsiteEndpoint(
                resource=resource,
                website=website,
                application_environment=environment,
                domain=domain,
                tls_certificate=certificate,
            )
            _populate_endpoint(endpoint, payload)
            endpoint.full_clean()
            endpoint.save()
    except ValidationError as error:
        return _validation_problem(error)
    created = _endpoint_queryset(request).get(resource_id=resource.id)
    return 201, _endpoint_out(created, _visible_resource_ids(request))


@web_domain_specialist_router.put(
    "/infrastructure/website-endpoints/{resource_id}",
    response={
        200: WebsiteEndpointOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_website_endpoint(
    request: HttpRequest,
    resource_id: int,
    payload: WebsiteEndpointUpdateIn,
) -> WebsiteEndpointOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.change_infrastructureresource",
        "infrastructure.change_websiteendpoint",
    )
    if problem:
        return problem
    endpoint = _endpoint_queryset(request).filter(resource_id=resource_id).first()
    if endpoint is None:
        return _problem(404, "Website endpoint not found.", "not_found")
    website = _visible_website(request, payload.website_resource_id)
    environment = _visible_application_environment(
        request,
        payload.application_environment_resource_id,
    )
    domain = _visible_domain(request, payload.domain_resource_id)
    certificate = _visible_tls_certificate(request, payload.tls_certificate_resource_id)
    if website is None:
        return _problem(404, "Website not found.", "not_found")
    if payload.application_environment_resource_id is not None and environment is None:
        return _problem(404, "Application environment not found.", "not_found")
    if payload.domain_resource_id is not None and domain is None:
        return _problem(404, "Domain not found.", "not_found")
    if payload.tls_certificate_resource_id is not None and certificate is None:
        return _problem(404, "TLS certificate not found.", "not_found")
    try:
        with transaction.atomic():
            resource_problem = _update_resource(request, endpoint.resource, payload)
            if resource_problem:
                transaction.set_rollback(True)
                return resource_problem
            endpoint.website = website
            endpoint.application_environment = environment
            endpoint.domain = domain
            endpoint.tls_certificate = certificate
            _populate_endpoint(endpoint, payload)
            endpoint.full_clean()
            endpoint.save()
    except ValidationError as error:
        return _validation_problem(error)
    refreshed = _endpoint_queryset(request).get(resource_id=resource_id)
    return _endpoint_out(refreshed, _visible_resource_ids(request))


@web_domain_specialist_router.post(
    "/infrastructure/website-endpoints/{resource_id}/archive",
    response={200: WebsiteEndpointOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def archive_website_endpoint(
    request: HttpRequest,
    resource_id: int,
) -> WebsiteEndpointOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.change_infrastructureresource",
        "infrastructure.change_websiteendpoint",
    )
    if problem:
        return problem
    endpoint = _endpoint_queryset(request).filter(resource_id=resource_id).first()
    if endpoint is None:
        return _problem(404, "Website endpoint not found.", "not_found")
    if endpoint.is_primary:
        endpoint.is_primary = False
        endpoint.save(update_fields=["is_primary", "updated_at"])
    _archive_resource(request, endpoint.resource)
    return _endpoint_out(endpoint, _visible_resource_ids(request))


@web_domain_specialist_router.post(
    "/infrastructure/domains",
    response={
        201: DomainOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def create_domain(
    request: HttpRequest,
    payload: DomainCreateIn,
) -> tuple[int, DomainOut | dict[str, object]]:
    problem = _permission_problem(
        request,
        "infrastructure.add_infrastructureresource",
        "infrastructure.add_domainprofile",
    )
    if problem:
        return problem
    registrar = _visible_provider_account(request, payload.registrar_account_resource_id)
    if payload.registrar_account_resource_id is not None and registrar is None:
        return _problem(404, "Registrar account not found.", "not_found")
    try:
        with transaction.atomic():
            resource, resource_problem = _new_resource(
                request,
                payload,
                InfrastructureResource.ResourceType.DOMAIN,
            )
            if resource_problem:
                transaction.set_rollback(True)
                return resource_problem
            assert resource is not None
            domain = DomainProfile(resource=resource, registrar_account=registrar)
            _populate_domain(domain, payload)
            domain.full_clean()
            domain.save()
    except ValidationError as error:
        return _validation_problem(error)
    created = _visible_domain(request, resource.id)
    assert created is not None
    return 201, _domain_out(request, created)


@web_domain_specialist_router.put(
    "/infrastructure/domains/{resource_id}",
    response={
        200: DomainOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_domain(
    request: HttpRequest,
    resource_id: int,
    payload: DomainUpdateIn,
) -> DomainOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.change_infrastructureresource",
        "infrastructure.change_domainprofile",
    )
    if problem:
        return problem
    domain = _visible_domain(request, resource_id)
    if domain is None:
        return _problem(404, "Domain not found.", "not_found")
    registrar = _visible_provider_account(request, payload.registrar_account_resource_id)
    if payload.registrar_account_resource_id is not None and registrar is None:
        return _problem(404, "Registrar account not found.", "not_found")
    try:
        with transaction.atomic():
            resource_problem = _update_resource(request, domain.resource, payload)
            if resource_problem:
                transaction.set_rollback(True)
                return resource_problem
            domain.registrar_account = registrar
            _populate_domain(domain, payload)
            domain.full_clean()
            domain.save()
    except ValidationError as error:
        return _validation_problem(error)
    refreshed = _visible_domain(request, resource_id)
    assert refreshed is not None
    return _domain_out(request, refreshed)


@web_domain_specialist_router.post(
    "/infrastructure/domains/{resource_id}/archive",
    response={200: DomainOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def archive_domain(request: HttpRequest, resource_id: int) -> DomainOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.change_infrastructureresource",
        "infrastructure.change_domainprofile",
    )
    if problem:
        return problem
    domain = _visible_domain(request, resource_id)
    if domain is None:
        return _problem(404, "Domain not found.", "not_found")
    _archive_resource(request, domain.resource)
    return _domain_out(request, domain)


@web_domain_specialist_router.post(
    "/infrastructure/dns-zones",
    response={
        201: DNSZoneOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def create_dns_zone(
    request: HttpRequest,
    payload: DNSZoneCreateIn,
) -> tuple[int, DNSZoneOut | dict[str, object]]:
    problem = _permission_problem(
        request,
        "infrastructure.add_infrastructureresource",
        "infrastructure.add_dnszone",
    )
    if problem:
        return problem
    domain = _visible_domain(request, payload.domain_resource_id)
    provider = _visible_provider_account(request, payload.provider_account_resource_id)
    if domain is None:
        return _problem(404, "Domain not found.", "not_found")
    if payload.provider_account_resource_id is not None and provider is None:
        return _problem(404, "DNS provider account not found.", "not_found")
    try:
        with transaction.atomic():
            resource, resource_problem = _new_resource(
                request,
                payload,
                InfrastructureResource.ResourceType.DNS_ZONE,
            )
            if resource_problem:
                transaction.set_rollback(True)
                return resource_problem
            assert resource is not None
            zone = DNSZone(resource=resource, domain=domain, provider_account=provider)
            _populate_dns_zone(zone, payload)
            zone.full_clean()
            zone.save()
    except ValidationError as error:
        return _validation_problem(error)
    created = _visible_dns_zone(request, resource.id)
    assert created is not None
    return 201, _dns_zone_out(request, created)


@web_domain_specialist_router.put(
    "/infrastructure/dns-zones/{resource_id}",
    response={
        200: DNSZoneOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_dns_zone(
    request: HttpRequest,
    resource_id: int,
    payload: DNSZoneUpdateIn,
) -> DNSZoneOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.change_infrastructureresource",
        "infrastructure.change_dnszone",
    )
    if problem:
        return problem
    zone = _visible_dns_zone(request, resource_id)
    if zone is None:
        return _problem(404, "DNS zone not found.", "not_found")
    domain = _visible_domain(request, payload.domain_resource_id)
    provider = _visible_provider_account(request, payload.provider_account_resource_id)
    if domain is None:
        return _problem(404, "Domain not found.", "not_found")
    if payload.provider_account_resource_id is not None and provider is None:
        return _problem(404, "DNS provider account not found.", "not_found")
    try:
        with transaction.atomic():
            resource_problem = _update_resource(request, zone.resource, payload)
            if resource_problem:
                transaction.set_rollback(True)
                return resource_problem
            zone.domain = domain
            zone.provider_account = provider
            _populate_dns_zone(zone, payload)
            zone.full_clean()
            zone.save()
    except ValidationError as error:
        return _validation_problem(error)
    refreshed = _visible_dns_zone(request, resource_id)
    assert refreshed is not None
    return _dns_zone_out(request, refreshed)


@web_domain_specialist_router.post(
    "/infrastructure/dns-zones/{resource_id}/archive",
    response={200: DNSZoneOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def archive_dns_zone(request: HttpRequest, resource_id: int) -> DNSZoneOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.change_infrastructureresource",
        "infrastructure.change_dnszone",
    )
    if problem:
        return problem
    zone = _visible_dns_zone(request, resource_id)
    if zone is None:
        return _problem(404, "DNS zone not found.", "not_found")
    if zone.is_primary:
        zone.is_primary = False
        zone.save(update_fields=["is_primary", "updated_at"])
    _archive_resource(request, zone.resource)
    return _dns_zone_out(request, zone)


@web_domain_specialist_router.post(
    "/infrastructure/dns-zones/{resource_id}/records",
    response={
        201: DNSRecordOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def create_dns_record(
    request: HttpRequest,
    resource_id: int,
    payload: DNSRecordCreateIn,
) -> tuple[int, DNSRecordOut | dict[str, object]]:
    problem = _permission_problem(
        request,
        "infrastructure.view_infrastructureresource",
        "infrastructure.view_dnszone",
        "infrastructure.view_dnsrecord",
        "infrastructure.add_dnsrecord",
    )
    if problem:
        return problem
    zone = _visible_dns_zone(request, resource_id)
    if zone is None:
        return _problem(404, "DNS zone not found.", "not_found")
    record = DNSRecord(zone=zone)
    _populate_dns_record(record, payload)
    try:
        record.full_clean()
        record.save()
    except ValidationError as error:
        return _validation_problem(error)
    return 201, _dns_record_out(record)


@web_domain_specialist_router.put(
    "/infrastructure/dns-zones/{resource_id}/records/{record_id}",
    response={
        200: DNSRecordOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_dns_record(
    request: HttpRequest,
    resource_id: int,
    record_id: int,
    payload: DNSRecordUpdateIn,
) -> DNSRecordOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.view_infrastructureresource",
        "infrastructure.view_dnszone",
        "infrastructure.view_dnsrecord",
        "infrastructure.change_dnsrecord",
    )
    if problem:
        return problem
    zone = _visible_dns_zone(request, resource_id)
    if zone is None:
        return _problem(404, "DNS zone not found.", "not_found")
    record = DNSRecord.objects.filter(id=record_id, zone=zone).first()
    if record is None:
        return _problem(404, "DNS record not found.", "not_found")
    _populate_dns_record(record, payload)
    try:
        record.full_clean()
        record.save()
    except ValidationError as error:
        return _validation_problem(error)
    return _dns_record_out(record)


@web_domain_specialist_router.delete(
    "/infrastructure/dns-zones/{resource_id}/records/{record_id}",
    response={204: None, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def delete_dns_record(
    request: HttpRequest,
    resource_id: int,
    record_id: int,
) -> tuple[int, None] | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.view_infrastructureresource",
        "infrastructure.view_dnszone",
        "infrastructure.view_dnsrecord",
        "infrastructure.delete_dnsrecord",
    )
    if problem:
        return problem
    zone = _visible_dns_zone(request, resource_id)
    if zone is None:
        return _problem(404, "DNS zone not found.", "not_found")
    record = DNSRecord.objects.filter(id=record_id, zone=zone).first()
    if record is None:
        return _problem(404, "DNS record not found.", "not_found")
    record.delete()
    return 204, None


@web_domain_specialist_router.post(
    "/infrastructure/tls-certificates",
    response={
        201: TLSCertificateOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def create_tls_certificate(
    request: HttpRequest,
    payload: TLSCertificateCreateIn,
) -> tuple[int, TLSCertificateOut | dict[str, object]]:
    problem = _permission_problem(
        request,
        "infrastructure.add_infrastructureresource",
        "infrastructure.add_tlscertificate",
    )
    if problem:
        return problem
    provider = _visible_provider_account(request, payload.provider_account_resource_id)
    if payload.provider_account_resource_id is not None and provider is None:
        return _problem(404, "TLS provider account not found.", "not_found")
    try:
        with transaction.atomic():
            resource, resource_problem = _new_resource(
                request,
                payload,
                InfrastructureResource.ResourceType.TLS_CERTIFICATE,
            )
            if resource_problem:
                transaction.set_rollback(True)
                return resource_problem
            assert resource is not None
            certificate = TLSCertificate(resource=resource, provider_account=provider)
            _populate_tls_certificate(certificate, payload)
            certificate.full_clean()
            certificate.save()
    except ValidationError as error:
        return _validation_problem(error)
    created = _visible_tls_certificate(request, resource.id)
    assert created is not None
    return 201, _tls_certificate_out(request, created)


@web_domain_specialist_router.put(
    "/infrastructure/tls-certificates/{resource_id}",
    response={
        200: TLSCertificateOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_tls_certificate(
    request: HttpRequest,
    resource_id: int,
    payload: TLSCertificateUpdateIn,
) -> TLSCertificateOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.change_infrastructureresource",
        "infrastructure.change_tlscertificate",
    )
    if problem:
        return problem
    certificate = _visible_tls_certificate(request, resource_id)
    if certificate is None:
        return _problem(404, "TLS certificate not found.", "not_found")
    provider = _visible_provider_account(request, payload.provider_account_resource_id)
    if payload.provider_account_resource_id is not None and provider is None:
        return _problem(404, "TLS provider account not found.", "not_found")
    try:
        with transaction.atomic():
            resource_problem = _update_resource(request, certificate.resource, payload)
            if resource_problem:
                transaction.set_rollback(True)
                return resource_problem
            certificate.provider_account = provider
            _populate_tls_certificate(certificate, payload)
            certificate.full_clean()
            certificate.save()
    except ValidationError as error:
        return _validation_problem(error)
    refreshed = _visible_tls_certificate(request, resource_id)
    assert refreshed is not None
    return _tls_certificate_out(request, refreshed)


@web_domain_specialist_router.post(
    "/infrastructure/tls-certificates/{resource_id}/archive",
    response={200: TLSCertificateOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def archive_tls_certificate(
    request: HttpRequest,
    resource_id: int,
) -> TLSCertificateOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.change_infrastructureresource",
        "infrastructure.change_tlscertificate",
    )
    if problem:
        return problem
    certificate = _visible_tls_certificate(request, resource_id)
    if certificate is None:
        return _problem(404, "TLS certificate not found.", "not_found")
    _archive_resource(request, certificate.resource)
    return _tls_certificate_out(request, certificate)


@web_domain_specialist_router.post(
    "/infrastructure/tls-certificates/{resource_id}/domains",
    response={
        201: TLSCertificateDomainOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def create_tls_certificate_domain(
    request: HttpRequest,
    resource_id: int,
    payload: TLSCertificateDomainCreateIn,
) -> tuple[int, TLSCertificateDomainOut | dict[str, object]]:
    problem = _permission_problem(
        request,
        "infrastructure.view_infrastructureresource",
        "infrastructure.view_tlscertificate",
        "infrastructure.view_domainprofile",
        "infrastructure.view_tlscertificatedomain",
        "infrastructure.add_tlscertificatedomain",
    )
    if problem:
        return problem
    certificate = _visible_tls_certificate(request, resource_id)
    domain = _visible_domain(request, payload.domain_resource_id)
    if certificate is None:
        return _problem(404, "TLS certificate not found.", "not_found")
    if domain is None:
        return _problem(404, "Domain not found.", "not_found")
    link = TLSCertificateDomain(
        certificate=certificate,
        domain=domain,
        is_primary=payload.is_primary,
    )
    try:
        link.full_clean()
        link.save()
    except ValidationError as error:
        return _validation_problem(error)
    link = TLSCertificateDomain.objects.select_related("domain__resource").get(id=link.id)
    return 201, _tls_domain_out(link)


@web_domain_specialist_router.delete(
    "/infrastructure/tls-certificates/{resource_id}/domains/{link_id}",
    response={204: None, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def delete_tls_certificate_domain(
    request: HttpRequest,
    resource_id: int,
    link_id: int,
) -> tuple[int, None] | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.view_infrastructureresource",
        "infrastructure.view_tlscertificate",
        "infrastructure.view_domainprofile",
        "infrastructure.view_tlscertificatedomain",
        "infrastructure.delete_tlscertificatedomain",
    )
    if problem:
        return problem
    certificate = _visible_tls_certificate(request, resource_id)
    if certificate is None:
        return _problem(404, "TLS certificate not found.", "not_found")
    link = TLSCertificateDomain.objects.filter(
        id=link_id,
        certificate=certificate,
        domain__resource__in=_visible_queryset(request),
    ).first()
    if link is None:
        return _problem(404, "TLS certificate domain link not found.", "not_found")
    link.delete()
    return 204, None


@web_domain_specialist_router.put(
    "/infrastructure/tls-certificates/{resource_id}/domains/{link_id}",
    response={
        200: TLSCertificateDomainOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_tls_certificate_domain(
    request: HttpRequest, resource_id: int, link_id: int, payload: TLSCertificateDomainCreateIn
) -> TLSCertificateDomainOut | StaffProblem:
    problem = _permission_problem(
        request,
        "infrastructure.view_infrastructureresource",
        "infrastructure.view_tlscertificate",
        "infrastructure.view_domainprofile",
        "infrastructure.view_tlscertificatedomain",
        "infrastructure.change_tlscertificatedomain",
    )
    if problem:
        return problem
    owner = _visible_tls_certificate(request, resource_id)
    related = _visible_domain(request, payload.domain_resource_id)
    if owner is None or related is None:
        return _problem(404, "Resource not found.", "not_found")
    try:
        with transaction.atomic():
            link = (
                TLSCertificateDomain.objects.select_for_update()
                .filter(
                    id=link_id, certificate=owner, domain__resource__in=_visible_queryset(request)
                )
                .first()
            )
            if link is None:
                return _problem(404, "Link not found.", "not_found")
            link.domain = related
            link.is_primary = payload.is_primary
            link.full_clean()
            link.save()
            AuditEvent.record(
                action="updated",
                target=link,
                actor=request.user,
                resource_id=owner.resource_id,
                client_id=owner.resource.client_id,
            )
    except ValidationError as error:
        return _validation_problem(error)
    return _tls_domain_out(link)

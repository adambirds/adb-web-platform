"""Public registration/certificate discovery; never retrieve account secrets."""

from __future__ import annotations

import json
import socket
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any
from urllib.parse import quote, urlparse

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import NameOID
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.core.models import AuditEvent
from apps.monitoring.models import MonitorCheck

from .models import DomainProfile, InfrastructureResource, TLSCertificate, WebsiteEndpoint

REFRESH_INTERVAL = timedelta(days=1)
ERROR_RETRY_INTERVAL = timedelta(hours=1)
LOOKUP_TIMEOUT_SECONDS = 10
MAX_RDAP_BYTES = 1_000_000
CURRENT_LIFECYCLES = [
    InfrastructureResource.LifecycleStatus.ACTIVE,
    InfrastructureResource.LifecycleStatus.MAINTENANCE,
    InfrastructureResource.LifecycleStatus.DEPRECATED,
]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> None:
        return None


def _rdap_json(url: str) -> dict[str, Any]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("RDAP requires an HTTPS registry URL.")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/rdap+json, application/json",
            "User-Agent": "ADB-Inventory/1.0",
        },
    )
    # Only IANA bootstrap URLs are used; provider links and redirects are not followed.
    with urllib.request.build_opener(_NoRedirect()).open(
        request, timeout=LOOKUP_TIMEOUT_SECONDS
    ) as response:
        payload = response.read(MAX_RDAP_BYTES + 1)
    if len(payload) > MAX_RDAP_BYTES:
        raise ValueError("RDAP response exceeded the size limit.")
    result = json.loads(payload)
    if not isinstance(result, dict):
        raise ValueError("RDAP response must be a JSON object.")
    return result


@dataclass(frozen=True)
class DomainMetadata:
    registered_on: date | None
    expires_on: date
    transfer_lock_enabled: bool | None


def discover_domain(domain_name: str) -> DomainMetadata:
    """Query the IANA-listed authoritative registry; retain no contact data."""
    domain = domain_name.rstrip(".").encode("idna").decode("ascii").lower()
    bootstrap = cache.get("infrastructure:rdap:dns-bootstrap")
    if bootstrap is None:
        bootstrap = _rdap_json("https://data.iana.org/rdap/dns.json")
        cache.set("infrastructure:rdap:dns-bootstrap", bootstrap, timeout=86400)
    services = bootstrap.get("services", [])
    if not isinstance(services, list):
        raise ValueError("Invalid RDAP bootstrap services.")
    urls: list[str] = []
    for service in services:
        if (
            isinstance(service, list)
            and len(service) == 2
            and isinstance(service[0], list)
            and isinstance(service[1], list)
            and domain.rsplit(".", 1)[-1] in service[0]
        ):
            urls = [
                url for url in service[1] if isinstance(url, str) and url.startswith("https://")
            ]
            break
    if not urls:
        raise ValueError("No HTTPS RDAP service is published for this domain's TLD.")
    data: dict[str, Any] | None = None
    for url in urls:
        try:
            data = _rdap_json(f"{url.rstrip('/')}/domain/{quote(domain, safe='')}")
            break
        except (OSError, ValueError, urllib.error.URLError):
            continue
    if data is None:
        raise ValueError("Registry RDAP lookup failed; stored registration dates were retained.")
    returned_name = data.get("ldhName") or data.get("unicodeName")
    if (
        not isinstance(returned_name, str)
        or returned_name.rstrip(".").encode("idna").decode("ascii").lower() != domain
        or data.get("objectClassName") != "domain"
    ):
        raise ValueError("RDAP response did not match the requested domain.")
    events = data.get("events", [])
    dates: dict[str, date] = {}
    if not isinstance(events, list):
        raise ValueError("Invalid RDAP events.")
    for event in events:
        if not isinstance(event, dict):
            continue
        action = event.get("eventAction")
        if action not in {"registration", "expiration"}:
            continue
        stamp = event.get("eventDate")
        if not isinstance(stamp, str):
            raise ValueError("Invalid RDAP event date.")
        parsed_date = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        if parsed_date.tzinfo is None:
            raise ValueError("RDAP event dates must include a timezone.")
        observed = parsed_date.astimezone(UTC).date()
        if action in dates and dates[action] != observed:
            raise ValueError("Registry supplied conflicting registration dates.")
        dates[action] = observed
    if "expiration" not in dates:
        raise ValueError(
            "Registry does not publish an expiration date; stored dates were retained."
        )
    status = data.get("status")
    locked = (
        "client transfer prohibited" in status or "server transfer prohibited" in status
        if isinstance(status, list)
        else None
    )
    return DomainMetadata(dates.get("registration"), dates["expiration"], locked)


def certificate_target(certificate: TLSCertificate) -> str | None:
    # An explicitly linked HTTPS endpoint takes precedence over the stored CN.
    endpoint = (
        WebsiteEndpoint.objects.filter(
            tls_certificate=certificate,
            resource__lifecycle_status__in=CURRENT_LIFECYCLES,
            url__startswith="https://",
        )
        .order_by("-is_primary", "id")
        .first()
    )
    if endpoint is not None:
        return endpoint.url
    name = certificate.subject_common_name.strip()
    if not name or "*" in name or "/" in name or ":" in name:
        return certificate.metadata_source or None
    return f"https://{name}"


def discover_certificate(target: str) -> dict[str, str | datetime]:
    parsed = urlparse(target)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("A concrete HTTPS endpoint or certificate common name is required.")
    context = ssl.create_default_context()
    with (
        socket.create_connection(
            (parsed.hostname, parsed.port or 443), timeout=LOOKUP_TIMEOUT_SECONDS
        ) as raw_socket,
        context.wrap_socket(raw_socket, server_hostname=parsed.hostname) as tls_socket,
    ):
        der = tls_socket.getpeercert(binary_form=True)
    if der is None:
        raise ValueError("TLS endpoint did not provide a certificate.")
    certificate = x509.load_der_x509_certificate(der)
    names = certificate.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
    hostname = f"[{parsed.hostname}]" if ":" in parsed.hostname else parsed.hostname
    origin = f"https://{hostname}" + (f":{parsed.port}" if parsed.port else "")
    return {
        "metadata_source": origin,
        "issuer": certificate.issuer.rfc4514_string()[:255],
        "subject_common_name": str(names[0].value)[:253] if names else "",
        "serial_number": format(certificate.serial_number, "x")[:200],
        "fingerprint_sha256": certificate.fingerprint(hashes.SHA256()).hex(),
        "issued_at": certificate.not_valid_before_utc,
        "expires_at": certificate.not_valid_after_utc,
    }


def refresh_due(profile: DomainProfile | TLSCertificate) -> bool:
    interval = ERROR_RETRY_INTERVAL if profile.metadata_refresh_error else REFRESH_INTERVAL
    return (
        profile.last_metadata_checked_at is None
        or profile.last_metadata_checked_at <= timezone.now() - interval
    )


def ensure_expiry_check(profile: DomainProfile | TLSCertificate) -> MonitorCheck:
    domain = isinstance(profile, DomainProfile)
    check_type = (
        MonitorCheck.CheckType.DOMAIN_EXPIRY
        if domain
        else MonitorCheck.CheckType.CERTIFICATE_EXPIRY
    )
    with transaction.atomic():
        InfrastructureResource.objects.select_for_update().get(pk=profile.resource_id)
        existing = MonitorCheck.objects.filter(
            resource_id=profile.resource_id, check_type=check_type
        ).first()
        if existing is not None:
            return existing
        check = MonitorCheck(
            resource=profile.resource,
            name="Automatic registration expiry" if domain else "Automatic certificate expiry",
            check_type=check_type,
            target=profile.domain_name
            if isinstance(profile, DomainProfile)
            else f"certificate:{profile.pk}",
            interval_seconds=3600,
            failure_threshold=1,
            recovery_threshold=1,
        )
        # Do not hijack a manually configured check with the reserved display name.
        if MonitorCheck.objects.filter(resource_id=profile.resource_id, name=check.name).exists():
            check.name = f"{check.name} ({check_type})"
        check.full_clean()
        check.save()
        return check


def refresh_metadata(resource_id: int) -> bool:
    """Refresh one inventory record; callers provide a resource-scoped worker lock."""
    resource = InfrastructureResource.objects.filter(
        pk=resource_id, lifecycle_status__in=CURRENT_LIFECYCLES
    ).first()
    if resource is None:
        return False
    profile: DomainProfile | TLSCertificate | None
    if resource.resource_type == InfrastructureResource.ResourceType.DOMAIN:
        profile = DomainProfile.objects.filter(resource=resource).first()
    elif resource.resource_type == InfrastructureResource.ResourceType.TLS_CERTIFICATE:
        profile = TLSCertificate.objects.filter(resource=resource).first()
    else:
        return False
    if profile is None:
        return False
    ensure_expiry_check(profile)
    if not refresh_due(profile):
        return False
    source = (
        profile.domain_name if isinstance(profile, DomainProfile) else certificate_target(profile)
    )
    values: dict[str, str | date | datetime | bool] = {}
    error = ""
    try:
        if isinstance(profile, DomainProfile):
            metadata = discover_domain(profile.domain_name)
            values["expires_on"] = metadata.expires_on
            if profile.registered_on is None and metadata.registered_on is not None:
                values["registered_on"] = metadata.registered_on
            if profile.transfer_lock_enabled is None and metadata.transfer_lock_enabled is not None:
                values["transfer_lock_enabled"] = metadata.transfer_lock_enabled
        else:
            if source is None:
                raise ValueError(
                    "Link an HTTPS Website Endpoint or supply a concrete certificate common name for discovery."
                )
            values.update(discover_certificate(source))
    except (OSError, ValueError, urllib.error.URLError) as lookup_error:
        error = str(lookup_error)[:500]
    with transaction.atomic():
        resource = InfrastructureResource.objects.select_for_update().get(pk=resource_id)
        if resource.lifecycle_status not in CURRENT_LIFECYCLES:
            return False
        profile.refresh_from_db()
        current_source = (
            profile.domain_name
            if isinstance(profile, DomainProfile)
            else certificate_target(profile)
        )
        if current_source != source:
            return False
        changed: list[str] = []
        if not error:
            for field, value in values.items():
                if (
                    field in {"registered_on", "transfer_lock_enabled"}
                    and getattr(profile, field) is not None
                ):
                    continue
                if getattr(profile, field) != value:
                    setattr(profile, field, value)
                    changed.append(field)
            try:
                profile.full_clean()
            except ValidationError:
                error = "Discovered metadata conflicts with the stored record; existing values were retained."
                profile.refresh_from_db()
                changed = []
        profile.last_metadata_checked_at = timezone.now()
        profile.metadata_refresh_error = error
        profile.save(
            update_fields=[
                *changed,
                "last_metadata_checked_at",
                "metadata_refresh_error",
                "updated_at",
            ]
        )
        if changed:
            AuditEvent.record(
                action="infrastructure.metadata_refreshed",
                target=resource,
                metadata={
                    "fields": changed,
                    "source": "rdap" if isinstance(profile, DomainProfile) else "tls",
                },
            )
    return True

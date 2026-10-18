"""Validated tenant administration and reusable reporting input rules."""

import re
import uuid
from datetime import date, timedelta
from typing import Any
from urllib.parse import urlsplit, urlunsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from ninja.errors import HttpError

from apps.analytics.access import business_for
from apps.analytics.models import Business, BusinessMembership, Website
from apps.core.models import AuditEvent


def normalize_domain(value: str) -> str:
    try:
        parsed = urlsplit(value.strip() if "://" in value else f"https://{value.strip()}")
        invalid = (
            parsed.scheme not in {"http", "https"}
            or parsed.username
            or parsed.password
            or parsed.port is not None
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        )
        domain = (parsed.hostname or "").rstrip(".").encode("idna").decode("ascii").lower()
    except (ValueError, UnicodeError):
        raise HttpError(422, "Enter a valid public domain.") from None
    if invalid:
        raise HttpError(422, "Enter a domain without a path, credentials or port.")
    if (
        len(domain) > 253
        or "." not in domain
        or any(
            not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", part)
            for part in domain.split(".")
        )
    ):
        raise HttpError(422, "Enter a valid public domain.")
    return domain


def normalize_page(value: str, domain: str) -> str:
    """Conservative canonical join: retain host, query and slash distinctions."""
    parsed = urlsplit(value if "://" in value else f"https://{domain}/{value.lstrip('/')}")
    return urlunsplit(
        (
            parsed.scheme.lower(),
            (parsed.hostname or domain).lower(),
            parsed.path or "/",
            parsed.query,
            "",
        )
    )


def date_window(start: date, end: date) -> tuple[date, date]:
    if start > end or (end - start).days > 365 or end > timezone.now().date():
        raise HttpError(422, "Choose a past date range of at most 366 days.")
    return start, end


def previous_window(start: date, end: date) -> tuple[date, date]:
    return start - timedelta(days=(end - start).days + 1), start - timedelta(days=1)


@transaction.atomic
def create_business(user: Any, name: str) -> Business:
    slug = f"{slugify(name)[:70] or 'business'}-{uuid.uuid4().hex[:12]}"
    business = Business.objects.create(name=name.strip(), slug=slug)
    BusinessMembership.objects.create(business=business, user=user, role="owner")
    AuditEvent.record(action="analytics.business_created", actor=user, target=business)
    return business


@transaction.atomic
def set_membership(
    user: Any, business_id: int, member_user_id: uuid.UUID, role: str | None
) -> None:
    business = business_for(user, business_id, "change_businessmembership")
    Business.objects.select_for_update().get(pk=business.pk)
    business_for(user, business_id, "change_businessmembership")
    membership = BusinessMembership.objects.filter(
        business=business, user_id=member_user_id
    ).first()
    if (
        membership
        and membership.role == "owner"
        and role != "owner"
        and business.memberships.filter(role="owner").count() <= 1
    ):
        raise HttpError(409, "A business must retain at least one owner.")
    if role is None:
        if membership:
            membership.delete()
    else:
        BusinessMembership.objects.update_or_create(
            business=business, user_id=member_user_id, defaults={"role": role}
        )
    AuditEvent.record(
        action="analytics.membership_changed",
        actor=user,
        target=business,
        metadata={"member_id": str(member_user_id), "role": role},
    )


def save_website(
    user: Any,
    business_id: int,
    *,
    name: str,
    domain: str,
    timezone: str,
    website: Website | None = None,
    is_active: bool = True,
) -> Website:
    business = business_for(user, business_id, "change_website" if website else "add_website")
    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError):
        raise HttpError(422, "Choose a valid IANA timezone.") from None
    if website and timezone != website.timezone:
        linked = website.provider_properties.filter(provider="ga4").first()
        if linked and linked.metadata.get("timeZone") != timezone:
            raise HttpError(
                409, "Unlink the current GA4 property before changing the website timezone."
            )
    normalized = normalize_domain(domain)
    duplicates = Website.objects.filter(business=business, domain=normalized)
    if website:
        duplicates = duplicates.exclude(pk=website.pk)
    if duplicates.exists():
        raise HttpError(409, "This domain already exists in the business.")
    website = website or Website(business=business)
    website.name, website.domain, website.timezone, website.is_active = (
        name.strip(),
        normalized,
        timezone,
        is_active,
    )
    website.save()
    AuditEvent.record(action="analytics.website_saved", actor=user, target=website)
    return website

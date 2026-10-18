"""Validated provider association shared by manual linking and website import."""

import re
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.db import transaction
from ninja.errors import HttpError

from apps.analytics.google import ADMIN_URL, READ, SEARCH, discover, google_request
from apps.analytics.models import GoogleConnection, ProviderProperty, Website
from apps.analytics.synchronization import queue_sync, scheduled_window
from apps.core.models import AuditEvent


def property_timezone(metadata: dict[str, Any]) -> str:
    value = metadata.get("timeZone", "")
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        raise HttpError(422, "Google did not provide a valid property timezone.") from None
    return str(value)


def link_property(
    actor: Any,
    website: Website,
    connection: GoogleConnection,
    provider: str,
    external_id: str,
    search_type: str = "web",
) -> ProviderProperty:
    if connection.business_id != website.business_id:
        raise HttpError(404, "Connection unavailable.")
    if provider == "ga4":
        if not re.fullmatch(r"properties/[0-9]+", external_id) or READ not in connection.scopes:
            raise HttpError(422, "Choose an accessible GA4 property with reporting permission.")
        metadata = google_request(connection, "GET", ADMIN_URL + external_id)
        timezone = property_timezone(metadata)
    else:
        search_metadata = next(
            (
                item
                for item in discover(connection)["gsc"]
                if item["siteUrl"] == external_id
                and item.get("permissionLevel") != "siteUnverifiedUser"
            ),
            None,
        )
        if search_metadata is None or SEARCH not in connection.scopes:
            raise HttpError(403, "Google account cannot access this Search Console property.")
        metadata = search_metadata
        timezone = None
    with transaction.atomic():
        # Lock the website even on first association so concurrent imports cannot race.
        website = Website.objects.select_for_update().get(pk=website.pk)
        existing = website.provider_properties.filter(provider=provider).first()
        if existing and existing.jobs.filter(status__in=["queued", "running", "retrying"]).exists():
            raise HttpError(409, "Wait for the active synchronization before changing properties.")
        if timezone and website.timezone != timezone:
            if website.provider_properties.filter(
                jobs__status__in=["queued", "running", "retrying"]
            ).exists():
                raise HttpError(
                    409, "Wait for synchronization before updating the property timezone."
                )
            website.timezone = timezone
            website.save(update_fields=["timezone"])
        prop, _ = ProviderProperty.objects.update_or_create(
            website=website,
            provider=provider,
            defaults={
                "connection": connection,
                "external_id": external_id,
                "metadata": {**metadata, "search_type": search_type, "_backfill_pending": True},
                "last_synced_at": None,
                "error_code": "",
            },
        )
        prop.snapshots.all().delete()
        prop.definitions.all().delete()
        prop.revision += 1
        prop.save(update_fields=["revision"])
        AuditEvent.record(
            action="analytics.property_linked",
            actor=actor,
            target=prop,
            metadata={"provider": provider, "external_id": external_id},
        )
        queue_sync(prop, *scheduled_window(prop))
    return prop

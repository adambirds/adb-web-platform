"""Discover websites from Google web streams and match verified Search Console sites."""

import re
from typing import Any
from urllib.parse import urlsplit

from django.core.cache import cache
from django.db import transaction
from ninja.errors import HttpError

from apps.analytics.access import business_for
from apps.analytics.google import ADMIN_URL, ProviderError, discover, google_request, paginated
from apps.analytics.linking import link_property, property_timezone
from apps.analytics.models import Business, GoogleConnection, Website
from apps.analytics.services import normalize_domain, save_website


def website_domain(value: str) -> str:
    """Group only bare/www variants; keep arbitrary subdomains distinct."""
    parsed = urlsplit(value if "://" in value else "https://" + value)
    domain = normalize_domain(parsed.hostname or "")
    return domain.removeprefix("www.")


def discover_websites(connection: GoogleConnection, *, refresh: bool = False) -> dict[str, Any]:
    key = f"analytics-discovery:{connection.pk}:{connection.updated_at.timestamp()}"
    if not refresh:
        cached = cache.get(key)
        if cached is not None:
            return dict(cached)
    properties = discover(connection)
    candidates: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []

    def candidate(domain: str) -> dict[str, Any]:
        return candidates.setdefault(domain, {"domain": domain, "ga4": [], "gsc": []})

    search = []
    for item in properties["gsc"]:
        if item.get("permissionLevel") == "siteUnverifiedUser":
            continue
        identifier = str(item.get("siteUrl", ""))
        try:
            is_domain = identifier.startswith("sc-domain:")
            if not is_domain and urlsplit(identifier).path not in {"", "/"}:
                warnings.append(f"Skipped path-only Search Console property: {identifier}")
                continue
            domain = website_domain(identifier.removeprefix("sc-domain:"))
        except HttpError:
            continue
        search.append((domain, is_domain, identifier))
        candidate(domain)
    ga_properties = properties["ga4"]
    if len(ga_properties) > 100:
        warnings.append(
            "Showing the first 100 GA4 properties. Use a narrower Google account for additional properties."
        )
    for item in ga_properties[:100]:
        identifier = str(item.get("property", ""))
        if not re.fullmatch(r"properties/[0-9]+", identifier):
            continue
        try:
            metadata = google_request(connection, "GET", ADMIN_URL + identifier)
            timezone = property_timezone(metadata)
            streams = paginated(connection, ADMIN_URL + identifier + "/dataStreams", "dataStreams")
        except ProviderError as exc:
            if exc.code != "google_permission_denied":
                raise
            warnings.append(
                f"Could not read web streams for {item.get('displayName', identifier)}."
            )
            continue
        except HttpError:
            warnings.append(f"Google supplied an invalid timezone for {identifier}.")
            continue
        hosts: set[str] = set()
        for stream in streams:
            uri = stream.get("webStreamData", {}).get("defaultUri", "")
            if not uri:
                continue
            try:
                hosts.add(website_domain(uri))
            except HttpError:
                continue
        if not hosts:
            warnings.append(
                f"No usable website URL found in web streams for {item.get('displayName', identifier)}."
            )
        for domain in hosts:
            candidate(domain)["ga4"].append(
                {"id": identifier, "name": item.get("displayName", domain), "timezone": timezone}
            )
    for domain, row in candidates.items():
        matches = [
            (host, is_domain, identifier)
            for host, is_domain, identifier in search
            if domain == host or (is_domain and domain.endswith("." + host))
        ]
        # Prefer exact coverage, then the most specific domain property. Never use name guessing.
        matches.sort(key=lambda entry: (entry[0] == domain, len(entry[0]), entry[1]), reverse=True)
        row["gsc"] = [{"id": identifier, "name": identifier} for _, _, identifier in matches]
        row["existing_id"] = next(
            (
                w.pk
                for w in connection.business.websites.all()
                if website_domain(w.domain) == domain
            ),
            None,
        )
    result = {
        "websites": sorted(candidates.values(), key=lambda row: row["domain"]),
        "warnings": warnings,
    }
    cache.set(key, result, 300)
    return result


def import_websites(
    actor: Any, connection: GoogleConnection, selections: list[dict[str, Any]]
) -> list[Website]:
    business_for(actor, connection.business_id, "add_website")
    business_for(actor, connection.business_id, "change_googleconnection")
    if not selections or len({item["domain"] for item in selections}) != len(selections):
        raise HttpError(422, "Select each website once.")
    # Re-fetch Google's inventory on mutation; never trust domains/property IDs supplied by a browser.
    inventory = {
        row["domain"]: row for row in discover_websites(connection, refresh=True)["websites"]
    }
    validated = []
    for selection in selections:
        row = inventory.get(selection["domain"])
        if not row:
            raise HttpError(422, "A selected website is no longer accessible in Google.")
        ga4 = next((prop for prop in row["ga4"] if prop["id"] == selection.get("ga4")), None)
        gsc = next((prop for prop in row["gsc"] if prop["id"] == selection.get("gsc")), None)
        if (row["ga4"] and not ga4) or (row["gsc"] and not gsc) or (not ga4 and not gsc):
            raise HttpError(422, "Choose a discovered property for each available provider.")
        validated.append((row, ga4, gsc))
    imported = []
    with transaction.atomic():
        Business.objects.select_for_update().get(pk=connection.business_id)
        for row, ga4, gsc in validated:
            website = next(
                (
                    w
                    for w in connection.business.websites.all()
                    if website_domain(w.domain) == row["domain"]
                ),
                None,
            )
            if website:
                business_for(actor, connection.business_id, "change_website")
                if not website.is_active:
                    website.is_active = True
                    website.save(update_fields=["is_active"])
            else:
                website = save_website(
                    actor,
                    connection.business_id,
                    name=row["domain"],
                    domain=row["domain"],
                    timezone=ga4["timezone"] if ga4 else "America/Los_Angeles",
                )
            for provider, selected in (("ga4", ga4), ("gsc", gsc)):
                if not selected:
                    continue
                current = website.provider_properties.filter(provider=provider).first()
                if current:
                    if (
                        current.external_id == selected["id"]
                        and current.connection_id == connection.pk
                    ):
                        continue
                    raise HttpError(
                        409,
                        f"{website.domain} already has a different {provider} property. Unlink it in Integrations first.",
                    )
                link_property(actor, website, connection, provider, selected["id"])
            imported.append(website)
    return imported

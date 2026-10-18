"""Session-authenticated analytics product APIs, independent of staff operations."""

import csv
import io
from datetime import date
from typing import Any, Literal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from ninja.errors import HttpError
from ninja.security import django_auth
from pydantic import ConfigDict, Field

from apps.analytics.access import business_for, website_for
from apps.analytics.administration import (
    create_definition,
    definition_plan,
    definitions,
    delete_key_event,
)
from apps.analytics.google import (
    ADMIN_URL,
    EDIT,
    READ,
    SEARCH,
    consume_oauth_state,
    disconnect,
    discover,
    google_request,
    oauth_callback,
    oauth_start,
)
from apps.analytics.models import (
    AnalyticsPreference,
    Business,
    GoogleConnection,
    ProviderProperty,
    ReportSnapshot,
    SyncJob,
)
from apps.analytics.reports import (
    GA_REPORTS,
    GSC_REPORTS,
    derive_metrics,
    ga_report,
    opportunities,
    realtime,
)
from apps.analytics.services import (
    create_business,
    date_window,
    normalize_page,
    previous_window,
    save_website,
    set_membership,
)
from apps.analytics.synchronization import queue_sync, scheduled_window
from apps.core.models import AuditEvent
from authentication.custom_request import AuthenticatedHttpRequest

router = Router(tags=["analytics"], auth=django_auth)


class BusinessIn(Schema):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=255)


class WebsiteIn(BusinessIn):
    domain: str = Field(min_length=1, max_length=253)
    timezone: str = "Europe/London"
    is_active: bool = True


class MembershipIn(Schema):
    email: str = Field(max_length=254)
    role: Literal["owner", "admin", "viewer"] | None = None


class OAuthIn(Schema):
    mode: Literal["reporting", "administration"] = "reporting"


class PropertyIn(Schema):
    search_type: Literal["web", "image", "video", "news", "discover", "googleNews"] = "web"
    connection_id: int
    external_id: str = Field(min_length=1, max_length=512)


class WindowIn(Schema):
    start: date
    end: date


class DefinitionIn(Schema):
    confirmed: bool = False
    parameterName: str = ""
    displayName: str = ""
    description: str = ""
    measurementUnit: str = "STANDARD"
    eventName: str = ""


class ParametersIn(Schema):
    event: str = Field(min_length=1, max_length=40)
    parameters: list[str] = Field(max_length=25)
    confirmed: bool = False


class KeyEventDeleteIn(Schema):
    name: str
    confirmed: bool = False


class PreferenceIn(Schema):
    website_id: int


def throttle(request: AuthenticatedHttpRequest, action: str, limit: int = 30) -> None:
    key = f"analytics-rate:{request.user.pk}:{action}"
    if cache.add(key, 1, 60):
        return
    if cache.incr(key) > limit:
        raise HttpError(429, "Too many requests. Try again shortly.")


def prop_for(
    request: AuthenticatedHttpRequest,
    website_id: int,
    provider: str,
    capability: str = "view_report",
) -> ProviderProperty:
    website = website_for(request.user, website_id, capability)
    if provider not in {"ga4", "gsc"}:
        raise HttpError(422, "Unknown provider.")
    return get_object_or_404(
        website.provider_properties.select_related("connection"), provider=provider
    )


def website_json(website: Any) -> dict[str, Any]:
    return {
        "id": website.pk,
        "business_id": website.business_id,
        "name": website.name,
        "domain": website.domain,
        "timezone": website.timezone,
        "is_active": website.is_active,
        "providers": [
            {
                "provider": p.provider,
                "external_id": p.external_id,
                "connection_id": p.connection_id,
                "metadata": p.metadata,
                "last_synced_at": p.last_synced_at,
                "error_code": p.error_code,
            }
            for p in website.provider_properties.all()
        ],
    }


@router.get("/session")
def session(request: AuthenticatedHttpRequest) -> dict[str, Any]:
    businesses = Business.objects.filter(memberships__user=request.user).prefetch_related(
        "websites__provider_properties", "memberships"
    )
    return {
        "email": request.user.email,
        "businesses": [
            {
                "id": b.pk,
                "name": b.name,
                "slug": b.slug,
                "role": b.memberships.get(user=request.user).role,
                "websites": [website_json(w) for w in b.websites.all()],
            }
            for b in businesses
        ],
        "website_id": AnalyticsPreference.objects.filter(user=request.user)
        .values_list("website_id", flat=True)
        .first(),
    }


@router.post("/businesses")
def business_create(request: AuthenticatedHttpRequest, payload: BusinessIn) -> dict[str, Any]:
    throttle(request, "business-create", 5)
    business = create_business(request.user, payload.name)
    return {"id": business.pk, "name": business.name}


@router.put("/businesses/{business_id}")
def business_update(
    request: AuthenticatedHttpRequest, business_id: int, payload: BusinessIn
) -> dict[str, Any]:
    business = business_for(request.user, business_id, "change_business")
    business.name = payload.name.strip()
    business.save()
    AuditEvent.record(action="analytics.business_updated", actor=request.user, target=business)
    return {"id": business.pk, "name": business.name}


@router.get("/businesses/{business_id}/members")
def members(request: AuthenticatedHttpRequest, business_id: int) -> list[dict[str, Any]]:
    business = business_for(request.user, business_id, "change_businessmembership")
    return [
        {"email": m.user.email, "role": m.role} for m in business.memberships.select_related("user")
    ]


@router.put("/businesses/{business_id}/members")
def member_update(
    request: AuthenticatedHttpRequest, business_id: int, payload: MembershipIn
) -> dict[str, bool]:
    business_for(request.user, business_id, "change_businessmembership")
    user = get_object_or_404(get_user_model(), email__iexact=payload.email, is_active=True)
    set_membership(request.user, business_id, user.pk, payload.role)
    return {"saved": True}


@router.post("/businesses/{business_id}/websites")
def website_create(
    request: AuthenticatedHttpRequest, business_id: int, payload: WebsiteIn
) -> dict[str, Any]:
    return website_json(save_website(request.user, business_id, **payload.model_dump()))


@router.put("/websites/{website_id}")
def website_update(
    request: AuthenticatedHttpRequest, website_id: int, payload: WebsiteIn
) -> dict[str, Any]:
    website = website_for(request.user, website_id, "change_website")
    return website_json(
        save_website(request.user, website.business_id, website=website, **payload.model_dump())
    )


@router.put("/preferences")
def preferences(request: AuthenticatedHttpRequest, payload: PreferenceIn) -> dict[str, bool]:
    website = website_for(request.user, payload.website_id)
    AnalyticsPreference.objects.update_or_create(user=request.user, defaults={"website": website})
    return {"saved": True}


@router.get("/businesses/{business_id}/connections")
def connections(request: AuthenticatedHttpRequest, business_id: int) -> list[dict[str, Any]]:
    business_for(request.user, business_id, "change_googleconnection")
    return [
        dict(row)
        for row in (
            GoogleConnection.objects.filter(business_id=business_id).values(
                "id", "email", "status", "scopes", "error_code", "last_validated_at"
            )
        )
    ]


@router.post("/businesses/{business_id}/oauth")
def connect(
    request: AuthenticatedHttpRequest, business_id: int, payload: OAuthIn
) -> dict[str, str]:
    throttle(request, "oauth", 10)
    return {"url": oauth_start(request, business_id, payload.mode)}


@router.get("/oauth/callback")
def callback(
    request: AuthenticatedHttpRequest, state: str = "", code: str = "", error: str = ""
) -> HttpResponse:
    if error:
        consume_oauth_state(request, state)
        return HttpResponseRedirect(settings.ANALYTICS_FRONTEND_URL + "/?integration=denied")
    oauth_callback(request, state, code)
    response = HttpResponseRedirect(settings.ANALYTICS_FRONTEND_URL + "/?integration=connected")
    response["Cache-Control"] = "no-store"
    response["Referrer-Policy"] = "no-referrer"
    return response


def connection_for(request: AuthenticatedHttpRequest, connection_id: int) -> GoogleConnection:
    connection = get_object_or_404(
        GoogleConnection.objects.filter(business__memberships__user=request.user), pk=connection_id
    )
    business_for(request.user, connection.business_id, "change_googleconnection")
    return connection


@router.get("/connections/{connection_id}/properties")
def property_discovery(request: AuthenticatedHttpRequest, connection_id: int) -> dict[str, Any]:
    throttle(request, "discovery")
    return discover(connection_for(request, connection_id))


@router.post("/connections/{connection_id}/disconnect")
def connection_disconnect(request: AuthenticatedHttpRequest, connection_id: int) -> dict[str, bool]:
    disconnect(connection_for(request, connection_id), request.user)
    return {"disconnected": True}


@router.put("/websites/{website_id}/properties/{provider}")
def associate(
    request: AuthenticatedHttpRequest,
    website_id: int,
    provider: Literal["ga4", "gsc"],
    payload: PropertyIn,
) -> dict[str, bool]:
    website = website_for(request.user, website_id, "change_googleconnection")
    connection = connection_for(request, payload.connection_id)
    if connection.business_id != website.business_id:
        raise HttpError(404, "Connection unavailable.")
    if provider == "ga4":
        import re

        if (
            not re.fullmatch(r"properties/[0-9]+", payload.external_id)
            or READ not in connection.scopes
        ):
            raise HttpError(422, "Choose an accessible GA4 property with reporting permission.")
        metadata = google_request(connection, "GET", ADMIN_URL + payload.external_id)
        if metadata.get("timeZone") != website.timezone:
            raise HttpError(
                422,
                "Set the website timezone to match the GA4 property timezone: "
                + metadata.get("timeZone", "unknown"),
            )
    else:
        properties = discover(connection)["gsc"]
        search_metadata = next(
            (
                item
                for item in properties
                if item["siteUrl"] == payload.external_id
                and item.get("permissionLevel") != "siteUnverifiedUser"
            ),
            None,
        )
        if search_metadata is None or SEARCH not in connection.scopes:
            raise HttpError(403, "Google account cannot access this Search Console property.")
    with transaction.atomic():
        existing = (
            ProviderProperty.objects.select_for_update()
            .filter(website=website, provider=provider)
            .first()
        )
        if existing and existing.jobs.filter(status__in=["queued", "running", "retrying"]).exists():
            raise HttpError(409, "Wait for the active synchronization before changing properties.")
        prop, _ = ProviderProperty.objects.update_or_create(
            website=website,
            provider=provider,
            defaults={
                "connection": connection,
                "external_id": payload.external_id,
                "metadata": {**metadata, "_backfill_pending": True},
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
            actor=request.user,
            target=prop,
            metadata={"provider": provider, "external_id": payload.external_id},
        )
        queue_sync(prop, *scheduled_window(prop))
    return {"linked": True}


@router.post("/websites/{website_id}/sync")
def synchronize(
    request: AuthenticatedHttpRequest, website_id: int, payload: WindowIn
) -> list[dict[str, Any]]:
    website = website_for(request.user, website_id, "sync_providerproperty")
    throttle(request, "sync", 6)
    date_window(payload.start, payload.end)
    result = []
    for prop in website.provider_properties.filter(connection__status="connected"):
        job = queue_sync(prop, payload.start, payload.end)
        result.append(
            {
                "id": job.pk,
                "provider": prop.provider,
                "status": job.status,
                "start": job.start,
                "end": job.end,
            }
        )
    return result


@router.get("/websites/{website_id}/sync")
def sync_status(request: AuthenticatedHttpRequest, website_id: int) -> list[dict[str, Any]]:
    website_for(request.user, website_id)
    return [
        dict(row)
        for row in (
            SyncJob.objects.filter(property__website_id=website_id)
            .order_by("-created_at")
            .values(
                "id",
                "property__provider",
                "status",
                "progress",
                "error_code",
                "start",
                "end",
                "updated_at",
            )[:20]
        )
    ]


def snapshot(prop: ProviderProperty, report: str, start: date, end: date) -> dict[str, Any] | None:
    key = f"analytics-report:{prop.pk}:{prop.revision}:{report}:{start}:{end}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    stored = ReportSnapshot.objects.filter(
        property=prop, report=report, start=start, end=end
    ).first()
    if stored is None:
        return None
    result = {
        **stored.payload,
        "rows": [derive_metrics(row) for row in stored.payload.get("rows", [])],
        "updated_at": stored.updated_at.isoformat(),
    }
    cache.set(key, result, 300)
    return result


@router.get("/websites/{website_id}/reports/{provider}/{report}")
def report_get(
    request: AuthenticatedHttpRequest,
    website_id: int,
    provider: str,
    report: str,
    start: date,
    end: date,
    search: str = "",
    sort: str = "",
    descending: bool = True,
    page: int = 1,
    page_size: int = 100,
    export: bool = False,
) -> Any:
    prop = prop_for(request, website_id, provider)
    date_window(start, end)
    allowed = GA_REPORTS if provider == "ga4" else GSC_REPORTS
    if report not in allowed:
        raise HttpError(422, "Unsupported report.")
    current = snapshot(prop, report, start, end)
    previous = snapshot(prop, report, *previous_window(start, end))
    rows = (
        [
            r
            for r in current["rows"]
            if not search or search.lower() in " ".join(map(str, r.values())).lower()
        ]
        if current
        else []
    )
    if sort and rows and sort in rows[0]:
        rows = sorted(
            rows, key=lambda r: (r.get(sort) is not None, r.get(sort, 0)), reverse=descending
        )
    if export:
        if current is None:
            raise HttpError(409, "Synchronize this date range before exporting.")
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else [])
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    k: "'" + str(v)
                    if isinstance(v, str)
                    and (v.lstrip().startswith(("=", "+", "-", "@")) or v.startswith(("\t", "\r")))
                    else v
                    for k, v in row.items()
                }
            )
        response = HttpResponse(stream.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{provider}-{report}.csv"'
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response
    total = len(rows)
    if current:
        size = min(max(page_size, 1), 1000)
        current = {**current, "rows": rows[(max(page, 1) - 1) * size : max(page, 1) * size]}
    return {
        "current": current,
        "previous": previous,
        "total": total,
        "page": page,
        "last_synced_at": prop.last_synced_at,
        "error_code": prop.error_code,
        "status": "available" if current else "range_not_synchronized",
        "timezone": prop.website.timezone,
    }


@router.get("/websites/{website_id}/realtime")
def realtime_get(request: AuthenticatedHttpRequest, website_id: int) -> dict[str, Any]:
    prop = prop_for(request, website_id, "ga4")
    throttle(request, "realtime", 30)
    key = f"analytics-realtime:{prop.pk}:{prop.revision}"
    value = cache.get(key)
    if value is None:
        value = realtime(prop)
        cache.set(key, value, 30)
    return value


@router.get("/websites/{website_id}/opportunities")
def opportunity_get(
    request: AuthenticatedHttpRequest, website_id: int, start: date, end: date
) -> dict[str, Any]:
    prop = prop_for(request, website_id, "gsc")
    date_window(start, end)
    output = []
    for report, dimension in [("pages", "page"), ("queries", "query")]:
        current = snapshot(prop, report, start, end)
        previous = snapshot(prop, report, *previous_window(start, end))
        if current:
            output.extend(
                opportunities(current["rows"], previous["rows"] if previous else [], dimension)
            )
    ga = prop.website.provider_properties.filter(provider="ga4").first()
    current_pages = snapshot(prop, "pages", start, end)
    previous_pages = snapshot(prop, "pages", *previous_window(start, end))
    engagement = snapshot(ga, "pages", start, end) if ga else None
    if current_pages and previous_pages and engagement:
        prior = {row["page"]: row for row in previous_pages["rows"]}
        ga_pages = {
            normalize_page(
                row.get("pageLocation")
                or f"https://{row['hostName']}{row['pagePathPlusQueryString']}",
                prop.website.domain,
            ): row
            for row in engagement["rows"]
        }
        for row in current_pages["rows"]:
            old = prior.get(row["page"])
            activity = ga_pages.get(normalize_page(row["page"], prop.website.domain))
            if (
                old
                and activity
                and old["impressions"] >= 100
                and row["impressions"] > old["impressions"] * 1.2
                and activity.get("activeUsers", 0) >= 20
                and activity.get("averageEngagementTime") is not None
                and activity["averageEngagementTime"] < 10
            ):
                output.append(
                    {
                        "subject": row["page"],
                        "reasons": [
                            "Search visibility grew by more than 20%, while average engagement stayed below 10 seconds across at least 20 active visitors. Review landing-page relevance. Measurement windows use different provider timezones."
                        ],
                        "heuristic": True,
                        "metrics": row,
                    }
                )
    return {"items": output, "heuristic": True, "minimum_impressions": 100}


@router.get("/websites/{website_id}/combined")
def combined(
    request: AuthenticatedHttpRequest, website_id: int, start: date, end: date, page: str = ""
) -> dict[str, Any]:
    website = website_for(request.user, website_id)
    date_window(start, end)
    data: dict[str, dict[str, Any]] = {}
    available = []
    for prop in website.provider_properties.all():
        result = snapshot(prop, "pages", start, end)
        if not result:
            continue
        available.append(prop.provider)
        for row in result["rows"]:
            url = normalize_page(
                row["page"]
                if prop.provider == "gsc"
                else row.get("pageLocation")
                or f"https://{row['hostName']}{row['pagePathPlusQueryString']}",
                website.domain,
            )
            if page and url != normalize_page(page, website.domain):
                continue
            data.setdefault(url, {"url": url})[prop.provider] = row
    if page:
        selected_url = normalize_page(page, website.domain)
        for prop in website.provider_properties.all():
            for report_name in (
                ["page_trend", "page_events"] if prop.provider == "ga4" else ["page_trend"]
            ):
                stored = snapshot(prop, report_name, start, end)
                if stored is None:
                    continue
                matching = [
                    row
                    for row in stored["rows"]
                    if normalize_page(row.get("pageLocation", row.get("page", "")), website.domain)
                    == selected_url
                ]
                if selected_url in data:
                    data[selected_url][prop.provider + "_" + report_name] = matching
    return {
        "rows": list(data.values()),
        "providers_available": available,
        "notice": "Exact host, path, query and slash matching. Canonical/hostname differences can leave unmatched rows. GA4 uses the property timezone; Search Console uses Pacific Time. Clicks and sessions are separate measures.",
    }


@router.get("/websites/{website_id}/definitions/{kind}")
def definition_list(
    request: AuthenticatedHttpRequest,
    website_id: int,
    kind: Literal["dimensions", "metrics", "key-events"],
) -> dict[str, Any]:
    prop = prop_for(request, website_id, "ga4", "change_eventdefinition")
    throttle(request, "definitions")
    return {"items": definitions(prop, kind), "can_edit": EDIT in prop.connection.scopes}


@router.post("/websites/{website_id}/definitions/{kind}")
def definition_create(
    request: AuthenticatedHttpRequest,
    website_id: int,
    kind: Literal["dimensions", "metrics", "key-events"],
    payload: DefinitionIn,
) -> dict[str, Any]:
    prop = prop_for(request, website_id, "ga4", "change_eventdefinition")
    throttle(request, "definition-write", 10)
    return create_definition(prop, kind, payload.model_dump(), request.user, payload.confirmed)


@router.post("/websites/{website_id}/key-events/delete")
def key_delete(
    request: AuthenticatedHttpRequest, website_id: int, payload: KeyEventDeleteIn
) -> dict[str, bool]:
    prop = prop_for(request, website_id, "ga4", "change_eventdefinition")
    delete_key_event(prop, payload.name, request.user, payload.confirmed)
    return {"deleted": True}


@router.post("/websites/{website_id}/tracking/plan")
def tracking_plan(
    request: AuthenticatedHttpRequest, website_id: int, payload: ParametersIn
) -> dict[str, Any]:
    prop = prop_for(request, website_id, "ga4", "change_eventdefinition")
    return definition_plan(prop, payload.parameters)


@router.post("/websites/{website_id}/tracking/register")
def tracking_register(
    request: AuthenticatedHttpRequest, website_id: int, payload: ParametersIn
) -> dict[str, Any]:
    prop = prop_for(request, website_id, "ga4", "change_eventdefinition")
    throttle(request, "tracking-register", 6)
    plan = definition_plan(prop, payload.parameters)
    if not payload.confirmed:
        raise HttpError(422, "Confirm the definition plan first.")
    created = [
        create_definition(
            prop,
            "dimensions",
            {"parameterName": name, "displayName": name.replace("_", " ")},
            request.user,
            True,
        )
        for name in plan["missing"]
    ]
    website = prop.website
    website.tracking_schema = {**website.tracking_schema, payload.event: payload.parameters}
    website.save(update_fields=["tracking_schema"])
    return {"created": created, "notice": plan["notice"]}


@router.get("/websites/{website_id}/events/{event}/parameters")
def event_parameters(
    request: AuthenticatedHttpRequest,
    website_id: int,
    event: str,
    parameter: str,
    start: date,
    end: date,
) -> dict[str, Any]:
    prop = prop_for(request, website_id, "ga4")
    date_window(start, end)
    throttle(request, "event-parameters", 15)
    registered = prop.definitions.filter(
        kind="dimensions", payload__parameterName=parameter, payload__scope="EVENT"
    ).exists()
    if not registered:
        raise HttpError(
            422,
            "Parameter is not registered or definitions need refreshing. Unregistered parameters cannot be reported.",
        )
    return ga_report(prop, "events", start, end, event=event, parameter="customEvent:" + parameter)


@router.get("/websites/{website_id}/key-events")
def configured_key_events(request: AuthenticatedHttpRequest, website_id: int) -> dict[str, Any]:
    prop = prop_for(request, website_id, "ga4")
    return {
        "items": list(prop.definitions.filter(kind="key-events").values_list("payload", flat=True)),
        "last_synced_at": prop.last_synced_at,
        "error_code": prop.metadata.get("configuration_error", ""),
    }


@router.get("/websites/{website_id}/events/{event}/trend")
def event_trend(
    request: AuthenticatedHttpRequest, website_id: int, event: str, start: date, end: date
) -> dict[str, Any]:
    prop = prop_for(request, website_id, "ga4")
    date_window(start, end)
    stored = snapshot(prop, "event_trend", start, end)
    return {
        "rows": [row for row in stored["rows"] if row.get("eventName") == event] if stored else [],
        "available": stored is not None,
    }


class ConfirmationIn(Schema):
    confirmed: bool = False


@router.delete("/websites/{website_id}/properties/{provider}")
def unlink_property(
    request: AuthenticatedHttpRequest,
    website_id: int,
    provider: Literal["ga4", "gsc"],
    payload: ConfirmationIn,
) -> dict[str, bool]:
    website = website_for(request.user, website_id, "change_googleconnection")
    if not payload.confirmed:
        raise HttpError(
            422, "Confirm unlinking this property and removing its synchronized reports."
        )
    with transaction.atomic():
        prop = get_object_or_404(website.provider_properties.select_for_update(), provider=provider)
        if prop.jobs.filter(status__in=["queued", "running", "retrying"]).exists():
            raise HttpError(
                409, "Wait for the active synchronization before unlinking this property."
            )
        AuditEvent.record(
            action="analytics.property_unlinked",
            actor=request.user,
            target=prop,
            metadata={"provider": provider, "external_id": prop.external_id},
        )
        prop.delete()
    return {"unlinked": True}

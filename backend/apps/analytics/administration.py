"""Confirmed GA4 configuration writes with provider scope and local audit checks."""

import re
from typing import Any

from django.db import transaction
from ninja.errors import HttpError

from apps.analytics.google import ADMIN_URL, EDIT, google_request, paginated
from apps.analytics.models import EventDefinition, ProviderProperty
from apps.core.models import AuditEvent

KINDS = {"dimensions": "customDimensions", "metrics": "customMetrics", "key-events": "keyEvents"}


def definitions(prop: ProviderProperty, kind: str) -> list[dict[str, Any]]:
    resource = KINDS[kind]
    rows = paginated(prop.connection, ADMIN_URL + prop.external_id + "/" + resource, resource)
    with transaction.atomic():
        names = []
        for row in rows:
            names.append(row["name"])
            EventDefinition.objects.update_or_create(
                property=prop, kind=kind, external_name=row["name"], defaults={"payload": row}
            )
        prop.definitions.filter(kind=kind).exclude(external_name__in=names).delete()
    return rows


def definition_plan(prop: ProviderProperty, parameters: list[str]) -> dict[str, Any]:
    existing = definitions(prop, "dimensions")
    registered = {item["parameterName"] for item in existing if item.get("scope") == "EVENT"}
    return {
        "registered": sorted(set(parameters) & registered),
        "missing": sorted(set(parameters) - registered),
        "event_dimensions_used": len(registered),
        "limit": None,
        "notice": "Property tier limits are enforced by Google. Registration is not retroactive; allow 24–48 hours for reporting. Unregistered parameters cannot be discovered using the Data API.",
    }


def create_definition(
    prop: ProviderProperty, kind: str, payload: dict[str, Any], actor: Any, confirmed: bool
) -> dict[str, Any]:
    if not confirmed:
        raise HttpError(422, "Confirm the proposed Google property change.")
    if EDIT not in prop.connection.scopes:
        raise HttpError(403, "Reconnect Google with analytics administration permission.")
    if kind == "key-events":
        name = payload.get("eventName", "")
        body = {"eventName": name}
    else:
        name = payload.get("parameterName", "")
        display = str(payload.get("displayName", "")).strip()
        if not 1 <= len(display) <= 82:
            raise HttpError(422, "Display name must be between 1 and 82 characters.")
        body = {
            "parameterName": name,
            "displayName": display,
            "scope": "EVENT",
            "description": str(payload.get("description", ""))[:150],
        }
        if kind == "metrics":
            unit = payload.get("measurementUnit", "STANDARD")
            if unit not in {
                "STANDARD",
                "CURRENCY",
                "FEET",
                "METERS",
                "KILOMETERS",
                "MILES",
                "MILLISECONDS",
                "SECONDS",
                "MINUTES",
                "HOURS",
            }:
                raise HttpError(422, "Invalid metric measurement unit.")
            body["measurementUnit"] = unit
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,39}", name) or name.startswith(
        ("ga_", "google_", "firebase_")
    ):
        raise HttpError(422, "Use a valid event or parameter name of at most 40 characters.")
    existing = definitions(prop, kind)
    field = "eventName" if kind == "key-events" else "parameterName"
    for row in existing:
        if row.get(field) == name:
            return row
    # Audit intent first: remote changes cannot participate in our database transaction.
    AuditEvent.record(
        action="analytics.google_write_requested",
        actor=actor,
        target=prop,
        metadata={"kind": kind, "parameter": name},
    )
    created = google_request(
        prop.connection, "POST", ADMIN_URL + prop.external_id + "/" + KINDS[kind], body=body
    )
    verified = google_request(prop.connection, "GET", ADMIN_URL + created["name"])
    EventDefinition.objects.update_or_create(
        property=prop, kind=kind, external_name=verified["name"], defaults={"payload": verified}
    )
    AuditEvent.record(
        action="analytics.google_definition_created",
        actor=actor,
        target=prop,
        metadata={"kind": kind, "name": verified["name"]},
    )
    return verified


def delete_key_event(
    prop: ProviderProperty, external_name: str, actor: Any, confirmed: bool
) -> None:
    if not confirmed or EDIT not in prop.connection.scopes:
        raise HttpError(403, "Confirmation and Google administration permission are required.")
    prefix = prop.external_id + "/keyEvents/"
    if not external_name.startswith(prefix) or not external_name.removeprefix(prefix).isdigit():
        raise HttpError(422, "Invalid key event identifier.")
    AuditEvent.record(
        action="analytics.google_key_event_delete_requested",
        actor=actor,
        target=prop,
        metadata={"name": external_name},
    )
    google_request(prop.connection, "DELETE", ADMIN_URL + external_name)
    prop.definitions.filter(external_name=external_name).delete()
    AuditEvent.record(
        action="analytics.google_key_event_deleted",
        actor=actor,
        target=prop,
        metadata={"name": external_name},
    )

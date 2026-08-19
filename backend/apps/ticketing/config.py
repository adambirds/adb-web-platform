from __future__ import annotations

import os

from django.core.exceptions import ImproperlyConfigured

DEFAULT_GRAPH_SYNC_INTERVAL_SECONDS = 60
DEFAULT_GRAPH_SYNC_LOCK_SECONDS = 15 * 60
DEFAULT_MALWARE_SCANNING_ENABLED = False
MIN_GRAPH_SYNC_INTERVAL_SECONDS = 30
MIN_GRAPH_SYNC_LOCK_SECONDS = 60


def graph_sync_interval_seconds() -> int:
    """Return the configured interval between Graph mailbox dispatch rounds."""
    return _configured_seconds(
        "TICKETING_GRAPH_SYNC_INTERVAL_SECONDS",
        default=DEFAULT_GRAPH_SYNC_INTERVAL_SECONDS,
        minimum=MIN_GRAPH_SYNC_INTERVAL_SECONDS,
    )


def graph_sync_lock_seconds() -> int:
    """Return the maximum lifetime of the per-mailbox distributed sync lock."""
    return _configured_seconds(
        "TICKETING_GRAPH_SYNC_LOCK_SECONDS",
        default=DEFAULT_GRAPH_SYNC_LOCK_SECONDS,
        minimum=MIN_GRAPH_SYNC_LOCK_SECONDS,
    )


def malware_scanning_enabled() -> bool:
    """Return whether quarantined attachments must pass malware scanning before download."""
    raw_value = os.environ.get("TICKETING_MALWARE_SCANNING_ENABLED", "").strip().lower()
    if not raw_value:
        return DEFAULT_MALWARE_SCANNING_ENABLED
    if raw_value in {"1", "true", "yes", "on"}:
        return True
    if raw_value in {"0", "false", "no", "off"}:
        return False
    raise ImproperlyConfigured("TICKETING_MALWARE_SCANNING_ENABLED must be a boolean value.")


def _configured_seconds(name: str, *, default: int, minimum: int) -> int:
    raw_value = os.environ.get(name, "").strip()
    if not raw_value:
        return default

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ImproperlyConfigured(f"{name} must be an integer number of seconds.") from exc

    if value < minimum:
        raise ImproperlyConfigured(f"{name} must be at least {minimum} seconds.")
    return value

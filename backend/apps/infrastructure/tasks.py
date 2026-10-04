from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager, suppress

from celery import shared_task
from django.db.models import Q
from django.utils import timezone
from django_redis import get_redis_connection
from redis.exceptions import LockError

from .metadata_refresh import (
    CURRENT_LIFECYCLES,
    ERROR_RETRY_INTERVAL,
    REFRESH_INTERVAL,
    refresh_due,
    refresh_metadata,
)
from .models import DomainProfile, TLSCertificate


@shared_task(name="infrastructure.enqueue_metadata_refreshes", queue="general")
def enqueue_metadata_refreshes() -> int:
    count = 0
    now = timezone.now()
    due = (
        Q(last_metadata_checked_at__isnull=True)
        | Q(metadata_refresh_error="", last_metadata_checked_at__lte=now - REFRESH_INTERVAL)
        | (
            ~Q(metadata_refresh_error="")
            & Q(last_metadata_checked_at__lte=now - ERROR_RETRY_INTERVAL)
        )
    )
    for model in (DomainProfile, TLSCertificate):
        for profile in model.objects.filter(
            due, resource__lifecycle_status__in=CURRENT_LIFECYCLES
        ).iterator():
            if refresh_due(profile):
                refresh_resource_metadata.delay(profile.resource_id)
                count += 1
    return count


@contextmanager
def _metadata_lock(resource_id: int) -> Iterator[bool]:
    lock = get_redis_connection("default").lock(
        f"infrastructure:metadata:{resource_id}", timeout=180, blocking_timeout=0
    )
    acquired = bool(lock.acquire(blocking=False))
    try:
        yield acquired
    finally:
        if acquired:
            with suppress(LockError):
                lock.release()


@shared_task(name="infrastructure.refresh_resource_metadata", queue="general")
def refresh_resource_metadata(resource_id: int) -> None:
    with _metadata_lock(resource_id) as acquired:
        if acquired:
            refresh_metadata(resource_id)

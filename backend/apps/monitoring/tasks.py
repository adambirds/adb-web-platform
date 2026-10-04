from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager, suppress

from celery import shared_task
from django.db.models import Q
from django.utils import timezone
from django_redis import get_redis_connection
from redis.exceptions import LockError

from apps.infrastructure.models import InfrastructureResource

from .execution import execute_check
from .models import MonitorCheck
from .services import record_observation

MONITOR_CHECK_LOCK_PREFIX = "monitoring:check"
MONITOR_CHECK_LOCK_GRACE_SECONDS = 30
MINIMUM_MONITOR_CHECK_LOCK_SECONDS = 60


@shared_task(name="monitoring.enqueue_due_checks", queue="general")
def enqueue_due_checks() -> int:
    due_ids = list(
        MonitorCheck.objects.filter(enabled=True)
        .exclude(
            resource__lifecycle_status__in=[
                InfrastructureResource.LifecycleStatus.RETIRED,
                InfrastructureResource.LifecycleStatus.ARCHIVED,
            ]
        )
        .filter(Q(next_run_at__isnull=True) | Q(next_run_at__lte=timezone.now()))
        .values_list("id", flat=True)
    )
    for check_id in due_ids:
        run_monitor_check.delay(check_id)
    return len(due_ids)


@shared_task(name="monitoring.run_check", queue="general")
def run_monitor_check(check_id: int) -> None:
    check = (
        MonitorCheck.objects.select_related("resource", "credential").filter(id=check_id).first()
    )
    if check is None or not check.enabled:
        return

    with _monitor_check_lock(check) as acquired:
        if not acquired:
            return

        check.refresh_from_db()
        check.resource.refresh_from_db()
        if not check.enabled or check.resource.lifecycle_status in [
            InfrastructureResource.LifecycleStatus.RETIRED,
            InfrastructureResource.LifecycleStatus.ARCHIVED,
        ]:
            return
        if check.next_run_at is not None and check.next_run_at > timezone.now():
            return

        record_observation(check.id, execute_check(check))


@contextmanager
def _monitor_check_lock(check: MonitorCheck) -> Iterator[bool]:
    """Prevent concurrent workers from executing the same scheduled check."""
    redis = get_redis_connection("default")
    lock = redis.lock(
        f"{MONITOR_CHECK_LOCK_PREFIX}:{check.id}",
        timeout=max(
            check.timeout_seconds + MONITOR_CHECK_LOCK_GRACE_SECONDS,
            MINIMUM_MONITOR_CHECK_LOCK_SECONDS,
        ),
        blocking_timeout=0,
    )
    acquired = bool(lock.acquire(blocking=False))
    try:
        yield acquired
    finally:
        if acquired:
            with suppress(LockError):
                lock.release()

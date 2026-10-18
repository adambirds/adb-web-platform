from datetime import timedelta
from typing import Any

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

from apps.analytics.google import ProviderError, access_token
from apps.analytics.models import GoogleConnection, ProviderProperty, SyncJob
from apps.analytics.synchronization import queue_sync, scheduled_window, sync_job


@shared_task(
    bind=True, max_retries=5, name="analytics.synchronize", soft_time_limit=1500, time_limit=1800
)
def synchronize(self: Any, job_id: int) -> None:
    try:
        sync_job(job_id)
    except ProviderError as exc:
        retry = exc.retryable and self.request.retries < self.max_retries
        SyncJob.objects.filter(pk=job_id).update(
            status="retrying" if retry else "failed", error_code=exc.code, updated_at=timezone.now()
        )
        job = SyncJob.objects.get(pk=job_id)
        ProviderProperty.objects.filter(pk=job.property_id).update(error_code=exc.code)
        if retry:
            raise self.retry(exc=exc, countdown=min(60 * 2**self.request.retries, 3600)) from None
    except Exception:
        SyncJob.objects.filter(pk=job_id).update(
            status="failed", error_code="sync_failed", updated_at=timezone.now()
        )
        raise


@shared_task(name="analytics.enqueue_syncs")
def enqueue_syncs() -> None:
    # Recover jobs abandoned by worker termination without scheduling overlapping provider jobs.
    SyncJob.objects.filter(
        status__in=["queued", "running", "retrying"],
        updated_at__lt=timezone.now() - __import__("datetime").timedelta(hours=2),
    ).update(status="failed", error_code="worker_interrupted")
    for prop in ProviderProperty.objects.filter(
        website__is_active=True, connection__status="connected"
    ).iterator():
        queue_sync(prop, *scheduled_window(prop))


@shared_task(
    bind=True,
    max_retries=5,
    name="analytics.refresh_google_token",
    soft_time_limit=90,
    time_limit=120,
)
def refresh_google_token(self: Any, connection_id: int) -> None:
    connection = GoogleConnection.objects.filter(pk=connection_id, status="connected").first()
    if connection is None:
        return
    try:
        access_token(connection, refresh_before=timedelta(minutes=10))
    except ProviderError as exc:
        if exc.retryable and self.request.retries < self.max_retries:
            connection.refresh_from_db()
            delay = (
                max(60, int((connection.refresh_retry_at - timezone.now()).total_seconds()) + 1)
                if connection.refresh_retry_at
                else min(60 * 2**self.request.retries, 3600)
            )
            raise self.retry(exc=exc, countdown=delay) from None


@shared_task(name="analytics.enqueue_token_refreshes")
def enqueue_token_refreshes() -> None:
    now = timezone.now()
    due = (
        GoogleConnection.objects.filter(status="connected")
        .filter(
            Q(expires_at__isnull=True) | Q(expires_at__lte=now + timedelta(minutes=10)),
        )
        .filter(Q(refresh_retry_at__isnull=True) | Q(refresh_retry_at__lte=now))
    )
    for connection_id in due.values_list("pk", flat=True).iterator():
        refresh_google_token.delay(connection_id)

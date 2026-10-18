from typing import Any

from celery import shared_task
from django.utils import timezone

from apps.analytics.google import ProviderError
from apps.analytics.models import ProviderProperty, SyncJob
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

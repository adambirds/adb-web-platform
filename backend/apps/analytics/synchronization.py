"""Durable bounded sync jobs. Exact window snapshots preserve provider metric semantics."""

from datetime import date, timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.analytics.administration import definitions
from apps.analytics.google import ProviderError
from apps.analytics.models import ProviderProperty, ReportSnapshot, SyncJob
from apps.analytics.reports import GA_REPORTS, GSC_REPORTS, ga_report, gsc_report
from apps.analytics.services import date_window, previous_window


def queue_sync(prop: ProviderProperty, start: date, end: date) -> SyncJob:
    date_window(start, end)
    try:
        with transaction.atomic():
            job = SyncJob.objects.create(property=prop, start=start, end=end)
            from apps.analytics.tasks import synchronize

            transaction.on_commit(lambda: synchronize.delay(job.pk))
            return job
    except IntegrityError:
        return SyncJob.objects.get(property=prop, status__in=["queued", "running", "retrying"])


def sync_job(job_id: int) -> None:
    with transaction.atomic():
        job = (
            SyncJob.objects.select_for_update()
            .select_related("property__connection")
            .get(pk=job_id)
        )
        if job.status not in {"queued", "retrying"}:
            return
        job.status = "running"
        job.attempts += 1
        job.save()
    prop = job.property
    if prop.provider == "ga4":
        try:
            for kind in ("dimensions", "metrics", "key-events"):
                definitions(prop, kind)
        except ProviderError as exc:
            if exc.retryable:
                raise
            prop.metadata["configuration_error"] = exc.code
            prop.save(update_fields=["metadata"])
    reports = GA_REPORTS if prop.provider == "ga4" else GSC_REPORTS
    windows = [(job.start, job.end), previous_window(job.start, job.end)]
    completed = 0
    for start, end in windows:
        for report in reports:
            # Keep complete windows atomically, including empty successful responses.
            saved = ReportSnapshot.objects.filter(
                property=prop, report=report, start=start, end=end
            ).first()
            if saved is not None and end < timezone.now().date() - timedelta(days=14):
                completed += 1
                continue
            payload = (
                ga_report(prop, report, start, end)
                if prop.provider == "ga4"
                else gsc_report(
                    prop, report, start, end, search_type=prop.metadata.get("search_type", "web")
                )
            )
            with transaction.atomic():
                locked = ProviderProperty.objects.select_for_update().get(pk=prop.pk)
                if (
                    locked.connection_id != prop.connection_id
                    or locked.external_id != prop.external_id
                ):
                    return
                ReportSnapshot.objects.update_or_create(
                    property=prop,
                    report=report,
                    start=start,
                    end=end,
                    defaults={"payload": payload},
                )
            completed += 1
            SyncJob.objects.filter(pk=job.pk).update(
                progress=completed * 100 // (len(reports) * 2), updated_at=timezone.now()
            )
    with transaction.atomic():
        prop = ProviderProperty.objects.select_for_update().get(pk=prop.pk)
        prop.last_synced_at = timezone.now()
        prop.synced_through = job.end
        prop.error_code = ""
        prop.revision += 1
        backfill = prop.metadata.pop("_backfill_pending", False)
        prop.save()
        SyncJob.objects.filter(pk=job.pk).update(
            status="complete",
            progress=100,
            finished_at=timezone.now(),
            error_code="",
            updated_at=timezone.now(),
        )

    if backfill:
        # One bounded historical backfill follows the useful initial dashboard window.
        queue_sync(prop, job.end - timedelta(days=89), job.end)


def scheduled_window(prop: ProviderProperty) -> tuple[date, date]:
    # Refresh recent provider correction windows; old custom windows remain immutable until requested.
    end = timezone.now().date() - timedelta(days=3)
    return end - timedelta(days=27), end

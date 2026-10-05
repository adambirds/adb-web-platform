from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.core.celery_dashboard.services import RETENTION_DAYS
from apps.core.models import CeleryTaskExecution, CeleryTaskLog


@shared_task(name="core.purge_celery_history")
def purge_celery_history() -> int:
    """Retain incomplete executions; purge only terminal metadata older than 14 days."""
    CeleryTaskLog.objects.filter(
        created_at__lt=timezone.now() - timedelta(days=RETENTION_DAYS)
    ).delete()
    _, counts = CeleryTaskExecution.objects.filter(
        finished_at__lt=timezone.now() - timedelta(days=RETENTION_DAYS),
        state__in=["SUCCESS", "FAILURE", "REVOKED", "IGNORED"],
    ).delete()
    return counts.get("core.CeleryTaskExecution", 0)

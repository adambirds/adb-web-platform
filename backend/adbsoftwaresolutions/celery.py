import logging
import logging.config
import os

from celery import Celery
from celery.signals import setup_logging
from django.conf import settings

from adbsoftwaresolutions.bootsteps import LivenessProbe
from adbsoftwaresolutions.logs import json_enabled
from apps.ticketing.config import graph_sync_interval_seconds

# Setting the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "adbsoftwaresolutions.settings")

app = Celery("ADB Software Solutions")
app.steps["worker"].add(LivenessProbe)

# Configuring Celery with settings from the Django settings.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.beat_schedule = {
    "lead-retention-review": {"task": "crm.refresh_retention_reviews", "schedule": 86400},
    "celery-history-retention": {"task": "core.purge_celery_history", "schedule": 86400},
    "github-delivery-recovery": {"task": "github.recover_deliveries", "schedule": 60},
    "infrastructure-metadata-refresh-dispatch": {
        "task": "infrastructure.enqueue_metadata_refreshes",
        "schedule": 300,
    },
    "monitoring-due-check-dispatch": {
        "task": "monitoring.enqueue_due_checks",
        "schedule": 30,
    },
    "ticketing-graph-mailbox-sync": {
        "task": "ticketing.enqueue_graph_mailbox_syncs",
        "schedule": graph_sync_interval_seconds(),
    },
    "ticketing-attachment-scan-dispatch": {
        "task": "ticketing.enqueue_attachment_scans",
        "schedule": 60,
    },
    "knowledge-base-attachment-scan-dispatch": {
        "task": "knowledge_base.enqueue_attachment_scans",
        "schedule": 60,
    },
}
app.conf.timezone = "UTC"

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

if json_enabled():
    # JSON lines (adbsoftwaresolutions/logs.py) from the worker and beat too: with a
    # receiver for this signal, Celery leaves logging to it.
    @setup_logging.connect
    def use_django_logging(**kwargs: object) -> None:
        logging.config.dictConfig(settings.LOGGING)

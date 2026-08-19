import logging
import os

from celery import Celery
from django.conf import settings

from adbsoftwaresolutions.bootsteps import LivenessProbe
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
    "ticketing-graph-mailbox-sync": {
        "task": "ticketing.enqueue_graph_mailbox_syncs",
        "schedule": graph_sync_interval_seconds(),
    },
    "ticketing-attachment-scan-dispatch": {
        "task": "ticketing.enqueue_attachment_scans",
        "schedule": 60,
    },
}
app.conf.timezone = "UTC"

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

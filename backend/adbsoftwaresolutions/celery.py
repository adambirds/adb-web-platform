import logging
import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

from adbsoftwaresolutions.bootsteps import LivenessProbe

# Setting the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "adbsoftwaresolutions.settings")

app = Celery("ADB Software Solutions")
app.steps["worker"].add(LivenessProbe)

# Configuring Celery with settings from the Django settings.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Define the Celery beat schedule if any.
app.conf.beat_schedule = {
    
}
app.conf.timezone = "UTC"

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

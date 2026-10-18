import logging

from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.analytics"

    def ready(self) -> None:
        from adbsoftwaresolutions.logs import OAuthCallbackLogFilter

        for name in ("uvicorn.access", "gunicorn.access", "django.server", "django.request"):
            logger = logging.getLogger(name)
            if not any(isinstance(item, OAuthCallbackLogFilter) for item in logger.filters):
                logger.addFilter(OAuthCallbackLogFilter())

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Platform Core"

    def ready(self) -> None:
        from .live.signals import register

        register()

        from .celery_dashboard.signals import register as register_celery_telemetry

        register_celery_telemetry()

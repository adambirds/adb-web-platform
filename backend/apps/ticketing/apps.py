from django.apps import AppConfig


class TicketingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ticketing"

    def ready(self) -> None:
        from apps.ticketing import signals  # noqa: F401

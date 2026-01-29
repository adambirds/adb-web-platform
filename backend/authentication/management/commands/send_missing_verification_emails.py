from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from authentication.models import User  # Adjust path as needed
from authentication.tasks import send_missing_initial_verification_email  # Adjust path as needed


class Command(BaseCommand):
    help = "Resend verification emails to users who are not verified, regardless of existing token"

    def handle(self, *args: str, **options: dict[str, Any]) -> None:
        users = User.objects.filter(
            is_active=True,
            email__isnull=False,
            email_verified=False,
        )

        if not users.exists():
            self.stdout.write(self.style.SUCCESS("No unverified users found."))
            return

        for user in users:
            # Optionally: regenerate token if needed (comment out if you want to keep old one)
            user.verification_token = user.generate_verification_token()
            user.last_verification_email_sent = timezone.now()
            user.save(update_fields=["verification_token", "last_verification_email_sent"])

            send_missing_initial_verification_email.delay(
                user.email,
                user.first_name,
                user.verification_token,
            )

            self.stdout.write(self.style.SUCCESS(f"Queued email for {user.email}"))

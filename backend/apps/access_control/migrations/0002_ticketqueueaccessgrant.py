from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("access_control", "0001_initial"),
        ("ticketing", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TicketQueueAccessGrant",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "granted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ticket_queue_access_grants_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ticket_queue_grants",
                        to="access_control.staffaccessprofile",
                    ),
                ),
                (
                    "queue",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="access_grants",
                        to="ticketing.ticketqueue",
                    ),
                ),
            ],
            options={
                "ordering": ["queue__ordering", "queue__name"],
            },
        ),
        migrations.AddConstraint(
            model_name="ticketqueueaccessgrant",
            constraint=models.UniqueConstraint(
                fields=("profile", "queue"),
                name="unique_staff_ticket_queue_access_grant",
            ),
        ),
    ]

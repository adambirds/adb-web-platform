from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("clients", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="StaffAccessProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "all_clients",
                    models.BooleanField(
                        default=False,
                        help_text="Allow access to every client when the user also has the required capability permission.",
                    ),
                ),
                (
                    "all_ticket_queues",
                    models.BooleanField(
                        default=False,
                        help_text="Reserved for ticketing; selected queue grants will be added with the ticket domain.",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="access_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "permissions": [("manage_staff_access", "Can manage staff access scopes")],
            },
        ),
        migrations.CreateModel(
            name="ClientAccessGrant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="access_grants",
                        to="clients.client",
                    ),
                ),
                (
                    "granted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="client_access_grants_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="client_grants",
                        to="access_control.staffaccessprofile",
                    ),
                ),
            ],
            options={
                "ordering": ["client__name"],
            },
        ),
        migrations.AddConstraint(
            model_name="clientaccessgrant",
            constraint=models.UniqueConstraint(
                fields=("profile", "client"),
                name="unique_staff_client_access_grant",
            ),
        ),
    ]

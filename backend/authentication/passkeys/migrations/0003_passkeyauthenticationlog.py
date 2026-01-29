# Generated migration for PasskeyAuthenticationLog

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("authentication", "0002_passkeychallenge"),
    ]

    operations = [
        migrations.CreateModel(
            name="PasskeyAuthenticationLog",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("authentication_started", "Authentication Started"),
                            ("authentication_success", "Authentication Success"),
                            ("authentication_failed", "Authentication Failed"),
                            ("registration_started", "Registration Started"),
                            ("registration_success", "Registration Success"),
                            ("registration_failed", "Registration Failed"),
                        ],
                        max_length=50,
                        verbose_name="event type",
                    ),
                ),
                (
                    "ip_address",
                    models.GenericIPAddressField(blank=True, null=True, verbose_name="IP address"),
                ),
                ("user_agent", models.TextField(blank=True, verbose_name="user agent")),
                (
                    "failure_reason",
                    models.CharField(blank=True, max_length=255, verbose_name="failure reason"),
                ),
                ("passkey_id", models.UUIDField(blank=True, null=True, verbose_name="passkey ID")),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, db_index=True, verbose_name="created at"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="passkey_auth_logs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
            ],
            options={
                "verbose_name": "passkey authentication log",
                "verbose_name_plural": "passkey authentication logs",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["-created_at"], name="auth_passkey_log_created_idx"),
                    models.Index(fields=["user", "-created_at"], name="auth_passkey_log_user_idx"),
                    models.Index(
                        fields=["event_type", "-created_at"], name="auth_passkey_log_event_idx"
                    ),
                ],
            },
        ),
    ]

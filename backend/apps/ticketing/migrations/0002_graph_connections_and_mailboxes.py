import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
        ("credentials", "0003_credential_ownership"),
        ("ticketing", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MicrosoftGraphConnection",
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
                ("name", models.CharField(max_length=160)),
                ("tenant_id", models.CharField(max_length=255)),
                ("client_id", models.CharField(max_length=255)),
                (
                    "authentication_method",
                    models.CharField(
                        choices=[
                            ("certificate", "Certificate"),
                            ("client_secret", "Client secret"),
                            ("delegated", "Delegated OAuth"),
                        ],
                        default="certificate",
                        max_length=32,
                    ),
                ),
                ("enabled", models.BooleanField(default=True)),
                ("last_verified_at", models.DateTimeField(blank=True, null=True)),
                ("last_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "credential",
                    models.ForeignKey(
                        blank=True,
                        help_text=(
                            "Internal credential containing the certificate/private key or client secret."
                        ),
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="microsoft_graph_connections",
                        to="credentials.storedcredential",
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
                "permissions": [
                    (
                        "configure_graph_connections",
                        "Can configure Microsoft Graph connections",
                    )
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="microsoftgraphconnection",
            constraint=models.UniqueConstraint(
                fields=("tenant_id", "client_id"),
                name="unique_graph_tenant_client",
            ),
        ),
        migrations.CreateModel(
            name="Mailbox",
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
                ("email_address", models.EmailField(max_length=254)),
                ("display_name", models.CharField(blank=True, max_length=255)),
                ("graph_user_id", models.CharField(blank=True, max_length=255)),
                (
                    "purpose",
                    models.CharField(
                        choices=[
                            ("support", "Support"),
                            ("sales", "Sales"),
                            ("accounts", "Accounts"),
                            ("operations", "Operations"),
                            ("general", "General"),
                        ],
                        default="support",
                        max_length=24,
                    ),
                ),
                ("enabled", models.BooleanField(default=True)),
                ("delta_link", models.TextField(blank=True)),
                ("last_synced_at", models.DateTimeField(blank=True, null=True)),
                ("last_successful_sync_at", models.DateTimeField(blank=True, null=True)),
                ("last_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "brand",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ticket_mailboxes",
                        to="core.brand",
                    ),
                ),
                (
                    "default_queue",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="mailboxes",
                        to="ticketing.ticketqueue",
                    ),
                ),
                (
                    "graph_connection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="mailboxes",
                        to="ticketing.microsoftgraphconnection",
                    ),
                ),
            ],
            options={
                "ordering": ["brand__name", "email_address"],
                "permissions": [
                    ("configure_mailboxes", "Can configure ticket mailboxes"),
                    ("sync_mailbox", "Can trigger mailbox synchronisation"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="mailbox",
            constraint=models.UniqueConstraint(
                fields=("graph_connection", "email_address"),
                name="unique_graph_mailbox_address",
            ),
        ),
        migrations.AddField(
            model_name="ticket",
            name="mailbox",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="tickets",
                to="ticketing.mailbox",
            ),
        ),
    ]

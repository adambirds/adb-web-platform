import django.db.models.deletion
from django.db import migrations, models


INITIAL_VENDORS = (
    ("GitHub", "github.com"),
    ("DigitalOcean", "digitalocean.com"),
    ("PayPal", "paypal.com"),
    ("Microsoft", "microsoft.com"),
    ("Elegant Themes", "elegantthemes.com"),
    ("Google", "google.com"),
    ("Wordfence", "wordfence.com"),
    ("LastPass", "lastpass.com"),
)


def seed_vendor_routing(apps, schema_editor):
    TicketQueue = apps.get_model("ticketing", "TicketQueue")
    Vendor = apps.get_model("ticketing", "Vendor")
    VendorSenderRule = apps.get_model("ticketing", "VendorSenderRule")

    queue, _ = TicketQueue.objects.update_or_create(
        key="vendors-services",
        defaults={
            "name": "Vendors & Services",
            "brand": None,
            "purpose": "Vendor and third-party service correspondence",
            "default_priority": "low",
            "enabled": True,
            "ordering": 80,
        },
    )
    for name, domain in INITIAL_VENDORS:
        vendor, _ = Vendor.objects.update_or_create(
            name=name,
            defaults={"enabled": True},
        )
        VendorSenderRule.objects.update_or_create(
            match_type="domain",
            match_value=domain,
            defaults={
                "vendor": vendor,
                "target_queue": queue,
                "priority": "low",
                "enabled": True,
            },
        )


def unseed_vendor_routing(apps, schema_editor):
    Vendor = apps.get_model("ticketing", "Vendor")
    Vendor.objects.filter(name__in=[name for name, _ in INITIAL_VENDORS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("ticketing", "0004_ticketattachment_provider_metadata"),
    ]

    operations = [
        migrations.CreateModel(
            name="Vendor",
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
                ("name", models.CharField(max_length=160, unique=True)),
                ("website_url", models.URLField(blank=True)),
                ("notes", models.TextField(blank=True)),
                ("enabled", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["name"],
                "permissions": [("configure_vendors", "Can configure ticket vendors")],
            },
        ),
        migrations.AddField(
            model_name="ticket",
            name="vendor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="tickets",
                to="ticketing.vendor",
            ),
        ),
        migrations.CreateModel(
            name="VendorSenderRule",
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
                (
                    "match_type",
                    models.CharField(
                        choices=[
                            ("email", "Exact email address"),
                            ("domain", "Email domain"),
                        ],
                        max_length=16,
                    ),
                ),
                ("match_value", models.CharField(max_length=320)),
                (
                    "priority",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("low", "Low"),
                            ("normal", "Normal"),
                            ("high", "High"),
                            ("urgent", "Urgent"),
                        ],
                        max_length=20,
                    ),
                ),
                ("enabled", models.BooleanField(default=True)),
                ("ordering", models.PositiveIntegerField(default=0)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "target_queue",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="vendor_sender_rules",
                        to="ticketing.ticketqueue",
                    ),
                ),
                (
                    "vendor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sender_rules",
                        to="ticketing.vendor",
                    ),
                ),
            ],
            options={
                "ordering": ["ordering", "vendor__name", "match_value"],
            },
        ),
        migrations.AddConstraint(
            model_name="vendorsenderrule",
            constraint=models.UniqueConstraint(
                fields=("match_type", "match_value"),
                name="unique_vendor_sender_rule",
            ),
        ),
        migrations.RunPython(seed_vendor_routing, unseed_vendor_routing),
    ]

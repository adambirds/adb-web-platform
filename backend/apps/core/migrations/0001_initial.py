from typing import Any

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


BRANDS = [
    {
        "name": "ADB Software Solutions",
        "slug": "adb-software-solutions",
        "domain": "adbsoftwaresolutions.co.uk",
    },
    {
        "name": "ADB Web Designs",
        "slug": "adb-web-designs",
        "domain": "adbwebdesigns.co.uk",
    },
    {
        "name": "ADB Technology",
        "slug": "adb-technology",
        "domain": "adbtechnology.co.uk",
    },
]


def create_initial_brands(apps: Any, schema_editor: Any) -> None:
    Brand = apps.get_model("core", "Brand")
    for brand in BRANDS:
        Brand.objects.update_or_create(slug=brand["slug"], defaults=brand)


def remove_initial_brands(apps: Any, schema_editor: Any) -> None:
    Brand = apps.get_model("core", "Brand")
    Brand.objects.filter(slug__in=[brand["slug"] for brand in BRANDS]).delete()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Brand",
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
                ("name", models.CharField(max_length=150)),
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("domain", models.CharField(max_length=255, unique=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="AuditEvent",
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
                ("action", models.CharField(max_length=150)),
                ("target_type", models.CharField(blank=True, max_length=150)),
                ("target_id", models.CharField(blank=True, max_length=255)),
                ("target_label", models.CharField(blank=True, max_length=255)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "permissions": [
                    ("view_sensitive_audit_metadata", "Can view sensitive audit metadata")
                ],
            },
        ),
        migrations.RunPython(create_initial_brands, remove_initial_brands),
    ]

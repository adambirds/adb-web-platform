from typing import Any

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def populate_time_entry_clients(apps: Any, schema_editor: Any) -> None:
    TimeEntry = apps.get_model("clients", "TimeEntry")
    for entry in TimeEntry.objects.select_related("project").all().iterator():
        if entry.project_id:
            entry.client_id = entry.project.client_id
            entry.save(update_fields=["client_id"])


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("clients", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="clientcontact",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="clientcontact",
            name="is_billing",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="clientcontact",
            name="is_primary",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="clientcontact",
            name="is_technical",
            field=models.BooleanField(default=False),
        ),
        migrations.AddConstraint(
            model_name="clientcontact",
            constraint=models.UniqueConstraint(
                fields=("client", "email"),
                name="unique_client_contact_email",
            ),
        ),
        migrations.AlterField(
            model_name="project",
            name="client",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="projects",
                to="clients.client",
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="ownership_type",
            field=models.CharField(
                choices=[("internal", "Internal"), ("client", "Client")],
                default="client",
                max_length=20,
            ),
        ),
        migrations.AddConstraint(
            model_name="project",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(("client__isnull", True), ("ownership_type", "internal"))
                    | models.Q(("client__isnull", False), ("ownership_type", "client"))
                ),
                name="project_valid_ownership",
            ),
        ),
        migrations.AlterField(
            model_name="timeentry",
            name="project",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="time_entries",
                to="clients.project",
            ),
        ),
        migrations.AddField(
            model_name="timeentry",
            name="client",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="time_entries",
                to="clients.client",
            ),
        ),
        migrations.AddField(
            model_name="timeentry",
            name="ownership_type",
            field=models.CharField(
                choices=[("internal", "Internal"), ("client", "Client")],
                default="client",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="timeentry",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="time_entries",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(populate_time_entry_clients, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="timeentry",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(("client__isnull", True), ("ownership_type", "internal"))
                    | models.Q(("client__isnull", False), ("ownership_type", "client"))
                ),
                name="timeentry_valid_ownership",
            ),
        ),
        migrations.AddField(
            model_name="projectnote",
            name="author",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="project_notes",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]

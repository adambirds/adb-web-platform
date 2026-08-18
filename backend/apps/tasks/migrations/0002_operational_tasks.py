import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("clients", "0002_operational_ownership"),
        ("tasks", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="tasklist",
            name="client",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="task_lists",
                to="clients.client",
            ),
        ),
        migrations.AddField(
            model_name="tasklist",
            name="ownership_type",
            field=models.CharField(
                choices=[("internal", "Internal"), ("client", "Client")],
                default="internal",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="tasklist",
            name="project",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="task_lists",
                to="clients.project",
            ),
        ),
        migrations.AddConstraint(
            model_name="tasklist",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(("client__isnull", True), ("ownership_type", "internal"))
                    | models.Q(("client__isnull", False), ("ownership_type", "client"))
                ),
                name="tasklist_valid_ownership",
            ),
        ),
        migrations.AlterField(
            model_name="task",
            name="task_list",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="tasks",
                to="tasks.tasklist",
            ),
        ),
        migrations.AddField(
            model_name="task",
            name="assigned_to",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assigned_tasks",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="task",
            name="client",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tasks",
                to="clients.client",
            ),
        ),
        migrations.AddField(
            model_name="task",
            name="completed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="task",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_tasks",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="task",
            name="next_occurrence_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="task",
            name="ownership_type",
            field=models.CharField(
                choices=[("internal", "Internal"), ("client", "Client")],
                default="internal",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="task",
            name="project",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tasks",
                to="clients.project",
            ),
        ),
        migrations.AddField(
            model_name="task",
            name="recurrence_rule",
            field=models.CharField(
                blank=True,
                help_text="Optional iCalendar RRULE for recurring tasks.",
                max_length=500,
            ),
        ),
        migrations.AddConstraint(
            model_name="task",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(("client__isnull", True), ("ownership_type", "internal"))
                    | models.Q(("client__isnull", False), ("ownership_type", "client"))
                ),
                name="task_valid_ownership",
            ),
        ),
    ]

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("clients", "0002_operational_ownership"),
        ("knowledge_base", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="knowledgebasedocument",
            name="client",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="knowledge_base_documents",
                to="clients.client",
            ),
        ),
        migrations.AddField(
            model_name="knowledgebasedocument",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="knowledge_base_documents_created",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="knowledgebasedocument",
            name="is_portal_visible",
            field=models.BooleanField(
                default=False,
                help_text="Reserved for future client-portal visibility. Private by default.",
            ),
        ),
        migrations.AddField(
            model_name="knowledgebasedocument",
            name="ownership_type",
            field=models.CharField(
                choices=[("internal", "Internal"), ("client", "Client")],
                default="internal",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="knowledgebasedocument",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="knowledge_base_documents_updated",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddConstraint(
            model_name="knowledgebasedocument",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(("client__isnull", True), ("ownership_type", "internal"))
                    | models.Q(("client__isnull", False), ("ownership_type", "client"))
                ),
                name="knowledge_document_valid_ownership",
            ),
        ),
        migrations.AddField(
            model_name="documentversion",
            name="editor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="knowledge_base_versions",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddConstraint(
            model_name="documentversion",
            constraint=models.UniqueConstraint(
                fields=("document", "version_number"),
                name="unique_document_version_number",
            ),
        ),
    ]

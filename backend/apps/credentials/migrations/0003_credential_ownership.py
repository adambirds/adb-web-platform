import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0002_operational_ownership"),
        ("credentials", "0002_credential_secret_permissions"),
    ]

    operations = [
        migrations.AddField(
            model_name="storedcredential",
            name="client",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="credentials",
                to="clients.client",
            ),
        ),
        migrations.AddField(
            model_name="storedcredential",
            name="expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="storedcredential",
            name="last_rotated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="storedcredential",
            name="ownership_type",
            field=models.CharField(
                choices=[("internal", "Internal"), ("client", "Client")],
                default="internal",
                max_length=20,
            ),
        ),
        migrations.AddConstraint(
            model_name="storedcredential",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(("client__isnull", True), ("ownership_type", "internal"))
                    | models.Q(("client__isnull", False), ("ownership_type", "client"))
                ),
                name="storedcredential_valid_ownership",
            ),
        ),
    ]

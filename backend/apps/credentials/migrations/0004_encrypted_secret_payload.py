from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("credentials", "0003_credential_ownership"),
    ]

    operations = [
        migrations.AddField(
            model_name="storedcredential",
            name="encrypted_secret_payload",
            field=models.TextField(blank=True, editable=False),
        ),
        migrations.AddField(
            model_name="storedcredential",
            name="secret_payload_version",
            field=models.PositiveSmallIntegerField(default=1, editable=False),
        ),
    ]

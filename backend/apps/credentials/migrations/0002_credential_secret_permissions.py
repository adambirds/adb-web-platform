from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("credentials", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="storedcredential",
            options={
                "ordering": ["-created_at"],
                "permissions": [
                    ("reveal_storedcredential", "Can reveal stored credential secrets"),
                    ("copy_storedcredential_secret", "Can copy stored credential secrets"),
                ],
            },
        ),
    ]

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
        ("crm", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="lead",
            name="brand",
            field=models.ForeignKey(
                blank=True,
                help_text="ADB brand through which this lead originated.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="leads",
                to="core.brand",
            ),
        ),
    ]

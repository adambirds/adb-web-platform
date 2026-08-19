from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ticketing", "0003_ticketmessage_provider_reply_to_message_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="ticketattachment",
            name="content_id",
            field=models.CharField(blank=True, max_length=512),
        ),
        migrations.AddField(
            model_name="ticketattachment",
            name="is_inline",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="ticketattachment",
            name="provider_attachment_id",
            field=models.CharField(blank=True, db_index=True, max_length=512),
        ),
        migrations.AddConstraint(
            model_name="ticketattachment",
            constraint=models.UniqueConstraint(
                condition=~models.Q(provider_attachment_id=""),
                fields=("message", "provider_attachment_id"),
                name="uniq_msg_provider_attachment",
            ),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ticketing", "0002_graph_connections_and_mailboxes"),
    ]

    operations = [
        migrations.AddField(
            model_name="ticketmessage",
            name="provider_reply_to_message_id",
            field=models.CharField(blank=True, db_index=True, max_length=512),
        ),
    ]

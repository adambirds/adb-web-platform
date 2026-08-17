from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0011_add_user_session"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="ebay_account_not_yet_linked_email_sent",
        ),
    ]

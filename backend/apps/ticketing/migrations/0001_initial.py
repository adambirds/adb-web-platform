import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("clients", "0002_operational_ownership"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TicketQueue",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("key", models.SlugField(max_length=80, unique=True)),
                ("purpose", models.CharField(blank=True, max_length=120)),
                ("default_priority", models.CharField(default="normal", max_length=20)),
                ("enabled", models.BooleanField(default=True)),
                ("ordering", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "brand",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ticket_queues",
                        to="core.brand",
                    ),
                ),
            ],
            options={
                "ordering": ["ordering", "name"],
                "permissions": [("configure_ticket_queues", "Can configure ticket queues")],
            },
        ),
        migrations.CreateModel(
            name="Ticket",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reference", models.CharField(db_index=True, editable=False, max_length=24, unique=True)),
                ("subject", models.CharField(max_length=500)),
                ("status", models.CharField(choices=[("new", "New"), ("open", "Open"), ("waiting_customer", "Waiting for customer"), ("waiting_internal", "Waiting internally"), ("resolved", "Resolved"), ("closed", "Closed"), ("spam", "Spam")], db_index=True, default="new", max_length=32)),
                ("priority", models.CharField(choices=[("low", "Low"), ("normal", "Normal"), ("high", "High"), ("urgent", "Urgent")], db_index=True, default="normal", max_length=20)),
                ("classification", models.CharField(choices=[("client_support", "Client support"), ("sales", "Sales"), ("accounts", "Accounts"), ("vendor", "Vendor"), ("automated_system", "Automated system"), ("monitoring", "Monitoring"), ("newsletter_marketing", "Newsletter / marketing"), ("probable_spam", "Probable spam"), ("unknown", "Unknown")], db_index=True, default="unknown", max_length=40)),
                ("source", models.CharField(choices=[("email", "Email"), ("contact_form", "Contact form"), ("api", "API"), ("manual", "Manual")], default="email", max_length=24)),
                ("first_response_at", models.DateTimeField(blank=True, null=True)),
                ("last_message_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_tickets", to=settings.AUTH_USER_MODEL)),
                ("brand", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="tickets", to="core.brand")),
                ("client", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tickets", to="clients.client")),
                ("primary_contact", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tickets", to="clients.clientcontact")),
                ("queue", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="tickets", to="ticketing.ticketqueue")),
            ],
            options={
                "ordering": ["-last_message_at", "-created_at"],
                "permissions": [
                    ("reply_ticket", "Can reply to tickets"),
                    ("add_ticket_note", "Can add internal ticket notes"),
                    ("assign_ticket", "Can assign tickets"),
                    ("close_ticket", "Can close and reopen tickets"),
                    ("view_ticket_attachment", "Can view safe ticket attachments"),
                ],
            },
        ),
        migrations.CreateModel(
            name="TicketMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("direction", models.CharField(choices=[("inbound", "Inbound"), ("outbound", "Outbound")], max_length=16)),
                ("sender_name", models.CharField(blank=True, max_length=255)),
                ("sender_address", models.EmailField(max_length=254)),
                ("to_recipients", models.JSONField(blank=True, default=list)),
                ("cc_recipients", models.JSONField(blank=True, default=list)),
                ("bcc_recipients", models.JSONField(blank=True, default=list)),
                ("subject", models.CharField(blank=True, max_length=500)),
                ("body_html", models.TextField(blank=True)),
                ("body_text", models.TextField(blank=True)),
                ("body_text_normalised", models.TextField(blank=True)),
                ("provider", models.CharField(blank=True, max_length=40)),
                ("provider_message_id", models.CharField(blank=True, max_length=512, null=True, unique=True)),
                ("internet_message_id", models.CharField(blank=True, db_index=True, max_length=512)),
                ("in_reply_to", models.CharField(blank=True, db_index=True, max_length=512)),
                ("references", models.JSONField(blank=True, default=list)),
                ("sent_or_received_at", models.DateTimeField(db_index=True)),
                ("delivery_status", models.CharField(blank=True, max_length=40)),
                ("delivery_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ticket_messages", to=settings.AUTH_USER_MODEL)),
                ("matched_contact", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ticket_messages", to="clients.clientcontact")),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="ticketing.ticket")),
            ],
            options={"ordering": ["sent_or_received_at", "created_at"]},
        ),
        migrations.CreateModel(
            name="TicketNote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("author", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ticket_notes", to=settings.AUTH_USER_MODEL)),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notes", to="ticketing.ticket")),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.CreateModel(
            name="TicketAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("original_filename", models.CharField(max_length=255)),
                ("storage_key", models.CharField(blank=True, max_length=500)),
                ("declared_content_type", models.CharField(blank=True, max_length=255)),
                ("detected_content_type", models.CharField(blank=True, max_length=255)),
                ("size", models.PositiveBigIntegerField(default=0)),
                ("sha256", models.CharField(blank=True, db_index=True, max_length=64)),
                ("scan_status", models.CharField(choices=[("pending", "Pending"), ("scanning", "Scanning"), ("safe", "Safe"), ("infected", "Infected"), ("scan_failed", "Scan failed"), ("blocked", "Blocked by policy")], db_index=True, default="pending", max_length=24)),
                ("scan_engine", models.CharField(blank=True, max_length=80)),
                ("scan_result", models.TextField(blank=True)),
                ("quarantined_at", models.DateTimeField(blank=True, null=True)),
                ("scanned_at", models.DateTimeField(blank=True, null=True)),
                ("safe_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("message", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="ticketing.ticketmessage")),
            ],
        ),
    ]

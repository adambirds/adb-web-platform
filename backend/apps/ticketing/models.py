from __future__ import annotations

import uuid
from typing import Any

from django.conf import settings
from django.db import models

from apps.clients.models import Client, ClientContact
from apps.core.models import Brand


class MicrosoftGraphConnection(models.Model):
    """Tenant/application-level Microsoft Graph configuration.

    Secret material is referenced through the platform credential store rather
    than duplicated on the Graph connection record.
    """

    class AuthenticationMethod(models.TextChoices):
        CERTIFICATE = "certificate", "Certificate"
        CLIENT_SECRET = "client_secret", "Client secret"
        DELEGATED = "delegated", "Delegated OAuth"

    name = models.CharField(max_length=160)
    tenant_id = models.CharField(max_length=255)
    client_id = models.CharField(max_length=255)
    authentication_method = models.CharField(
        max_length=32,
        choices=AuthenticationMethod.choices,
        default=AuthenticationMethod.CERTIFICATE,
    )
    credential = models.ForeignKey(
        "credentials.StoredCredential",
        on_delete=models.PROTECT,
        related_name="microsoft_graph_connections",
        null=True,
        blank=True,
        help_text="Internal credential containing the certificate/private key or client secret.",
    )
    enabled = models.BooleanField(default=True)
    last_verified_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "client_id"],
                name="unique_graph_tenant_client",
            )
        ]
        permissions = [
            ("configure_graph_connections", "Can configure Microsoft Graph connections"),
        ]

    def __str__(self) -> str:
        return self.name


class TicketQueue(models.Model):
    name = models.CharField(max_length=120)
    key = models.SlugField(max_length=80, unique=True)
    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name="ticket_queues",
        null=True,
        blank=True,
    )
    purpose = models.CharField(max_length=120, blank=True)
    default_priority = models.CharField(max_length=20, default="normal")
    enabled = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ordering", "name"]
        permissions = [
            ("configure_ticket_queues", "Can configure ticket queues"),
        ]

    def __str__(self) -> str:
        return self.name


class Mailbox(models.Model):
    """One Microsoft 365 mailbox ingested into ticketing."""

    class Purpose(models.TextChoices):
        SUPPORT = "support", "Support"
        SALES = "sales", "Sales"
        ACCOUNTS = "accounts", "Accounts"
        OPERATIONS = "operations", "Operations"
        GENERAL = "general", "General"

    graph_connection = models.ForeignKey(
        MicrosoftGraphConnection,
        on_delete=models.PROTECT,
        related_name="mailboxes",
    )
    email_address = models.EmailField()
    display_name = models.CharField(max_length=255, blank=True)
    graph_user_id = models.CharField(max_length=255, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="ticket_mailboxes")
    purpose = models.CharField(max_length=24, choices=Purpose.choices, default=Purpose.SUPPORT)
    default_queue = models.ForeignKey(
        TicketQueue,
        on_delete=models.PROTECT,
        related_name="mailboxes",
    )
    enabled = models.BooleanField(default=True)
    delta_link = models.TextField(blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    last_successful_sync_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["brand__name", "email_address"]
        constraints = [
            models.UniqueConstraint(
                fields=["graph_connection", "email_address"],
                name="unique_graph_mailbox_address",
            )
        ]
        permissions = [
            ("configure_mailboxes", "Can configure ticket mailboxes"),
            ("sync_mailbox", "Can trigger mailbox synchronisation"),
        ]

    def __str__(self) -> str:
        return self.display_name or self.email_address


class Ticket(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        OPEN = "open", "Open"
        WAITING_CUSTOMER = "waiting_customer", "Waiting for customer"
        WAITING_INTERNAL = "waiting_internal", "Waiting internally"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"
        SPAM = "spam", "Spam"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    class Classification(models.TextChoices):
        CLIENT_SUPPORT = "client_support", "Client support"
        SALES = "sales", "Sales"
        ACCOUNTS = "accounts", "Accounts"
        VENDOR = "vendor", "Vendor"
        AUTOMATED_SYSTEM = "automated_system", "Automated system"
        MONITORING = "monitoring", "Monitoring"
        NEWSLETTER_MARKETING = "newsletter_marketing", "Newsletter / marketing"
        PROBABLE_SPAM = "probable_spam", "Probable spam"
        UNKNOWN = "unknown", "Unknown"

    class Source(models.TextChoices):
        EMAIL = "email", "Email"
        CONTACT_FORM = "contact_form", "Contact form"
        API = "api", "API"
        MANUAL = "manual", "Manual"

    reference = models.CharField(max_length=24, unique=True, editable=False, db_index=True)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="tickets")
    queue = models.ForeignKey(TicketQueue, on_delete=models.PROTECT, related_name="tickets")
    mailbox = models.ForeignKey(
        Mailbox,
        on_delete=models.PROTECT,
        related_name="tickets",
        null=True,
        blank=True,
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        related_name="tickets",
        null=True,
        blank=True,
    )
    primary_contact = models.ForeignKey(
        ClientContact,
        on_delete=models.SET_NULL,
        related_name="tickets",
        null=True,
        blank=True,
    )
    subject = models.CharField(max_length=500)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL,
        db_index=True,
    )
    classification = models.CharField(
        max_length=40,
        choices=Classification.choices,
        default=Classification.UNKNOWN,
        db_index=True,
    )
    source = models.CharField(max_length=24, choices=Source.choices, default=Source.EMAIL)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_tickets",
        null=True,
        blank=True,
    )
    first_response_at = models.DateTimeField(null=True, blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_message_at", "-created_at"]
        permissions = [
            ("reply_ticket", "Can reply to tickets"),
            ("add_ticket_note", "Can add internal ticket notes"),
            ("assign_ticket", "Can assign tickets"),
            ("close_ticket", "Can close and reopen tickets"),
            ("view_ticket_attachment", "Can view safe ticket attachments"),
        ]

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.reference:
            self.reference = f"ADB-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.reference}: {self.subject}"


class TicketMessage(models.Model):
    class Direction(models.TextChoices):
        INBOUND = "inbound", "Inbound"
        OUTBOUND = "outbound", "Outbound"

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="messages")
    direction = models.CharField(max_length=16, choices=Direction.choices)
    sender_name = models.CharField(max_length=255, blank=True)
    sender_address = models.EmailField()
    to_recipients = models.JSONField(default=list, blank=True)
    cc_recipients = models.JSONField(default=list, blank=True)
    bcc_recipients = models.JSONField(default=list, blank=True)
    matched_contact = models.ForeignKey(
        ClientContact,
        on_delete=models.SET_NULL,
        related_name="ticket_messages",
        null=True,
        blank=True,
    )
    subject = models.CharField(max_length=500, blank=True)
    body_html = models.TextField(blank=True)
    body_text = models.TextField(blank=True)
    body_text_normalised = models.TextField(blank=True)
    provider = models.CharField(max_length=40, blank=True)
    provider_message_id = models.CharField(max_length=512, blank=True, null=True, unique=True)
    provider_reply_to_message_id = models.CharField(max_length=512, blank=True, db_index=True)
    internet_message_id = models.CharField(max_length=512, blank=True, db_index=True)
    in_reply_to = models.CharField(max_length=512, blank=True, db_index=True)
    references = models.JSONField(default=list, blank=True)
    sent_or_received_at = models.DateTimeField(db_index=True)
    delivery_status = models.CharField(max_length=40, blank=True)
    delivery_error = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="ticket_messages",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sent_or_received_at", "created_at"]

    def __str__(self) -> str:
        return f"{self.ticket.reference} message from {self.sender_address}"


class TicketNote(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="ticket_notes",
        null=True,
        blank=True,
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Note on {self.ticket.reference}"


class TicketAttachment(models.Model):
    class ScanStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SCANNING = "scanning", "Scanning"
        SAFE = "safe", "Safe"
        INFECTED = "infected", "Infected"
        FAILED = "scan_failed", "Scan failed"
        BLOCKED = "blocked", "Blocked by policy"

    message = models.ForeignKey(TicketMessage, on_delete=models.CASCADE, related_name="attachments")
    provider_attachment_id = models.CharField(max_length=512, blank=True, db_index=True)
    original_filename = models.CharField(max_length=255)
    content_id = models.CharField(max_length=512, blank=True)
    is_inline = models.BooleanField(default=False)
    storage_key = models.CharField(max_length=500, blank=True)
    declared_content_type = models.CharField(max_length=255, blank=True)
    detected_content_type = models.CharField(max_length=255, blank=True)
    size = models.PositiveBigIntegerField(default=0)
    sha256 = models.CharField(max_length=64, blank=True, db_index=True)
    scan_status = models.CharField(
        max_length=24,
        choices=ScanStatus.choices,
        default=ScanStatus.PENDING,
        db_index=True,
    )
    scan_engine = models.CharField(max_length=80, blank=True)
    scan_result = models.TextField(blank=True)
    quarantined_at = models.DateTimeField(null=True, blank=True)
    scanned_at = models.DateTimeField(null=True, blank=True)
    safe_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["message", "provider_attachment_id"],
                condition=~models.Q(provider_attachment_id=""),
                name="uniq_msg_provider_attachment",
            )
        ]

    def __str__(self) -> str:
        return self.original_filename

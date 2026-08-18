from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.ticketing.models import Ticket, TicketAttachment, TicketMessage, TicketNote, TicketQueue


@admin.register(TicketQueue)
class TicketQueueAdmin(ModelAdmin):
    list_display = ("name", "key", "brand", "purpose", "enabled", "ordering")
    list_filter = ("enabled", "brand")
    search_fields = ("name", "key", "purpose")


@admin.register(Ticket)
class TicketAdmin(ModelAdmin):
    list_display = (
        "reference",
        "subject",
        "queue",
        "client",
        "status",
        "priority",
        "assigned_to",
        "last_message_at",
    )
    list_filter = ("brand", "queue", "status", "priority", "classification", "source")
    search_fields = ("reference", "subject", "client__name", "client__company")
    readonly_fields = ("reference", "created_at", "updated_at")


@admin.register(TicketMessage)
class TicketMessageAdmin(ModelAdmin):
    list_display = ("ticket", "direction", "sender_address", "provider", "sent_or_received_at")
    list_filter = ("direction", "provider")
    search_fields = ("ticket__reference", "sender_address", "subject", "internet_message_id")


@admin.register(TicketNote)
class TicketNoteAdmin(ModelAdmin):
    list_display = ("ticket", "author", "created_at")
    search_fields = ("ticket__reference", "body")


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(ModelAdmin):
    list_display = ("original_filename", "message", "size", "scan_status", "scan_engine")
    list_filter = ("scan_status", "scan_engine")
    search_fields = ("original_filename", "sha256", "message__ticket__reference")

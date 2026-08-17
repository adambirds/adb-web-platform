from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile


@admin.register(StaffAccessProfile)
class StaffAccessProfileAdmin(ModelAdmin):
    list_display = ("user", "all_clients", "all_ticket_queues", "updated_at")
    list_filter = ("all_clients", "all_ticket_queues")
    search_fields = ("user__email", "user__first_name", "user__last_name")


@admin.register(ClientAccessGrant)
class ClientAccessGrantAdmin(ModelAdmin):
    list_display = ("profile", "client", "granted_by", "created_at")
    list_filter = ("created_at",)
    search_fields = ("profile__user__email", "client__name", "client__company")

from django.contrib import admin
from django.http import HttpRequest
from unfold.admin import ModelAdmin

from apps.core.models import AuditEvent, Brand


@admin.register(Brand)
class BrandAdmin(ModelAdmin):
    list_display = ("name", "domain", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "domain")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(AuditEvent)
class AuditEventAdmin(ModelAdmin):
    list_display = ("created_at", "actor", "action", "target_type", "target_label")
    list_filter = ("action", "target_type")
    search_fields = ("actor__email", "action", "target_type", "target_id", "target_label")
    readonly_fields = (
        "actor",
        "action",
        "target_type",
        "target_id",
        "target_label",
        "metadata",
        "ip_address",
        "user_agent",
        "created_at",
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: AuditEvent | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: AuditEvent | None = None) -> bool:
        return False

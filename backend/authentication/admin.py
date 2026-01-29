from typing import Any

from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group
from django.http import HttpRequest
from unfold.admin import ModelAdmin

from authentication.models import CustomGroup, User
from authentication.passkeys.models import Passkey, PasskeyAuthenticationLog, PasskeyChallenge
from authentication.twofactor.models import RecoveryCode, TwoFactorChallenge, TwoFactorMethod


class GroupAdmin(BaseGroupAdmin, ModelAdmin[CustomGroup]):
    pass


class UserAdmin(ModelAdmin[User]):
    list_display = (
        "email",
        "first_name",
        "last_name",
        "email_verified",
        "is_superuser",
        "is_staff",
        "is_active",
        "date_joined",
        "ebay_account_not_yet_linked_email_sent",
    )
    list_filter = (
        "email_verified",
        "is_superuser",
        "is_staff",
        "is_active",
        "date_joined",
        "ebay_account_not_yet_linked_email_sent",
    )
    list_editable = (
        "is_active",
        "is_staff",
        "email_verified",
        "ebay_account_not_yet_linked_email_sent",
    )
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined", "email")


class PasskeyAdmin(ModelAdmin[Passkey]):
    """Admin interface for Passkey model."""

    list_display = (
        "id",
        "user",
        "name",
        "device_type",
        "backed_up",
        "created_at",
        "last_used_at",
    )
    list_filter = ("device_type", "backed_up", "created_at", "last_used_at")
    search_fields = ("user__email", "name", "credential_id")
    readonly_fields = (
        "id",
        "credential_id",
        "public_key",
        "sign_count",
        "transports",
        "created_at",
        "last_used_at",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


class PasskeyChallengeAdmin(ModelAdmin[PasskeyChallenge]):
    """Admin interface for PasskeyChallenge model."""

    list_display = (
        "id",
        "user",
        "email",
        "challenge_type",
        "created_at",
    )
    list_filter = ("challenge_type", "created_at")
    search_fields = ("user__email", "email")
    readonly_fields = ("id", "challenge", "created_at")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


class PasskeyAuthenticationLogAdmin(ModelAdmin[PasskeyAuthenticationLog]):
    """Admin interface for PasskeyAuthenticationLog model."""

    list_display = (
        "id",
        "user",
        "email",
        "event_type",
        "passkey",
        "ip_address",
        "created_at",
    )
    list_filter = ("event_type", "created_at")
    search_fields = ("user__email", "email", "ip_address", "error_message")
    readonly_fields = (
        "id",
        "user",
        "email",
        "event_type",
        "passkey",
        "ip_address",
        "user_agent",
        "error_message",
        "metadata",
        "created_at",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Prevent manual creation of log entries."""
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Prevent editing of log entries."""
        return False


class TwoFactorMethodAdmin(ModelAdmin[TwoFactorMethod]):
    list_display = (
        "id",
        "user",
        "method_type",
        "name",
        "is_primary",
        "is_verified",
        "created_at",
        "last_used_at",
    )
    list_filter = ("method_type", "is_primary", "is_verified", "created_at")
    search_fields = ("user__email", "name")
    ordering = ("-created_at",)
    readonly_fields = ("secret", "created_at", "last_used_at")


class RecoveryCodeAdmin(ModelAdmin[RecoveryCode]):
    list_display = ("id", "user", "is_used", "created_at", "used_at")
    list_filter = ("is_used", "created_at", "used_at")
    search_fields = ("user__email",)
    ordering = ("-created_at",)
    readonly_fields = ("code_hash", "created_at", "used_at")


class TwoFactorChallengeAdmin(ModelAdmin[TwoFactorChallenge]):
    list_display = ("id", "user", "password_verified", "created_at", "ip_address")
    list_filter = ("password_verified", "created_at")
    search_fields = ("user__email", "ip_address")
    ordering = ("-created_at",)
    readonly_fields = ("challenge_token", "created_at", "ip_address", "user_agent")


admin.site.unregister(Group)
admin.site.register(User, UserAdmin)
admin.site.register(CustomGroup, GroupAdmin)
admin.site.register(Passkey, PasskeyAdmin)
admin.site.register(PasskeyChallenge, PasskeyChallengeAdmin)
admin.site.register(PasskeyAuthenticationLog, PasskeyAuthenticationLogAdmin)
admin.site.register(TwoFactorMethod, TwoFactorMethodAdmin)
admin.site.register(RecoveryCode, RecoveryCodeAdmin)
admin.site.register(TwoFactorChallenge, TwoFactorChallengeAdmin)

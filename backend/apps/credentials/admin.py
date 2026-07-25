from django.contrib import admin

from .models import CredentialType, StoredCredential

# Register your models here.


@admin.register(CredentialType)
class CredentialTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "icon")


@admin.register(StoredCredential)
class StoredCredentialAdmin(admin.ModelAdmin):
    list_display = ("name", "credential_type", "username", "created_at")
    list_filter = ("credential_type", "created_at")
    search_fields = ("name", "username")

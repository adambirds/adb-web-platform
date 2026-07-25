from django.contrib import admin

from .models import (
    API,
    Application,
    Bot,
    Database,
    Domain,
    EmailSystem,
    Licence,
    MobileApp,
    Server,
    SSLCertificate,
    Website,
    WebsiteTechStack,
)

# Register your models here.


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ("hostname", "provider", "os", "created_at")
    list_filter = ("provider", "os", "created_at")
    search_fields = ("hostname", "public_ip", "private_ip")


@admin.register(Database)
class DatabaseAdmin(admin.ModelAdmin):
    list_display = ("name", "db_type", "provider", "created_at")
    list_filter = ("db_type", "provider", "created_at")
    search_fields = ("name",)


@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    list_display = ("name", "primary_url", "environment_type", "created_at")
    list_filter = ("environment_type", "created_at")
    search_fields = ("name", "primary_url")


@admin.register(WebsiteTechStack)
class WebsiteTechStackAdmin(admin.ModelAdmin):
    list_display = ("website", "technology", "category")
    list_filter = ("website", "category")


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("domain_name", "registrar", "expiry_date", "auto_renew")
    list_filter = ("registrar", "auto_renew", "expiry_date")
    search_fields = ("domain_name",)


@admin.register(SSLCertificate)
class SSLCertificateAdmin(admin.ModelAdmin):
    list_display = ("domain", "provider", "expiry_date", "created_at")
    list_filter = ("provider", "expiry_date", "created_at")


@admin.register(Licence)
class LicenceAdmin(admin.ModelAdmin):
    list_display = ("name", "vendor", "licence_type", "renewal_date", "auto_renew")
    list_filter = ("licence_type", "auto_renew", "renewal_date")
    search_fields = ("name", "vendor")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("name", "app_type", "status", "created_at")
    list_filter = ("app_type", "status", "created_at")
    search_fields = ("name", "description")


@admin.register(MobileApp)
class MobileAppAdmin(admin.ModelAdmin):
    list_display = ("name", "platform", "framework", "release_status")
    list_filter = ("platform", "framework", "release_status")


@admin.register(API)
class APIAdmin(admin.ModelAdmin):
    list_display = ("name", "api_type", "visibility", "created_at")
    list_filter = ("api_type", "visibility", "created_at")


@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = ("name", "platform", "bot_type", "created_at")
    list_filter = ("platform", "bot_type", "created_at")


@admin.register(EmailSystem)
class EmailSystemAdmin(admin.ModelAdmin):
    list_display = ("provider", "created_at")
    list_filter = ("provider", "created_at")

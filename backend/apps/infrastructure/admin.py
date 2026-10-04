from django.contrib import admin

from .models import (
    API,
    Application,
    ApplicationEnvironment,
    ApplicationProfile,
    ApplicationRepositoryLink,
    Bot,
    Database,
    DatabaseInstance,
    DNSRecord,
    DNSZone,
    Domain,
    DomainProfile,
    EmailSystem,
    IPAddress,
    Licence,
    LogicalDatabase,
    MobileApp,
    Network,
    NetworkInterface,
    Server,
    ServerProfile,
    SourceRepository,
    SSLCertificate,
    Subnet,
    TLSCertificate,
    TLSCertificateDomain,
    Website,
    WebsiteEndpoint,
    WebsiteProfile,
    WebsiteTechStack,
)


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ("hostname", "provider", "os", "created_at")
    list_filter = ("provider", "os", "created_at")
    search_fields = ("hostname", "public_ip", "private_ip")


@admin.register(ServerProfile)
class ServerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "hostname",
        "resource",
        "compute_type",
        "os_family",
        "provider_account",
        "region",
    )
    list_filter = ("compute_type", "os_family", "region")
    search_fields = (
        "hostname",
        "fqdn",
        "resource__name",
        "provider_resource_id",
    )
    raw_id_fields = ("resource", "provider_account")


@admin.register(Network)
class NetworkAdmin(admin.ModelAdmin):
    list_display = (
        "resource",
        "network_type",
        "cidr",
        "provider_account",
        "region",
    )
    list_filter = ("network_type", "region")
    search_fields = ("resource__name", "cidr", "provider_network_id")
    raw_id_fields = ("resource", "provider_account")


@admin.register(Subnet)
class SubnetAdmin(admin.ModelAdmin):
    list_display = ("resource", "network", "cidr", "availability_zone", "vlan_id")
    search_fields = ("resource__name", "network__resource__name", "cidr")
    raw_id_fields = ("resource", "network")


@admin.register(NetworkInterface)
class NetworkInterfaceAdmin(admin.ModelAdmin):
    list_display = ("server", "name", "network", "subnet", "mac_address")
    search_fields = ("server__hostname", "name", "mac_address")
    raw_id_fields = ("server", "network", "subnet")


@admin.register(IPAddress)
class IPAddressAdmin(admin.ModelAdmin):
    list_display = ("address", "resource", "scope", "is_primary", "interface")
    list_filter = ("scope", "is_primary")
    search_fields = ("address", "resource__name", "ptr_record")
    raw_id_fields = ("resource", "interface")


@admin.register(DatabaseInstance)
class DatabaseInstanceAdmin(admin.ModelAdmin):
    list_display = (
        "resource",
        "engine",
        "engine_version",
        "hosting_type",
        "provider_account",
        "server",
        "region",
    )
    list_filter = ("engine", "hosting_type", "tls_mode", "region")
    search_fields = (
        "resource__name",
        "endpoint",
        "provider_resource_id",
        "engine_version",
    )
    raw_id_fields = ("resource", "provider_account", "server")


@admin.register(LogicalDatabase)
class LogicalDatabaseAdmin(admin.ModelAdmin):
    list_display = ("resource", "database_name", "instance", "default_schema")
    search_fields = ("resource__name", "database_name", "instance__resource__name")
    raw_id_fields = ("resource", "instance")


@admin.register(ApplicationProfile)
class ApplicationProfileAdmin(admin.ModelAdmin):
    list_display = ("resource", "application_type", "owner_team", "primary_language", "framework")
    list_filter = ("application_type",)
    search_fields = ("resource__name", "owner_team", "primary_language", "framework")
    raw_id_fields = ("resource",)


@admin.register(ApplicationEnvironment)
class ApplicationEnvironmentAdmin(admin.ModelAdmin):
    list_display = (
        "resource",
        "application",
        "deployment_type",
        "server",
        "provider_account",
        "region",
    )
    list_filter = ("deployment_type", "region", "automatic_deployments")
    search_fields = (
        "resource__name",
        "application__resource__name",
        "provider_resource_id",
        "runtime",
        "release_version",
    )
    raw_id_fields = ("resource", "application", "server", "provider_account")


@admin.register(SourceRepository)
class SourceRepositoryAdmin(admin.ModelAdmin):
    list_display = (
        "resource",
        "owner_name",
        "repository_name",
        "visibility",
        "provider_account",
        "default_branch",
    )
    list_filter = ("visibility", "is_fork")
    search_fields = (
        "resource__name",
        "owner_name",
        "repository_name",
        "provider_repository_id",
        "web_url",
    )
    raw_id_fields = ("resource", "provider_account")


@admin.register(ApplicationRepositoryLink)
class ApplicationRepositoryLinkAdmin(admin.ModelAdmin):
    list_display = ("application", "repository", "role", "path")
    list_filter = ("role",)
    search_fields = (
        "application__resource__name",
        "repository__resource__name",
        "repository__repository_name",
        "path",
    )
    raw_id_fields = ("application", "repository")


@admin.register(WebsiteProfile)
class WebsiteProfileAdmin(admin.ModelAdmin):
    list_display = (
        "resource",
        "website_type",
        "hosting_provider_account",
        "cdn_provider_account",
        "waf_provider_account",
    )
    list_filter = ("website_type",)
    search_fields = ("resource__name", "admin_url", "cms", "cms_version")
    raw_id_fields = (
        "resource",
        "hosting_provider_account",
        "cdn_provider_account",
        "waf_provider_account",
    )


@admin.register(WebsiteEndpoint)
class WebsiteEndpointAdmin(admin.ModelAdmin):
    list_display = ("url", "website", "role", "is_primary", "domain", "tls_certificate")
    list_filter = ("role", "is_primary")
    search_fields = ("url", "website__resource__name", "domain__domain_name")
    raw_id_fields = (
        "resource",
        "website",
        "application_environment",
        "domain",
        "tls_certificate",
    )


@admin.register(DomainProfile)
class DomainProfileAdmin(admin.ModelAdmin):
    readonly_fields = ("last_metadata_checked_at", "metadata_refresh_error")
    list_display = (
        "domain_name",
        "resource",
        "registrar_account",
        "status",
        "expires_on",
        "auto_renew",
    )
    list_filter = ("status", "auto_renew", "expires_on")
    search_fields = ("domain_name", "resource__name", "provider_domain_id")
    raw_id_fields = ("resource", "registrar_account")


@admin.register(DNSZone)
class DNSZoneAdmin(admin.ModelAdmin):
    list_display = (
        "zone_name",
        "resource",
        "domain",
        "provider_account",
        "dnssec_enabled",
        "is_primary",
    )
    list_filter = ("dnssec_enabled", "is_primary")
    search_fields = ("zone_name", "resource__name", "domain__domain_name", "provider_zone_id")
    raw_id_fields = ("resource", "domain", "provider_account")


@admin.register(DNSRecord)
class DNSRecordAdmin(admin.ModelAdmin):
    list_display = ("name", "record_type", "zone", "ttl", "proxied")
    list_filter = ("record_type", "proxied")
    search_fields = ("name", "value", "zone__zone_name", "provider_record_id")
    raw_id_fields = ("zone",)


@admin.register(TLSCertificate)
class TLSCertificateAdmin(admin.ModelAdmin):
    readonly_fields = ("metadata_source", "last_metadata_checked_at", "metadata_refresh_error")
    list_display = (
        "resource",
        "certificate_type",
        "subject_common_name",
        "issuer",
        "expires_at",
        "auto_renew",
    )
    list_filter = ("certificate_type", "auto_renew", "expires_at")
    search_fields = (
        "resource__name",
        "subject_common_name",
        "issuer",
        "serial_number",
        "fingerprint_sha256",
    )
    raw_id_fields = ("resource", "provider_account")


@admin.register(TLSCertificateDomain)
class TLSCertificateDomainAdmin(admin.ModelAdmin):
    list_display = ("certificate", "domain", "is_primary")
    list_filter = ("is_primary",)
    search_fields = ("certificate__resource__name", "domain__domain_name")
    raw_id_fields = ("certificate", "domain")


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

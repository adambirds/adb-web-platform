from ninja import Schema


class InfrastructureSummaryOut(Schema):
    server_count: int
    database_count: int
    website_count: int
    domain_count: int
    expiring_domain_count: int
    ssl_certificate_count: int
    expiring_certificate_count: int
    licence_count: int
    renewing_licence_count: int
    application_count: int
    mobile_app_count: int
    api_count: int
    bot_count: int
    email_system_count: int

from datetime import date
from decimal import Decimal

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


class ServerSummaryOut(Schema):
    id: int
    hostname: str
    role: str
    provider: str
    region: str
    os: str
    public_ip: str | None
    ram_gb: int | None


class DatabaseSummaryOut(Schema):
    id: int
    name: str
    db_type: str
    provider: str
    version: str
    server_hostname: str | None


class WebsiteSummaryOut(Schema):
    id: int
    name: str
    primary_url: str
    environment_type: str
    database_name: str | None
    server_count: int
    domain_count: int


class DomainSummaryOut(Schema):
    id: int
    domain_name: str
    registrar: str
    expiry_date: date
    auto_renew: bool
    website_count: int


class LicenceSummaryOut(Schema):
    id: int
    name: str
    licence_type: str
    vendor: str
    renewal_date: date
    renewal_cost: Decimal | None
    auto_renew: bool
    website_count: int

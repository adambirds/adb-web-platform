from typing import Literal

from ninja import Schema

from .specialist_schemas import ClientOptionOut, StructuredResourceIn, StructuredResourceUpdateIn

BasicResourceType = Literal[
    "api", "bot", "mobile_app", "licence", "email_system", "network_device", "other"
]
ProviderCategory = Literal[
    "cloud",
    "hosting",
    "registrar",
    "dns",
    "cdn",
    "saas",
    "source_control",
    "monitoring",
    "hardware",
    "other",
]


class ServiceProviderIn(Schema):
    name: str
    slug: str
    category: ProviderCategory
    website_url: str = ""
    support_url: str = ""
    status_page_url: str = ""
    documentation_url: str = ""
    notes: str = ""
    is_active: bool = True


class ServiceProviderUpdateIn(ServiceProviderIn):
    is_active: bool


class ServiceProviderOut(ServiceProviderIn):
    id: int
    is_active: bool


class ServiceProviderPageOut(Schema):
    items: list[ServiceProviderOut]
    page: int
    page_size: int
    total: int
    total_pages: int


class CatalogueOptionsOut(Schema):
    clients: list[ClientOptionOut]
    providers: list[ServiceProviderOut]


class BasicResourceIn(StructuredResourceIn):
    resource_type: BasicResourceType


class BasicResourceUpdateIn(StructuredResourceUpdateIn):
    pass


class ProviderAccountFields(Schema):
    provider_id: int
    account_identifier: str = ""
    tenant_id: str = ""
    project_id: str = ""
    portal_url: str = ""
    default_region: str = ""
    support_plan: str = ""
    billing_reference: str = ""


class ProviderAccountIn(StructuredResourceIn, ProviderAccountFields):
    pass


class ProviderAccountUpdateIn(StructuredResourceUpdateIn, ProviderAccountFields):
    pass


class ProviderAccountOut(ProviderAccountIn):
    resource_id: int
    provider_name: str


class ResourceMutationOut(Schema):
    resource_id: int

from datetime import date, datetime
from typing import Literal

from ninja import Schema

ResourceOwnershipFilter = Literal["all", "internal", "client"]
ResourceLifecycleFilter = Literal[
    "current",
    "all",
    "planned",
    "active",
    "maintenance",
    "deprecated",
    "retired",
    "archived",
]
ResourceTypeFilter = Literal[
    "server",
    "network",
    "subnet",
    "database_instance",
    "logical_database",
    "application",
    "application_environment",
    "source_repository",
    "website",
    "website_endpoint",
    "domain",
    "dns_zone",
    "tls_certificate",
    "provider_account",
    "storage",
    "backup_plan",
    "container_stack",
    "kubernetes_cluster",
    "kubernetes_namespace",
    "kubernetes_workload",
    "system_service",
    "scheduled_job",
    "api",
    "bot",
    "mobile_app",
    "licence",
    "email_system",
    "network_device",
    "other",
]
ResourceEnvironmentFilter = Literal[
    "production",
    "staging",
    "development",
    "testing",
    "shared",
    "not_applicable",
]


class InfrastructureTagOut(Schema):
    id: int
    name: str
    slug: str
    colour: str


class InfrastructureResourceSummaryOut(Schema):
    id: int
    name: str
    resource_type: str
    lifecycle_status: str
    environment: str
    criticality: str
    ownership_type: str
    client_id: int | None
    client_name: str | None
    tags: list[InfrastructureTagOut]
    updated_at: datetime
    expires_on: date | None = None
    expires_at: datetime | None = None
    auto_renew: bool | None = None


class InfrastructureResourcePageOut(Schema):
    items: list[InfrastructureResourceSummaryOut]
    page: int
    page_size: int
    total: int
    total_pages: int


class InfrastructureRelationshipOut(Schema):
    id: int
    direction: Literal["outgoing", "incoming"]
    relationship_type: str
    label: str
    notes: str = ""
    related_resource_id: int
    related_resource_name: str
    related_resource_type: str


class InfrastructureRelationshipCreateIn(Schema):
    target_resource_id: int
    relationship_type: str
    label: str = ""
    notes: str = ""


class InfrastructureRelationshipTypeOut(Schema):
    value: str
    label: str


class InfrastructureRelationshipTargetOut(Schema):
    id: int
    name: str
    resource_type: str
    ownership_type: str
    client_name: str | None


class InfrastructureRelationshipOptionsOut(Schema):
    relationship_types: list[InfrastructureRelationshipTypeOut]
    targets: list[InfrastructureRelationshipTargetOut]


class SpecialistFieldOut(Schema):
    key: str
    label: str
    value: str
    kind: Literal["text", "code", "url", "multiline"]


class InfrastructureResourceDetailOut(InfrastructureResourceSummaryOut):
    description: str
    is_portal_visible: bool
    relationships: list[InfrastructureRelationshipOut]
    specialist_fields: list[SpecialistFieldOut]
    created_at: datetime

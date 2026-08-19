from datetime import datetime
from uuid import UUID

from ninja import Schema


class LeadLookupOut(Schema):
    id: int
    name: str


class LeadAgentOut(Schema):
    id: UUID
    name: str
    email: str


class LeadSummaryOut(Schema):
    id: int
    name: str
    company: str
    email: str
    status: str
    source: str
    brand: str
    assigned_to_name: str | None
    converted_at: datetime | None
    created_at: datetime


class LeadTicketOut(Schema):
    id: int
    reference: str
    subject: str
    status: str
    priority: str
    queue_name: str
    last_message_at: datetime | None


class LeadDetailOut(Schema):
    id: int
    name: str
    email: str
    phone: str
    company: str
    brand_id: int | None
    brand_name: str | None
    status_id: int | None
    status_name: str | None
    source_id: int | None
    source_name: str | None
    assigned_to_id: UUID | None
    assigned_to_name: str | None
    converted_client_id: int | None
    converted_contact_id: int | None
    converted_by_name: str | None
    converted_at: datetime | None
    can_assign: bool
    can_convert: bool
    message: str
    notes: str
    created_at: datetime
    updated_at: datetime
    related_tickets: list[LeadTicketOut]


class LeadIn(Schema):
    name: str
    email: str
    phone: str = ""
    company: str = ""
    brand_id: int | None = None
    status_id: int | None = None
    source_id: int | None = None
    message: str = ""
    notes: str = ""


class LeadAssignmentIn(Schema):
    assigned_to_id: UUID | None = None


class LeadConversionOut(Schema):
    lead: LeadDetailOut
    client_id: int
    contact_id: int
    linked_ticket_count: int


class LeadOptionsOut(Schema):
    statuses: list[LeadLookupOut]
    sources: list[LeadLookupOut]
    assignees: list[LeadAgentOut]

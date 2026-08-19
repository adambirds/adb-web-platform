from datetime import datetime

from ninja import Schema


class LeadLookupOut(Schema):
    id: int
    name: str


class LeadSummaryOut(Schema):
    id: int
    name: str
    company: str
    email: str
    status: str
    source: str
    brand: str
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


class LeadOptionsOut(Schema):
    statuses: list[LeadLookupOut]
    sources: list[LeadLookupOut]

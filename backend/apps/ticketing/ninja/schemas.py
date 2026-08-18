from datetime import datetime
from uuid import UUID

from ninja import Schema


class TicketQueueOut(Schema):
    id: int
    name: str
    key: str
    brand_id: int | None
    brand_name: str | None
    purpose: str
    default_priority: str
    enabled: bool


class GraphConnectionOut(Schema):
    id: int
    name: str
    tenant_id: str
    client_id: str
    authentication_method: str
    credential_id: int | None
    credential_name: str | None
    enabled: bool
    last_verified_at: datetime | None
    last_error: str


class MailboxOut(Schema):
    id: int
    email_address: str
    display_name: str
    graph_connection_id: int
    graph_connection_name: str
    brand_id: int
    brand_name: str
    purpose: str
    default_queue_id: int
    default_queue_name: str
    enabled: bool
    last_synced_at: datetime | None
    last_successful_sync_at: datetime | None
    last_error: str


class TicketListItemOut(Schema):
    id: int
    reference: str
    subject: str
    brand_id: int
    brand_name: str
    queue_id: int
    queue_name: str
    client_id: int | None
    client_name: str | None
    primary_contact_id: int | None
    primary_contact_name: str | None
    status: str
    priority: str
    classification: str
    source: str
    assigned_to_id: UUID | None
    assigned_to_name: str | None
    message_count: int
    last_message_at: datetime | None
    created_at: datetime


class PaginatedTicketsOut(Schema):
    items: list[TicketListItemOut]
    page: int
    page_size: int
    total: int
    total_pages: int


class TicketMessageOut(Schema):
    id: int
    direction: str
    sender_name: str
    sender_address: str
    to_recipients: list[str]
    cc_recipients: list[str]
    bcc_recipients: list[str]
    matched_contact_id: int | None
    matched_contact_name: str | None
    subject: str
    body_html: str
    body_text: str
    body_text_normalised: str
    provider: str
    internet_message_id: str
    sent_or_received_at: datetime
    delivery_status: str
    delivery_error: str
    created_by_name: str | None


class TicketNoteOut(Schema):
    id: int
    author_name: str | None
    body: str
    created_at: datetime
    updated_at: datetime


class TicketAttachmentOut(Schema):
    id: int
    original_filename: str
    declared_content_type: str
    detected_content_type: str
    size: int
    sha256: str
    scan_status: str
    scan_engine: str
    scanned_at: datetime | None
    safe_at: datetime | None


class TicketDetailOut(Schema):
    id: int
    reference: str
    subject: str
    brand_id: int
    brand_name: str
    queue_id: int
    queue_name: str
    client_id: int | None
    client_name: str | None
    primary_contact_id: int | None
    primary_contact_name: str | None
    status: str
    priority: str
    classification: str
    source: str
    assigned_to_id: UUID | None
    assigned_to_name: str | None
    first_response_at: datetime | None
    last_message_at: datetime | None
    resolved_at: datetime | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    can_reply: bool
    can_add_note: bool
    messages: list[TicketMessageOut]
    notes: list[TicketNoteOut]
    attachments: list[TicketAttachmentOut]

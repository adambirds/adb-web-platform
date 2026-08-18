import math
from typing import Any, cast
from uuid import UUID

from django.db.models import Count, Q, QuerySet
from django.http import HttpRequest
from ninja import Query, Router, Schema
from pydantic import Field

from apps.access_control.policies import scope_clients_for_user, scope_ticket_queues_for_user
from apps.ticketing.models import Ticket, TicketAttachment, TicketMessage, TicketQueue
from apps.ticketing.services.replies import TicketReplyError, prepare_ticket_reply
from apps.ticketing.tasks import deliver_ticket_reply_task
from authentication.models import User
from authentication.ninja.schemas import ProblemDetail

from .schemas import (
    PaginatedTicketsOut,
    TicketAttachmentOut,
    TicketDetailOut,
    TicketListItemOut,
    TicketMessageOut,
    TicketNoteOut,
    TicketQueueOut,
)

ticketing_admin_router = Router(tags=["admin-ticketing"])

StaffProblem = tuple[int, dict[str, Any]]


class TicketFilters(Schema):
    page: int = 1
    page_size: int = 25
    queue_id: int | None = None
    brand_id: int | None = None
    status: str | None = None
    priority: str | None = None
    classification: str | None = None
    client_id: int | None = None
    primary_contact_id: int | None = None
    assigned_to_id: UUID | None = None
    source: str | None = None
    search: str | None = None


class TicketReplyIn(Schema):
    body_text: str
    cc_recipients: list[str] = Field(default_factory=list)
    bcc_recipients: list[str] = Field(default_factory=list)


def _staff_problem(request: HttpRequest) -> StaffProblem | None:
    if not request.user.is_authenticated:
        return 401, {
            "message": "User not authenticated",
            "success": False,
            "code": "unauthenticated",
        }
    if not (request.user.is_staff or request.user.is_superuser):
        return 403, {
            "message": "You do not have permission to access this resource.",
            "success": False,
            "code": "forbidden",
        }
    return None


def _visible_tickets(request: HttpRequest) -> QuerySet[Ticket]:
    tickets = Ticket.objects.select_related(
        "brand",
        "queue",
        "client",
        "primary_contact",
        "assigned_to",
    )
    if request.user.is_superuser:
        return tickets

    clients = scope_clients_for_user(request.user)
    queues = scope_ticket_queues_for_user(request.user)
    return tickets.filter(
        Q(queue__in=queues) & (Q(client__isnull=True) | Q(client__in=clients))
    ).distinct()


def _user_label(user: Any | None) -> str | None:
    if user is None:
        return None
    full_name = user.get_full_name().strip()
    return full_name or user.email


def _message_out(message: TicketMessage) -> TicketMessageOut:
    return TicketMessageOut(
        id=message.id,
        direction=message.direction,
        sender_name=message.sender_name,
        sender_address=message.sender_address,
        to_recipients=message.to_recipients,
        cc_recipients=message.cc_recipients,
        bcc_recipients=message.bcc_recipients,
        matched_contact_id=message.matched_contact_id,
        matched_contact_name=message.matched_contact.name if message.matched_contact else None,
        subject=message.subject,
        body_html=message.body_html,
        body_text=message.body_text,
        body_text_normalised=message.body_text_normalised,
        provider=message.provider,
        internet_message_id=message.internet_message_id,
        sent_or_received_at=message.sent_or_received_at,
        delivery_status=message.delivery_status,
        delivery_error=message.delivery_error,
        created_by_name=_user_label(message.created_by),
    )


@ticketing_admin_router.get(
    "/ticket-queues",
    response={200: list[TicketQueueOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_ticket_queues(request: HttpRequest) -> list[TicketQueueOut] | StaffProblem:
    staff_problem = _staff_problem(request)
    if staff_problem:
        return staff_problem
    if not request.user.has_perm("ticketing.view_ticketqueue"):
        return 403, {
            "message": "You do not have permission to view ticket queues.",
            "success": False,
            "code": "forbidden",
        }

    queues = scope_ticket_queues_for_user(
        request.user,
        TicketQueue.objects.select_related("brand"),
    )
    return [
        TicketQueueOut(
            id=queue.id,
            name=queue.name,
            key=queue.key,
            brand_id=queue.brand_id,
            brand_name=queue.brand.name if queue.brand else None,
            purpose=queue.purpose,
            default_priority=queue.default_priority,
            enabled=queue.enabled,
        )
        for queue in queues.order_by("ordering", "name")
    ]


@ticketing_admin_router.get(
    "/tickets",
    response={200: PaginatedTicketsOut, 401: ProblemDetail, 403: ProblemDetail},
)
def list_tickets(
    request: HttpRequest,
    filters: Query[TicketFilters],
) -> PaginatedTicketsOut | StaffProblem:
    staff_problem = _staff_problem(request)
    if staff_problem:
        return staff_problem
    if not request.user.has_perm("ticketing.view_ticket"):
        return 403, {
            "message": "You do not have permission to view tickets.",
            "success": False,
            "code": "forbidden",
        }

    page = max(filters.page, 1)
    page_size = min(max(filters.page_size, 1), 100)
    tickets = _visible_tickets(request).annotate(message_count=Count("messages"))

    if filters.queue_id:
        tickets = tickets.filter(queue_id=filters.queue_id)
    if filters.brand_id:
        tickets = tickets.filter(brand_id=filters.brand_id)
    if filters.status:
        tickets = tickets.filter(status=filters.status)
    if filters.priority:
        tickets = tickets.filter(priority=filters.priority)
    if filters.classification:
        tickets = tickets.filter(classification=filters.classification)
    if filters.client_id:
        tickets = tickets.filter(client_id=filters.client_id)
    if filters.primary_contact_id:
        tickets = tickets.filter(primary_contact_id=filters.primary_contact_id)
    if filters.assigned_to_id:
        tickets = tickets.filter(assigned_to_id=filters.assigned_to_id)
    if filters.source:
        tickets = tickets.filter(source=filters.source)
    if filters.search:
        search = filters.search.strip()
        if search:
            tickets = tickets.filter(
                Q(reference__icontains=search)
                | Q(subject__icontains=search)
                | Q(client__name__icontains=search)
                | Q(client__company__icontains=search)
                | Q(primary_contact__name__icontains=search)
                | Q(primary_contact__email__icontains=search)
            )

    total = tickets.count()
    total_pages = math.ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    page_items = tickets.order_by("-last_message_at", "-created_at")[start : start + page_size]

    return PaginatedTicketsOut(
        items=[
            TicketListItemOut(
                id=ticket.id,
                reference=ticket.reference,
                subject=ticket.subject,
                brand_id=ticket.brand_id,
                brand_name=ticket.brand.name,
                queue_id=ticket.queue_id,
                queue_name=ticket.queue.name,
                client_id=ticket.client_id,
                client_name=str(ticket.client) if ticket.client else None,
                primary_contact_id=ticket.primary_contact_id,
                primary_contact_name=(
                    ticket.primary_contact.name if ticket.primary_contact else None
                ),
                status=ticket.status,
                priority=ticket.priority,
                classification=ticket.classification,
                source=ticket.source,
                assigned_to_id=ticket.assigned_to_id,
                assigned_to_name=_user_label(ticket.assigned_to),
                message_count=ticket.message_count,
                last_message_at=ticket.last_message_at,
                created_at=ticket.created_at,
            )
            for ticket in page_items
        ],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@ticketing_admin_router.get(
    "/tickets/{ticket_id}",
    response={200: TicketDetailOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def get_ticket(request: HttpRequest, ticket_id: int) -> TicketDetailOut | StaffProblem:
    staff_problem = _staff_problem(request)
    if staff_problem:
        return staff_problem
    if not request.user.has_perm("ticketing.view_ticket"):
        return 403, {
            "message": "You do not have permission to view tickets.",
            "success": False,
            "code": "forbidden",
        }

    ticket = (
        _visible_tickets(request)
        .prefetch_related("messages__matched_contact", "messages__created_by", "notes__author")
        .filter(id=ticket_id)
        .first()
    )
    if ticket is None:
        return 404, {
            "message": "Ticket not found.",
            "success": False,
            "code": "not_found",
        }

    attachments = TicketAttachment.objects.filter(message__ticket=ticket).order_by("created_at")
    attachment_rows: list[TicketAttachmentOut] = []
    if request.user.has_perm("ticketing.view_ticket_attachment"):
        attachment_rows = [
            TicketAttachmentOut(
                id=attachment.id,
                original_filename=attachment.original_filename,
                declared_content_type=attachment.declared_content_type,
                detected_content_type=attachment.detected_content_type,
                size=attachment.size,
                sha256=attachment.sha256,
                scan_status=attachment.scan_status,
                scan_engine=attachment.scan_engine,
                scanned_at=attachment.scanned_at,
                safe_at=attachment.safe_at,
            )
            for attachment in attachments
        ]

    return TicketDetailOut(
        id=ticket.id,
        reference=ticket.reference,
        subject=ticket.subject,
        brand_id=ticket.brand_id,
        brand_name=ticket.brand.name,
        queue_id=ticket.queue_id,
        queue_name=ticket.queue.name,
        client_id=ticket.client_id,
        client_name=str(ticket.client) if ticket.client else None,
        primary_contact_id=ticket.primary_contact_id,
        primary_contact_name=ticket.primary_contact.name if ticket.primary_contact else None,
        status=ticket.status,
        priority=ticket.priority,
        classification=ticket.classification,
        source=ticket.source,
        assigned_to_id=ticket.assigned_to_id,
        assigned_to_name=_user_label(ticket.assigned_to),
        first_response_at=ticket.first_response_at,
        last_message_at=ticket.last_message_at,
        resolved_at=ticket.resolved_at,
        closed_at=ticket.closed_at,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        messages=[_message_out(message) for message in ticket.messages.all()],
        notes=[
            TicketNoteOut(
                id=note.id,
                author_name=_user_label(note.author),
                body=note.body,
                created_at=note.created_at,
                updated_at=note.updated_at,
            )
            for note in ticket.notes.all()
        ],
        attachments=attachment_rows,
    )


@ticketing_admin_router.post(
    "/tickets/{ticket_id}/reply",
    response={
        202: TicketMessageOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def reply_to_ticket(
    request: HttpRequest,
    ticket_id: int,
    data: TicketReplyIn,
) -> tuple[int, TicketMessageOut] | StaffProblem:
    staff_problem = _staff_problem(request)
    if staff_problem:
        return staff_problem
    if not request.user.has_perm("ticketing.view_ticket") or not request.user.has_perm(
        "ticketing.reply_ticket"
    ):
        return 403, {
            "message": "You do not have permission to reply to tickets.",
            "success": False,
            "code": "forbidden",
        }

    ticket = (
        _visible_tickets(request)
        .select_related("mailbox__graph_connection")
        .filter(id=ticket_id)
        .first()
    )
    if ticket is None:
        return 404, {
            "message": "Ticket not found.",
            "success": False,
            "code": "not_found",
        }

    author = cast(User, request.user)
    try:
        message = prepare_ticket_reply(
            ticket,
            author,
            data.body_text,
            cc_recipients=data.cc_recipients,
            bcc_recipients=data.bcc_recipients,
        )
    except TicketReplyError as exc:
        return 400, {
            "message": str(exc),
            "success": False,
            "code": "reply_unavailable",
        }

    deliver_ticket_reply_task.delay(message.id)
    return 202, _message_out(message)

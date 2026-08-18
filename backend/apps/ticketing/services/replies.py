from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from apps.ticketing.models import Ticket, TicketMessage
from authentication.models import User

GRAPH_PROVIDER = "microsoft_graph"
DELIVERY_STATUS_QUEUED = "queued"
DELIVERY_STATUS_SENDING = "sending"
DELIVERY_STATUS_SENT = "sent"
DELIVERY_STATUS_FAILED = "failed"


class TicketReplyError(RuntimeError):
    """A ticket reply cannot be prepared safely."""


def prepare_ticket_reply(
    ticket: Ticket,
    author: User,
    body_text: str,
    *,
    cc_recipients: Sequence[str] = (),
    bcc_recipients: Sequence[str] = (),
) -> TicketMessage:
    """Persist a queued outbound reply without coupling business logic to Celery."""
    body = body_text.strip()
    if not body:
        raise TicketReplyError("A reply body is required.")

    mailbox = ticket.mailbox
    if mailbox is None:
        raise TicketReplyError("This ticket is not linked to a Microsoft 365 mailbox.")
    if not mailbox.enabled or not mailbox.graph_connection.enabled:
        raise TicketReplyError("The ticket mailbox is not enabled for Microsoft Graph delivery.")

    source_message = (
        ticket.messages.filter(
            direction=TicketMessage.Direction.INBOUND,
            provider=GRAPH_PROVIDER,
            provider_message_id__isnull=False,
        )
        .exclude(provider_message_id="")
        .order_by("-sent_or_received_at", "-created_at")
        .first()
    )
    if source_message is None or not source_message.provider_message_id:
        raise TicketReplyError("This ticket has no Microsoft Graph message that can be replied to.")

    recipient = source_message.sender_address.strip().lower()
    if not recipient:
        raise TicketReplyError("The source message has no sender address.")

    mailbox_address = mailbox.email_address.strip().lower()
    cc = _normalise_recipients(
        cc_recipients,
        excluded={recipient, mailbox_address},
    )
    bcc = _normalise_recipients(
        bcc_recipients,
        excluded={recipient, mailbox_address, *cc},
    )
    references = tuple(
        dict.fromkeys(
            [
                *(str(value).strip() for value in source_message.references if str(value).strip()),
                *(
                    [source_message.internet_message_id]
                    if source_message.internet_message_id
                    else []
                ),
            ]
        )
    )

    with transaction.atomic():
        message = TicketMessage.objects.create(
            ticket=ticket,
            direction=TicketMessage.Direction.OUTBOUND,
            sender_name=mailbox.display_name.strip(),
            sender_address=mailbox_address,
            to_recipients=[recipient],
            cc_recipients=list(cc),
            bcc_recipients=list(bcc),
            subject=_reply_subject(ticket),
            body_text=body,
            body_text_normalised=body,
            provider=GRAPH_PROVIDER,
            provider_message_id=None,
            provider_reply_to_message_id=source_message.provider_message_id,
            internet_message_id="",
            in_reply_to=source_message.internet_message_id,
            references=list(references),
            sent_or_received_at=timezone.now(),
            delivery_status=DELIVERY_STATUS_QUEUED,
            created_by=author,
        )
    return message


def mark_ticket_reply_sending(message: TicketMessage) -> None:
    """Mark an outbound reply as actively being delivered."""
    message.delivery_status = DELIVERY_STATUS_SENDING
    message.delivery_error = ""
    message.save(update_fields=["delivery_status", "delivery_error"])


def fail_ticket_reply(message: TicketMessage, error: str) -> None:
    """Persist a delivery failure without changing the surrounding ticket state."""
    message.delivery_status = DELIVERY_STATUS_FAILED
    message.delivery_error = error.strip()[:2000]
    message.save(update_fields=["delivery_status", "delivery_error"])


def complete_ticket_reply(
    message: TicketMessage,
    *,
    provider_message_id: str,
    internet_message_id: str = "",
    sent_at: datetime | None = None,
) -> TicketMessage:
    """Persist successful delivery and advance the ticket workflow atomically."""
    provider_id = provider_message_id.strip()
    if not provider_id:
        raise TicketReplyError("A provider message ID is required to complete ticket delivery.")

    delivered_at = sent_at or timezone.now()
    with transaction.atomic():
        delivered_message = (
            TicketMessage.objects.select_for_update().select_related("ticket").get(pk=message.pk)
        )
        delivered_message.provider_message_id = provider_id
        delivered_message.internet_message_id = internet_message_id.strip()
        delivered_message.delivery_status = DELIVERY_STATUS_SENT
        delivered_message.delivery_error = ""
        delivered_message.sent_or_received_at = delivered_at
        delivered_message.save(
            update_fields=[
                "provider_message_id",
                "internet_message_id",
                "delivery_status",
                "delivery_error",
                "sent_or_received_at",
            ]
        )

        ticket = delivered_message.ticket
        if ticket.first_response_at is None:
            ticket.first_response_at = delivered_at
        ticket.last_message_at = delivered_at
        ticket.status = Ticket.Status.WAITING_CUSTOMER
        ticket.resolved_at = None
        ticket.closed_at = None
        ticket.save(
            update_fields=[
                "first_response_at",
                "last_message_at",
                "status",
                "resolved_at",
                "closed_at",
                "updated_at",
            ]
        )

    return delivered_message


def _reply_subject(ticket: Ticket) -> str:
    subject = ticket.subject.strip()
    lowered = subject.lower()
    while lowered.startswith("re:"):
        subject = subject[3:].strip()
        lowered = subject.lower()
    return f"Re: [{ticket.reference}] {subject}"


def _normalise_recipients(
    recipients: Sequence[str],
    *,
    excluded: set[str],
) -> tuple[str, ...]:
    normalised: list[str] = []
    seen = set(excluded)
    for value in recipients:
        address = value.strip().lower()
        if not address or address in seen:
            continue
        seen.add(address)
        normalised.append(address)
    return tuple(normalised)

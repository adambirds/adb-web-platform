from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager, suppress

from celery import shared_task
from django_redis import get_redis_connection
from redis.exceptions import LockError

from apps.ticketing.models import TicketMessage
from apps.ticketing.services.graph import MicrosoftGraphError
from apps.ticketing.services.graph_auth import (
    MicrosoftGraphAuthenticationError,
    MicrosoftGraphTokenProvider,
)
from apps.ticketing.services.graph_outbound import MicrosoftGraphOutboundAdapter
from apps.ticketing.services.outbound import mailbox_supports_background_delivery
from apps.ticketing.services.replies import (
    DELIVERY_STATUS_SENT,
    complete_new_ticket_message,
    fail_ticket_reply,
    mark_ticket_reply_sending,
)

LEAD_EMAIL_LOCK_PREFIX = "crm:lead-email-delivery"
LEAD_EMAIL_LOCK_SECONDS = 300
RETRYABLE_GRAPH_ERRORS = (MicrosoftGraphError, MicrosoftGraphAuthenticationError)


@shared_task(
    name="crm.deliver_lead_email",
    autoretry_for=RETRYABLE_GRAPH_ERRORS,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=5,
)
def deliver_lead_email_task(message_id: int) -> int:
    """Deliver one queued outbound-first lead conversation through Microsoft 365."""
    message = (
        TicketMessage.objects.select_related(
            "ticket__mailbox__graph_connection__credential",
            "ticket__mailbox",
            "ticket",
        )
        .filter(id=message_id)
        .first()
    )
    if message is None or message.delivery_status == DELIVERY_STATUS_SENT:
        return 0
    if message.direction != TicketMessage.Direction.OUTBOUND:
        return 0

    with _lead_email_delivery_lock(message.id) as acquired:
        if not acquired:
            return 0
        message.refresh_from_db()
        if message.delivery_status == DELIVERY_STATUS_SENT:
            return 0
        return _deliver(message)


def _deliver(message: TicketMessage) -> int:
    ticket = message.ticket
    mailbox = ticket.mailbox
    if mailbox is None:
        fail_ticket_reply(message, "Ticket mailbox is no longer configured.")
        return 0
    if not mailbox_supports_background_delivery(mailbox):
        fail_ticket_reply(message, "Ticket mailbox is not eligible for background Graph delivery.")
        return 0

    mark_ticket_reply_sending(message)
    token_provider = MicrosoftGraphTokenProvider(mailbox.graph_connection)
    adapter = MicrosoftGraphOutboundAdapter(token_provider)
    try:
        receipt = adapter.send_message(
            mailbox,
            subject=message.subject,
            to_recipients=message.to_recipients,
            body_html=message.body_html,
            body_text=message.body_text,
            cc_recipients=message.cc_recipients,
            bcc_recipients=message.bcc_recipients,
        )
    except RETRYABLE_GRAPH_ERRORS as exc:
        fail_ticket_reply(message, f"{type(exc).__name__}: {exc}")
        raise

    complete_new_ticket_message(
        message,
        provider_message_id=receipt.provider_message_id,
        internet_message_id=receipt.internet_message_id,
    )
    return 1


@contextmanager
def _lead_email_delivery_lock(message_id: int) -> Iterator[bool]:
    redis = get_redis_connection("default")
    lock = redis.lock(
        f"{LEAD_EMAIL_LOCK_PREFIX}:{message_id}",
        timeout=LEAD_EMAIL_LOCK_SECONDS,
        blocking_timeout=0,
    )
    acquired = bool(lock.acquire(blocking=False))
    try:
        yield acquired
    finally:
        if acquired:
            with suppress(LockError):
                lock.release()


@shared_task(name="crm.refresh_retention_reviews")
def refresh_retention_reviews_task() -> dict[str, int]:
    """Queue expired unsuccessful leads for human review; never auto-delete leads."""
    from apps.crm.retention import refresh_retention_reviews

    return refresh_retention_reviews()

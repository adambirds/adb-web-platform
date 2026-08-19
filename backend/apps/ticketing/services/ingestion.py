from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from django.db import IntegrityError, transaction

from apps.clients.models import Client, ClientContact
from apps.core.models import Brand
from apps.ticketing.models import Mailbox, Ticket, TicketMessage, TicketQueue
from apps.ticketing.services.classification import (
    ClassificationDecision,
    classify_message_for_purpose,
)
from apps.ticketing.services.contracts import CanonicalMessage
from apps.ticketing.services.normalisation import normalize_message_body
from apps.ticketing.services.routing import route_queue_for_classification

logger = logging.getLogger(__name__)

_TICKET_REFERENCE_RE = re.compile(r"\bADB-[A-Z0-9]{10}\b", flags=re.IGNORECASE)


class TicketIngestionError(RuntimeError):
    """A canonical message cannot be safely persisted as a ticket message."""


@dataclass(frozen=True, slots=True)
class TicketIngestionResult:
    ticket: Ticket
    message: TicketMessage
    created: bool


@dataclass(frozen=True, slots=True)
class TicketIngestionSource:
    """Routing context supplied by a provider adapter before ticket persistence."""

    brand: Brand
    queue: TicketQueue
    source: str
    purpose: str
    mailbox: Mailbox | None = None
    allow_thread_matching: bool = False


def ingest_canonical_message(
    mailbox: Mailbox,
    canonical: CanonicalMessage,
) -> TicketIngestionResult:
    """Persist a provider-neutral mailbox message idempotently."""
    source = TicketIngestionSource(
        brand=mailbox.brand,
        queue=mailbox.default_queue,
        source=Ticket.Source.EMAIL,
        purpose=mailbox.purpose,
        mailbox=mailbox,
        allow_thread_matching=True,
    )
    return ingest_source_message(source, canonical)


def ingest_contact_form_message(
    brand: Brand,
    queue: TicketQueue,
    canonical: CanonicalMessage,
    *,
    mailbox: Mailbox | None = None,
) -> TicketIngestionResult:
    """Persist a public website contact submission through the canonical ticket pipeline."""
    source = TicketIngestionSource(
        brand=brand,
        queue=queue,
        source=Ticket.Source.CONTACT_FORM,
        purpose=Mailbox.Purpose.SALES,
        mailbox=mailbox,
    )
    return ingest_source_message(source, canonical)


def ingest_source_message(
    source: TicketIngestionSource,
    canonical: CanonicalMessage,
) -> TicketIngestionResult:
    """Persist a canonical inbound message from any configured ticket source."""
    provider_message_id = canonical.provider_message_id.strip()
    if not provider_message_id:
        raise TicketIngestionError("Canonical messages require a provider message ID.")
    if source.queue.brand_id is not None and source.queue.brand_id != source.brand.id:
        raise TicketIngestionError("Ticket source queue does not belong to the selected Brand.")
    if source.mailbox is not None and source.mailbox.brand_id != source.brand.id:
        raise TicketIngestionError("Ticket source mailbox does not belong to the selected Brand.")

    existing = _existing_provider_message(provider_message_id)
    if existing is not None:
        return TicketIngestionResult(ticket=existing.ticket, message=existing, created=False)

    try:
        with transaction.atomic():
            return _persist_source_message(source, canonical, provider_message_id)
    except IntegrityError:
        existing = _existing_provider_message(provider_message_id)
        if existing is not None:
            return TicketIngestionResult(ticket=existing.ticket, message=existing, created=False)
        raise


def _persist_source_message(
    source: TicketIngestionSource,
    canonical: CanonicalMessage,
    provider_message_id: str,
) -> TicketIngestionResult:
    client, contact = _resolve_sender(canonical.sender_address)
    decision = classify_message_for_purpose(source.purpose, canonical, client)
    _log_classification(provider_message_id, decision)
    routed_queue = route_queue_for_classification(
        source.brand,
        source.queue,
        decision.classification,
    )

    ticket = None
    if source.allow_thread_matching and source.mailbox is not None:
        ticket = _find_thread(source.mailbox, canonical)

    if ticket is None:
        ticket = Ticket.objects.create(
            brand=source.brand,
            queue=routed_queue,
            mailbox=source.mailbox,
            client=client,
            primary_contact=contact,
            subject=canonical.subject.strip() or "(No subject)",
            status=Ticket.Status.NEW,
            priority=decision.suggested_priority or routed_queue.default_priority,
            classification=decision.classification,
            source=source.source,
            last_message_at=canonical.sent_or_received_at,
        )
    else:
        client, contact = _compatible_sender_context(ticket, client, contact)
        _update_existing_ticket(
            ticket,
            canonical=canonical,
            client=client,
            contact=contact,
            classification=decision.classification,
        )

    ticket_message = TicketMessage.objects.create(
        ticket=ticket,
        direction=TicketMessage.Direction.INBOUND,
        sender_name=canonical.sender_name,
        sender_address=canonical.sender_address,
        to_recipients=list(canonical.to_recipients),
        cc_recipients=list(canonical.cc_recipients),
        bcc_recipients=list(canonical.bcc_recipients),
        matched_contact=contact,
        subject=canonical.subject,
        body_html=canonical.body_html,
        body_text=canonical.body_text,
        body_text_normalised=normalize_message_body(
            body_text=canonical.body_text,
            body_html=canonical.body_html,
        ),
        provider=canonical.provider,
        provider_message_id=provider_message_id,
        internet_message_id=canonical.internet_message_id,
        in_reply_to=canonical.in_reply_to,
        references=list(canonical.references),
        sent_or_received_at=canonical.sent_or_received_at,
        delivery_status="received",
    )
    return TicketIngestionResult(ticket=ticket, message=ticket_message, created=True)


def _log_classification(
    provider_message_id: str,
    decision: ClassificationDecision,
) -> None:
    logger.info(
        "Classified ticket message %s as %s with score %d using %s",
        provider_message_id,
        decision.classification,
        decision.score,
        ",".join(decision.reasons),
    )


def _existing_provider_message(provider_message_id: str) -> TicketMessage | None:
    return (
        TicketMessage.objects.select_related("ticket")
        .filter(provider_message_id=provider_message_id)
        .first()
    )


def _resolve_sender(sender_address: str) -> tuple[Client | None, ClientContact | None]:
    email = sender_address.strip()
    if not email:
        return None, None

    contacts = list(
        ClientContact.objects.select_related("client")
        .filter(email__iexact=email, is_active=True, client__status="active")
        .order_by("id")[:2]
    )
    if len(contacts) == 1:
        contact = contacts[0]
        return contact.client, contact
    if len(contacts) > 1:
        return None, None

    clients = list(Client.objects.filter(email__iexact=email, status="active").order_by("id")[:2])
    if len(clients) == 1:
        return clients[0], None
    return None, None


def _find_thread(mailbox: Mailbox, canonical: CanonicalMessage) -> Ticket | None:
    message_ids = tuple(
        message_id
        for message_id in (canonical.in_reply_to, *reversed(canonical.references))
        if message_id
    )
    for message_id in dict.fromkeys(message_ids):
        matched_message = (
            TicketMessage.objects.select_related("ticket")
            .filter(
                ticket__mailbox=mailbox,
                internet_message_id=message_id,
            )
            .order_by("-sent_or_received_at", "-id")
            .first()
        )
        if matched_message is not None:
            return matched_message.ticket

    references = [
        reference.upper() for reference in _TICKET_REFERENCE_RE.findall(canonical.subject)
    ]
    if references:
        return (
            Ticket.objects.filter(mailbox=mailbox, reference__in=references)
            .order_by("-last_message_at", "-created_at")
            .first()
        )
    return None


def _compatible_sender_context(
    ticket: Ticket,
    client: Client | None,
    contact: ClientContact | None,
) -> tuple[Client | None, ClientContact | None]:
    if ticket.client_id is not None and client is not None and ticket.client_id != client.id:
        return None, None
    return client, contact


def _update_existing_ticket(
    ticket: Ticket,
    *,
    canonical: CanonicalMessage,
    client: Client | None,
    contact: ClientContact | None,
    classification: str,
) -> None:
    update_fields: set[str] = set()

    if ticket.client_id is None and client is not None:
        ticket.client = client
        update_fields.add("client")
    if ticket.primary_contact_id is None and contact is not None:
        ticket.primary_contact = contact
        update_fields.add("primary_contact")
    if (
        ticket.classification == Ticket.Classification.UNKNOWN
        and classification != Ticket.Classification.UNKNOWN
    ):
        ticket.classification = classification
        update_fields.add("classification")

    if ticket.last_message_at is None or canonical.sent_or_received_at > ticket.last_message_at:
        ticket.last_message_at = canonical.sent_or_received_at
        update_fields.add("last_message_at")

    if ticket.status in {
        Ticket.Status.WAITING_CUSTOMER,
        Ticket.Status.RESOLVED,
        Ticket.Status.CLOSED,
    }:
        ticket.status = Ticket.Status.OPEN
        ticket.resolved_at = None
        ticket.closed_at = None
        update_fields.update({"status", "resolved_at", "closed_at"})

    if update_fields:
        update_fields.add("updated_at")
        ticket.save(update_fields=sorted(update_fields))

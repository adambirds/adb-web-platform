from __future__ import annotations

import logging
from dataclasses import dataclass

from django.db.models import Q

from apps.core.models import Brand
from apps.crm.models import Lead
from apps.ticketing.models import Mailbox, TicketQueue
from apps.ticketing.services.contracts import CanonicalMessage
from apps.ticketing.services.ingestion import TicketIngestionResult, ingest_contact_form_message

logger = logging.getLogger(__name__)

CONTACT_FORM_PROVIDER = "website_contact_form"


@dataclass(frozen=True, slots=True)
class ContactFormRoute:
    queue: TicketQueue
    mailbox: Mailbox | None = None


def ingest_website_contact_lead(lead: Lead) -> TicketIngestionResult | None:
    """Turn one persisted website Lead into an operational ticket without duplicating CRM data."""
    brand = lead.brand
    if brand is None:
        logger.warning("Cannot ingest website contact Lead %s without a Brand.", lead.pk)
        return None

    route = contact_form_route_for_brand(brand)
    if route is None:
        logger.warning(
            "Cannot ingest website contact Lead %s because Brand %s has no enabled ticket queue.",
            lead.pk,
            brand.slug,
        )
        return None

    canonical = CanonicalMessage(
        provider=CONTACT_FORM_PROVIDER,
        provider_message_id=f"website-contact-form:{lead.pk}",
        provider_conversation_id="",
        internet_message_id="",
        in_reply_to="",
        references=(),
        sender_name=lead.name.strip(),
        sender_address=lead.email.strip().lower(),
        to_recipients=(),
        cc_recipients=(),
        bcc_recipients=(),
        subject=f"Website enquiry - {lead.name.strip() or lead.email}",
        body_html="",
        body_text=_contact_form_body(lead),
        sent_or_received_at=lead.created_at,
        has_attachments=False,
    )
    return ingest_contact_form_message(
        brand,
        route.queue,
        canonical,
        mailbox=route.mailbox,
    )


def contact_form_route_for_brand(brand: Brand) -> ContactFormRoute | None:
    """Prefer the Brand's sales mailbox/queue, then a matching enabled queue."""
    sales_mailbox = (
        Mailbox.objects.select_related("default_queue")
        .filter(
            brand=brand,
            purpose=Mailbox.Purpose.SALES,
            enabled=True,
            default_queue__enabled=True,
        )
        .order_by("id")
        .first()
    )
    if sales_mailbox is not None:
        return ContactFormRoute(
            queue=sales_mailbox.default_queue,
            mailbox=sales_mailbox,
        )

    queues = TicketQueue.objects.filter(brand=brand, enabled=True)
    for term in ("sales", "support"):
        queue = (
            queues.filter(Q(purpose__icontains=term) | Q(key__icontains=term))
            .order_by("ordering", "name")
            .first()
        )
        if queue is not None:
            return ContactFormRoute(queue=queue)

    queue = queues.order_by("ordering", "name").first()
    return ContactFormRoute(queue=queue) if queue is not None else None


def contact_form_queue_for_brand(brand: Brand) -> TicketQueue | None:
    route = contact_form_route_for_brand(brand)
    return route.queue if route is not None else None


def _contact_form_body(lead: Lead) -> str:
    metadata: list[str] = []
    if lead.company.strip():
        metadata.append(f"Company: {lead.company.strip()}")
    if lead.phone.strip():
        metadata.append(f"Phone: {lead.phone.strip()}")

    metadata_text = "\n".join(metadata)
    message = lead.message.strip()
    if metadata_text and message:
        return f"{metadata_text}\n\n{message}"
    return metadata_text or message

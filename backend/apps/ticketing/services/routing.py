from __future__ import annotations

from django.db.models import Q

from apps.core.models import Brand
from apps.ticketing.models import Ticket, TicketQueue


def route_queue_for_classification(
    brand: Brand,
    default_queue: TicketQueue,
    classification: str,
) -> TicketQueue:
    """Apply conservative Brand-local routing overrides for high-signal classifications."""
    if classification == Ticket.Classification.PROBABLE_SPAM:
        matched = _find_brand_queue(brand, terms=("quarantine", "spam"))
        return matched or default_queue

    if classification in {
        Ticket.Classification.MONITORING,
        Ticket.Classification.AUTOMATED_SYSTEM,
    }:
        matched = _find_brand_queue(brand, terms=("operations", "operational"))
        return matched or default_queue

    return default_queue


def _find_brand_queue(brand: Brand, *, terms: tuple[str, ...]) -> TicketQueue | None:
    query = Q()
    for term in terms:
        query |= Q(key__icontains=term) | Q(purpose__icontains=term)

    return (
        TicketQueue.objects.filter(brand=brand, enabled=True)
        .filter(query)
        .order_by("ordering", "name")
        .first()
    )

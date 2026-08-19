from __future__ import annotations

from django.db.models import Q

from apps.core.models import Brand
from apps.ticketing.models import Ticket, TicketQueue


def route_queue_for_classification(
    brand: Brand,
    default_queue: TicketQueue,
    classification: str,
    *,
    preferred_queue: TicketQueue | None = None,
) -> TicketQueue:
    """Apply conservative routing overrides for high-signal classifications."""
    if preferred_queue is not None and _queue_is_usable_for_brand(preferred_queue, brand):
        return preferred_queue

    if classification == Ticket.Classification.PROBABLE_SPAM:
        matched = _find_brand_queue(brand, terms=("quarantine", "spam"))
        return matched or default_queue

    if classification in {
        Ticket.Classification.MONITORING,
        Ticket.Classification.AUTOMATED_SYSTEM,
    }:
        matched = _find_brand_queue(brand, terms=("operations", "operational"))
        return matched or default_queue

    if classification == Ticket.Classification.VENDOR:
        matched = _find_brand_queue(brand, terms=("vendor", "vendors", "supplier"))
        if matched is not None:
            return matched
        global_queue = _find_global_queue(terms=("vendor", "vendors", "supplier"))
        return global_queue or default_queue

    return default_queue


def _queue_is_usable_for_brand(queue: TicketQueue, brand: Brand) -> bool:
    return queue.enabled and (queue.brand_id is None or queue.brand_id == brand.id)


def _find_brand_queue(brand: Brand, *, terms: tuple[str, ...]) -> TicketQueue | None:
    query = _queue_search_query(terms)
    return (
        TicketQueue.objects.filter(brand=brand, enabled=True)
        .filter(query)
        .order_by("ordering", "name")
        .first()
    )


def _find_global_queue(*, terms: tuple[str, ...]) -> TicketQueue | None:
    query = _queue_search_query(terms)
    return (
        TicketQueue.objects.filter(brand__isnull=True, enabled=True)
        .filter(query)
        .order_by("ordering", "name")
        .first()
    )


def _queue_search_query(terms: tuple[str, ...]) -> Q:
    query = Q()
    for term in terms:
        query |= Q(key__icontains=term) | Q(purpose__icontains=term)
    return query

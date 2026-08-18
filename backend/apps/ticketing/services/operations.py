from __future__ import annotations

from datetime import datetime

from django.utils import timezone

from apps.ticketing.models import Ticket, TicketQueue
from authentication.models import User


class TicketOperationError(ValueError):
    """A requested ticket operation is not valid for the current ticket."""


def assign_ticket(ticket: Ticket, assignee: User | None) -> Ticket:
    """Assign or unassign a ticket after endpoint-level scope checks."""
    if assignee is not None and (not assignee.is_active or not assignee.is_staff):
        raise TicketOperationError("Tickets can only be assigned to active staff users.")

    ticket.assigned_to = assignee
    ticket.save(update_fields=["assigned_to", "updated_at"])
    return ticket


def set_ticket_priority(ticket: Ticket, priority: str) -> Ticket:
    """Set a validated ticket priority."""
    try:
        validated_priority = Ticket.Priority(priority)
    except ValueError as exc:
        raise TicketOperationError("Unknown ticket priority.") from exc

    if ticket.priority == validated_priority:
        return ticket

    ticket.priority = validated_priority
    ticket.save(update_fields=["priority", "updated_at"])
    return ticket


def move_ticket_queue(ticket: Ticket, queue: TicketQueue) -> Ticket:
    """Move a ticket to an enabled queue belonging to its Brand or a global queue."""
    if queue.pk == ticket.queue_id:
        return ticket
    if not queue.enabled:
        raise TicketOperationError("Tickets cannot be moved to a disabled queue.")
    if queue.brand_id is not None and queue.brand_id != ticket.brand_id:
        raise TicketOperationError("The selected queue does not belong to this ticket Brand.")

    ticket.queue = queue
    ticket.save(update_fields=["queue", "updated_at"])
    return ticket


def set_ticket_status(
    ticket: Ticket,
    status: str,
    *,
    changed_at: datetime | None = None,
) -> Ticket:
    """Change workflow status while keeping resolved/closed timestamps consistent."""
    try:
        validated_status = Ticket.Status(status)
    except ValueError as exc:
        raise TicketOperationError("Unknown ticket status.") from exc

    if ticket.status == validated_status:
        return ticket

    timestamp = changed_at or timezone.now()
    ticket.status = validated_status

    if validated_status == Ticket.Status.RESOLVED:
        ticket.resolved_at = timestamp
        ticket.closed_at = None
    elif validated_status == Ticket.Status.CLOSED:
        ticket.resolved_at = ticket.resolved_at or timestamp
        ticket.closed_at = timestamp
    else:
        ticket.resolved_at = None
        ticket.closed_at = None

    ticket.save(
        update_fields=[
            "status",
            "resolved_at",
            "closed_at",
            "updated_at",
        ]
    )
    return ticket

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db.models import QuerySet

from apps.access_control.models import StaffAccessProfile
from apps.clients.models import Client

if TYPE_CHECKING:
    from apps.ticketing.models import TicketQueue


def get_access_profile(user: Any) -> StaffAccessProfile | None:
    """Return a staff access profile when one exists."""
    if not getattr(user, "is_authenticated", False):
        return None
    try:
        return user.access_profile
    except StaffAccessProfile.DoesNotExist:
        return None


def can_access_client(user: Any, client: Client) -> bool:
    """Check object-scope access to a client, independent of capability permission."""
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True

    profile = get_access_profile(user)
    if profile is None:
        return False
    if profile.all_clients:
        return True

    return profile.client_grants.filter(client=client).exists()


def scope_clients_for_user(
    user: Any,
    queryset: QuerySet[Client] | None = None,
) -> QuerySet[Client]:
    """Restrict a Client queryset to the object scope available to a user."""
    queryset = queryset if queryset is not None else Client.objects.all()

    if not getattr(user, "is_authenticated", False):
        return queryset.none()
    if getattr(user, "is_superuser", False):
        return queryset

    profile = get_access_profile(user)
    if profile is None:
        return queryset.none()
    if profile.all_clients:
        return queryset

    return queryset.filter(access_grants__profile=profile).distinct()


def can_access_ticket_queue(user: Any, queue: TicketQueue) -> bool:
    """Check object-scope access to a ticket queue, independent of capability permission."""
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True

    profile = get_access_profile(user)
    if profile is None:
        return False
    if profile.all_ticket_queues:
        return True

    return profile.ticket_queue_grants.filter(queue=queue).exists()


def scope_ticket_queues_for_user(user: Any, queryset: Any = None) -> Any:
    """Restrict a TicketQueue queryset to the queues available to a user."""
    from apps.ticketing.models import TicketQueue

    queryset = queryset if queryset is not None else TicketQueue.objects.all()

    if not getattr(user, "is_authenticated", False):
        return queryset.none()
    if getattr(user, "is_superuser", False):
        return queryset

    profile = get_access_profile(user)
    if profile is None:
        return queryset.none()
    if profile.all_ticket_queues:
        return queryset

    return queryset.filter(access_grants__profile=profile).distinct()

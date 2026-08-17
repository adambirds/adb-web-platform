from __future__ import annotations

from django.db.models import QuerySet

from apps.clients.models import Client


def get_access_profile(user):
    """Return a staff access profile when one exists."""
    if not getattr(user, "is_authenticated", False):
        return None
    try:
        return user.access_profile
    except Exception:
        return None


def can_access_client(user, client: Client) -> bool:
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


def scope_clients_for_user(user, queryset: QuerySet[Client] | None = None) -> QuerySet[Client]:
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

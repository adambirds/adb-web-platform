from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile, TicketQueueAccessGrant
from apps.clients.models import Client
from apps.core.models import AuditEvent
from apps.ticketing.models import TicketQueue
from authentication.models import User

if TYPE_CHECKING:
    from django.db.models import QuerySet


EXCLUDED_PERMISSION_APP_LABELS = {
    "admin",
    "auth",
    "authentication",
    "contenttypes",
    "sessions",
}
SENSITIVE_PERMISSION_CODES = {
    "access_control.manage_staff_access",
    "core.view_sensitive_audit_metadata",
    "credentials.reveal_storedcredential",
    "credentials.copy_storedcredential_secret",
    "credentials.download_storedcredential_secret",
    "credentials.reconcile_legacy_credentials",
    "ticketing.configure_graph_connections",
    "ticketing.configure_mailboxes",
}


@dataclass(frozen=True)
class StaffAccessWrite:
    group_ids: list[int]
    direct_permission_ids: list[int]
    all_clients: bool
    client_ids: list[int]
    all_ticket_queues: bool
    ticket_queue_ids: list[int]
    default_ticket_queue_ids: list[int]


def permission_code(permission: Permission) -> str:
    return f"{permission.content_type.app_label}.{permission.codename}"


def is_sensitive_permission(code: str) -> bool:
    return code in SENSITIVE_PERMISSION_CODES


def assignable_permissions_queryset() -> QuerySet[Permission]:
    return (
        Permission.objects.select_related("content_type")
        .filter(
            ~Q(content_type__app_label__in=EXCLUDED_PERMISSION_APP_LABELS),
            ~Q(content_type__app_label="access_control") | Q(codename="manage_staff_access"),
        )
        .order_by("content_type__app_label", "content_type__model", "codename")
    )


def assignable_groups_queryset() -> QuerySet[Group]:
    excluded_permissions = Permission.objects.exclude(
        id__in=assignable_permissions_queryset().values_list("id", flat=True)
    )
    return Group.objects.exclude(permissions__in=excluded_permissions).distinct().order_by("name")


def _validate_target(actor: User, target: User) -> None:
    if not target.is_staff and not target.is_superuser:
        raise ValidationError("Only staff identities can be managed here.")
    if target.is_superuser and not actor.is_superuser:
        raise ValidationError("Only a superuser can change a superuser account.")
    if actor.pk == target.pk and not actor.is_superuser:
        raise ValidationError("Non-superusers cannot change their own access.")


def _objects_for_ids(queryset: QuerySet, ids: list[int], label: str) -> list:
    unique_ids = sorted(set(ids))
    objects = list(queryset.filter(id__in=unique_ids))
    if len(objects) != len(unique_ids):
        raise ValidationError(f"One or more selected {label} are invalid.")
    return objects


def _snapshot(user: User) -> dict[str, object]:
    try:
        profile = user.access_profile
    except StaffAccessProfile.DoesNotExist:
        profile = None

    direct_permissions = list(
        user.user_permissions.select_related("content_type").order_by(
            "content_type__app_label", "codename"
        )
    )
    return {
        "groups": list(user.groups.order_by("name").values_list("name", flat=True)),
        "direct_permissions": [permission_code(permission) for permission in direct_permissions],
        "all_clients": bool(profile and profile.all_clients),
        "client_ids": []
        if profile is None or profile.all_clients
        else list(profile.client_grants.order_by("client_id").values_list("client_id", flat=True)),
        "all_ticket_queues": bool(profile and profile.all_ticket_queues),
        "ticket_queue_ids": []
        if profile is None or profile.all_ticket_queues
        else list(
            profile.ticket_queue_grants.order_by("queue_id").values_list("queue_id", flat=True)
        ),
        "default_ticket_queue_ids": []
        if profile is None
        else list(profile.default_ticket_queues.order_by("id").values_list("id", flat=True)),
    }


def _apply_staff_access(*, target: User, write: StaffAccessWrite, actor: User) -> None:
    groups = _objects_for_ids(assignable_groups_queryset(), write.group_ids, "groups")
    permissions = _objects_for_ids(
        assignable_permissions_queryset(),
        write.direct_permission_ids,
        "capabilities",
    )
    clients = (
        []
        if write.all_clients
        else _objects_for_ids(Client.objects.all(), write.client_ids, "clients")
    )
    queues = (
        []
        if write.all_ticket_queues
        else _objects_for_ids(TicketQueue.objects.all(), write.ticket_queue_ids, "ticket queues")
    )

    if write.all_ticket_queues:
        enabled_queue_ids = set(
            TicketQueue.objects.filter(enabled=True).values_list("id", flat=True)
        )
    else:
        enabled_queue_ids = {queue.id for queue in queues if queue.enabled}

    default_ids = set(write.default_ticket_queue_ids)
    if not default_ids.issubset(enabled_queue_ids):
        raise ValidationError(
            "Default ticket queues must be enabled queues inside the user's access scope."
        )
    normalised_default_ids = [] if default_ids == enabled_queue_ids else sorted(default_ids)

    target.groups.set(groups)
    target.user_permissions.set(permissions)

    profile, _ = StaffAccessProfile.objects.get_or_create(user=target)
    profile.all_clients = write.all_clients
    profile.all_ticket_queues = write.all_ticket_queues
    profile.save(update_fields=["all_clients", "all_ticket_queues", "updated_at"])

    profile.client_grants.all().delete()
    if not write.all_clients:
        ClientAccessGrant.objects.bulk_create(
            [
                ClientAccessGrant(profile=profile, client=client, granted_by=actor)
                for client in clients
            ]
        )

    profile.ticket_queue_grants.all().delete()
    if not write.all_ticket_queues:
        TicketQueueAccessGrant.objects.bulk_create(
            [
                TicketQueueAccessGrant(profile=profile, queue=queue, granted_by=actor)
                for queue in queues
            ]
        )

    profile.default_ticket_queues.set(normalised_default_ids)


def update_staff_access(
    *,
    actor: User,
    target: User,
    write: StaffAccessWrite,
    ip_address: str | None = None,
    user_agent: str = "",
) -> None:
    _validate_target(actor, target)
    before = _snapshot(target)
    with transaction.atomic():
        locked_target = User.objects.select_for_update().get(pk=target.pk)
        _apply_staff_access(target=locked_target, write=write, actor=actor)
        after = _snapshot(locked_target)
        AuditEvent.record(
            action="staff_access.updated",
            actor=actor,
            target=locked_target,
            metadata={"before": before, "after": after},
            ip_address=ip_address,
            user_agent=user_agent,
        )


def set_staff_active(
    *,
    actor: User,
    target: User,
    is_active: bool,
    ip_address: str | None = None,
    user_agent: str = "",
) -> None:
    _validate_target(actor, target)
    if not is_active and actor.pk == target.pk:
        raise ValidationError("You cannot deactivate your own account.")
    if target.is_active == is_active:
        return

    with transaction.atomic():
        locked_target = User.objects.select_for_update().get(pk=target.pk)
        locked_target.is_active = is_active
        locked_target.save(update_fields=["is_active"])
        AuditEvent.record(
            action="staff_access.activated" if is_active else "staff_access.deactivated",
            actor=actor,
            target=locked_target,
            metadata={"is_active": is_active},
            ip_address=ip_address,
            user_agent=user_agent,
        )


def _send_staff_invitation(user: User) -> bool:
    auth_frontend_url = getattr(settings, "AUTH_FRONTEND_URL", settings.FRONTEND_URL).rstrip("/")
    reset_url = f"{auth_frontend_url}/reset-password/{user.password_reset_token}"
    try:
        send_mail(
            subject="Set up your ADB Business Platform account",
            message=(
                f"Hi {user.first_name},\n\n"
                "An ADB Business Platform staff account has been created for you. "
                "Use the link below within one hour to set your password:\n\n"
                f"{reset_url}\n\n"
                "If you were not expecting this invitation, contact an ADB administrator."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception:
        return False
    return True


def invite_staff_user(
    *,
    actor: User,
    email: str,
    first_name: str,
    last_name: str,
    write: StaffAccessWrite,
    ip_address: str | None = None,
    user_agent: str = "",
) -> tuple[User, bool]:
    normalised_email = User.objects.normalize_email(email)
    if User.objects.filter(email__iexact=normalised_email).exists():
        raise ValidationError("A user with this email already exists.")
    if not first_name.strip() or not last_name.strip():
        raise ValidationError("First name and last name are required.")

    with transaction.atomic():
        user = User(
            email=normalised_email,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            is_staff=True,
            is_active=True,
            email_verified=False,
        )
        user.set_unusable_password()
        user.password_reset_token = uuid.uuid4()
        user.password_reset_token_created = timezone.now()
        user.full_clean()
        user.save()
        _apply_staff_access(target=user, write=write, actor=actor)

    email_sent = _send_staff_invitation(user)
    AuditEvent.record(
        action="staff_access.invited",
        actor=actor,
        target=user,
        metadata={"invitation_email_sent": email_sent, "access": _snapshot(user)},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return user, email_sent


def resend_staff_invitation(
    *,
    actor: User,
    target: User,
    ip_address: str | None = None,
    user_agent: str = "",
) -> bool:
    _validate_target(actor, target)
    with transaction.atomic():
        locked_target = User.objects.select_for_update().get(pk=target.pk)
        if locked_target.has_usable_password():
            raise ValidationError(
                "This account already has a password; use the normal password-reset flow instead."
            )
        locked_target.password_reset_token = uuid.uuid4()
        locked_target.password_reset_token_created = timezone.now()
        locked_target.save(update_fields=["password_reset_token", "password_reset_token_created"])

    email_sent = _send_staff_invitation(locked_target)
    AuditEvent.record(
        action="staff_access.invitation_resent",
        actor=actor,
        target=locked_target,
        metadata={"invitation_email_sent": email_sent},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return email_sent

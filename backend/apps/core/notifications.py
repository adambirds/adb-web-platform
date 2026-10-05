from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.access_control.policies import scope_clients_for_user, scope_ticket_queues_for_user
from apps.core.live.events import LiveChange, publish_change
from apps.core.models import Notification
from apps.core.ownership import OwnershipType
from apps.credentials.health import evaluate_credential_health
from apps.credentials.models import StoredCredential
from apps.credentials.policies import scope_credentials_for_user
from apps.infrastructure.policies import scope_infrastructure_resources_for_user
from apps.monitoring.models import MonitorIncident
from apps.tasks.models import CalendarEvent, Task
from apps.ticketing.models import Ticket
from apps.ticketing.services.sla import evaluate_ticket_sla
from authentication.models import User


@dataclass(frozen=True)
class NotificationSpec:
    source_key: str
    category: str
    severity: str
    title: str
    body: str = ""
    href: str = ""
    client_id: int | None = None
    resource_id: int | None = None


def sync_notification(user: User, spec: NotificationSpec) -> Notification:
    """Upsert one deterministic alert without reopening a dismissed unchanged alert."""
    notification, created = Notification.objects.get_or_create(
        user=user,
        source_key=spec.source_key,
        defaults={
            "category": spec.category,
            "severity": spec.severity,
            "title": spec.title,
            "body": spec.body,
            "href": spec.href,
            "client_id": spec.client_id,
            "resource_id": spec.resource_id,
        },
    )
    if created:
        return notification

    changed = any(
        [
            notification.category != spec.category,
            notification.severity != spec.severity,
            notification.title != spec.title,
            notification.body != spec.body,
            notification.href != spec.href,
            notification.client_id != spec.client_id,
            notification.resource_id != spec.resource_id,
        ]
    )
    update_fields: list[str] = []
    if changed:
        notification.category = spec.category
        notification.severity = spec.severity
        notification.title = spec.title
        notification.body = spec.body
        notification.href = spec.href
        notification.client_id = spec.client_id
        notification.resource_id = spec.resource_id
        notification.resolved_at = None
        notification.dismissed_at = None
        notification.read_at = None
        update_fields.extend(
            [
                "category",
                "severity",
                "title",
                "body",
                "href",
                "client_id",
                "resource_id",
                "resolved_at",
                "dismissed_at",
                "read_at",
            ]
        )
    elif notification.resolved_at is not None:
        notification.resolved_at = None
        notification.dismissed_at = None
        notification.read_at = None
        update_fields.extend(["resolved_at", "dismissed_at", "read_at"])

    if update_fields:
        notification.save(update_fields=[*update_fields, "updated_at"])
    return notification


def resolve_missing_notifications(user: User, prefix: str, active_keys: Iterable[str]) -> None:
    active = set(active_keys)
    unresolved = Notification.objects.filter(
        user=user,
        source_key__startswith=prefix,
        resolved_at__isnull=True,
    )
    if active:
        unresolved = unresolved.exclude(source_key__in=active)
    if unresolved.update(resolved_at=timezone.now()):
        publish_change(LiveChange("notifications", user_id=str(user.pk)))


def _task_notifications(user: User) -> list[NotificationSpec]:
    if not user.has_perm("tasks.view_task"):
        return []
    today = timezone.localdate()
    clients = scope_clients_for_user(user)
    tasks = Task.objects.select_related("client", "project").filter(
        assigned_to=user,
        completed_at__isnull=True,
        due_date__lt=today,
    )
    if not user.is_superuser:
        tasks = tasks.filter(Q(ownership_type=OwnershipType.INTERNAL) | Q(client__in=clients))

    specs: list[NotificationSpec] = []
    for task in tasks.distinct().order_by("due_date", "-priority", "id")[:50]:
        due_date = task.due_date
        if due_date is None:
            continue
        severity = (
            Notification.Severity.CRITICAL if task.priority >= 4 else Notification.Severity.WARNING
        )
        context = (
            task.project.name if task.project else (str(task.client) if task.client else "Internal")
        )
        specs.append(
            NotificationSpec(
                source_key=f"task:overdue:{task.id}",
                category=Notification.Category.TASK,
                severity=severity,
                title=f"Overdue task: {task.title}",
                body=f"Due {due_date.isoformat()} · {context}",
                href=f"/admin/tasks/{task.id}",
                client_id=task.client_id,
            )
        )
    return specs


def _ticket_notifications(user: User) -> list[NotificationSpec]:
    if not user.has_perm("ticketing.view_ticket"):
        return []
    queues = scope_ticket_queues_for_user(user)
    clients = scope_clients_for_user(user)
    tickets = Ticket.objects.select_related("queue", "client").filter(
        queue__in=queues,
        assigned_to=user,
    )
    if not user.is_superuser:
        tickets = tickets.filter(Q(client__isnull=True) | Q(client__in=clients))
    tickets = tickets.exclude(
        status__in=[Ticket.Status.RESOLVED, Ticket.Status.CLOSED, Ticket.Status.SPAM]
    )

    specs: list[NotificationSpec] = []
    for ticket in tickets.distinct().order_by("id")[:200]:
        health = evaluate_ticket_sla(ticket)
        if health.overall_status not in {"warning", "breached"}:
            continue
        severity = (
            Notification.Severity.CRITICAL
            if health.overall_status == "breached"
            else Notification.Severity.WARNING
        )
        title = (
            f"SLA breached: {ticket.reference}"
            if health.overall_status == "breached"
            else f"SLA approaching: {ticket.reference}"
        )
        due_text = health.next_due_at.isoformat() if health.next_due_at else "No pending deadline"
        specs.append(
            NotificationSpec(
                source_key=f"ticket:sla:{ticket.id}",
                category=Notification.Category.TICKET,
                severity=severity,
                title=title,
                body=f"{ticket.subject} · {due_text}",
                href=f"/admin/tickets/{ticket.id}",
                client_id=ticket.client_id,
            )
        )
    return specs


def _credential_notifications(user: User) -> list[NotificationSpec]:
    if not user.has_perm("credentials.view_storedcredential"):
        return []
    credentials = (
        scope_credentials_for_user(user)
        .select_related("client")
        .filter(status=StoredCredential.Status.ACTIVE)
    )
    specs: list[NotificationSpec] = []
    for credential in credentials.order_by("name", "id")[:500]:
        health = evaluate_credential_health(credential)
        if health.severity == "info":
            continue
        if health.status == "expired":
            title = f"Expired credential: {credential.name}"
            body = "The configured credential expiry date has passed."
        elif health.status in {"expiring", "expiring_soon"}:
            title = f"Credential expiring: {credential.name}"
            body = f"Expires in {health.expires_in_days} day(s)."
        elif health.status in {"rotation_due", "rotation_overdue"}:
            title = f"Credential rotation due: {credential.name}"
            body = (
                "Rotation is overdue."
                if health.rotation_due_in_days is not None and health.rotation_due_in_days < 0
                else "The configured rotation interval has been reached."
            )
        else:
            title = f"Credential rotation approaching: {credential.name}"
            body = f"Rotation due in {health.rotation_due_in_days} day(s)."
        specs.append(
            NotificationSpec(
                source_key=f"credential:health:{credential.id}",
                category=Notification.Category.CREDENTIAL,
                severity=health.severity,
                title=title,
                body=body,
                href=f"/admin/credentials/{credential.id}",
                client_id=credential.client_id,
            )
        )
    return specs


def _monitor_notifications(user: User) -> list[NotificationSpec]:
    if not (
        user.has_perm("monitoring.view_monitorincident")
        and user.has_perm("infrastructure.view_infrastructureresource")
    ):
        return []
    resources = scope_infrastructure_resources_for_user(user)
    incidents = MonitorIncident.objects.select_related("monitor_check__resource__client").filter(
        monitor_check__resource__in=resources,
        status__in=[MonitorIncident.Status.OPEN, MonitorIncident.Status.ACKNOWLEDGED],
    )
    specs: list[NotificationSpec] = []
    for incident in incidents.order_by("-opened_at", "-id")[:50]:
        resource = incident.monitor_check.resource
        severity = (
            Notification.Severity.CRITICAL
            if incident.severity == "critical"
            else Notification.Severity.WARNING
        )
        specs.append(
            NotificationSpec(
                source_key=f"monitoring:incident:{incident.id}",
                category=Notification.Category.MONITORING,
                severity=severity,
                title=f"Monitoring incident: {resource.name}",
                body=incident.summary,
                href=f"/admin/monitoring/checks/{incident.monitor_check_id}",
                client_id=resource.client_id,
                resource_id=resource.id,
            )
        )
    return specs


def _calendar_notifications(user: User) -> list[NotificationSpec]:
    if not user.has_perm("tasks.view_calendarevent"):
        return []
    current = timezone.now()
    upcoming_until = current + timedelta(hours=24)
    clients = scope_clients_for_user(user)
    events = CalendarEvent.objects.select_related("client").filter(
        status=CalendarEvent.Status.SCHEDULED,
        starts_at__gte=current,
        starts_at__lte=upcoming_until,
    )
    if not user.is_superuser:
        events = events.filter(Q(ownership_type=OwnershipType.INTERNAL) | Q(client__in=clients))

    user_email = user.email.strip().lower()
    specs: list[NotificationSpec] = []
    for event in events.distinct().order_by("starts_at", "id")[:100]:
        attendees = {str(value).strip().lower() for value in event.attendee_emails}
        if event.created_by_id != user.id and user_email not in attendees:
            continue
        specs.append(
            NotificationSpec(
                source_key=f"calendar:upcoming:{event.id}",
                category=Notification.Category.CALENDAR,
                severity=Notification.Severity.INFO,
                title=f"Upcoming {event.get_event_type_display().lower()}: {event.title}",
                body=f"Starts {event.starts_at.isoformat()}",
                href="/admin/calendar",
                client_id=event.client_id,
            )
        )
    return specs


def refresh_notifications(user: User) -> None:
    """Refresh deterministic operational alerts while preserving user read state."""
    sources = [
        ("task:overdue:", _task_notifications(user)),
        ("ticket:sla:", _ticket_notifications(user)),
        ("credential:health:", _credential_notifications(user)),
        ("monitoring:incident:", _monitor_notifications(user)),
        ("calendar:upcoming:", _calendar_notifications(user)),
    ]
    with transaction.atomic():
        for prefix, specs in sources:
            for spec in specs:
                sync_notification(user, spec)
            resolve_missing_notifications(
                user,
                prefix,
                (spec.source_key for spec in specs),
            )

from __future__ import annotations

from typing import Any, cast

from django.http import HttpRequest
from django.utils import timezone
from ninja import Router

from apps.access_control.policies import scope_clients_for_user
from apps.clients.models import Client
from apps.core.live.events import LiveChange, publish_change
from apps.core.models import AuditEvent, Notification
from apps.core.notifications import refresh_notifications
from apps.core.operational_activity import ActivityContext, activity_page, scoped_audit_events
from apps.infrastructure.models import InfrastructureResource
from apps.infrastructure.policies import scope_infrastructure_resources_for_user
from authentication.models import User
from authentication.ninja.schemas import ProblemDetail

from .operational_schemas import (
    ActivityPageOut,
    NotificationActionOut,
    NotificationCountOut,
    NotificationListOut,
    NotificationOut,
)

operational_polish_router = Router(tags=["admin-operational-polish"])
StaffProblem = tuple[int, dict[str, Any]]


def _problem(status: int, message: str, code: str) -> StaffProblem:
    return status, {"message": message, "success": False, "code": code}


def _staff_user(request: HttpRequest) -> tuple[User | None, StaffProblem | None]:
    if not request.user.is_authenticated:
        return None, _problem(401, "User not authenticated", "unauthenticated")
    if not (request.user.is_staff or request.user.is_superuser):
        return None, _problem(
            403,
            "You do not have permission to access this resource.",
            "forbidden",
        )
    return cast(User, request.user), None


def _resolve_activity_context(
    request: HttpRequest,
    user: User,
    client_id: int | None,
    resource_id: int | None,
) -> tuple[ActivityContext | None, StaffProblem | None]:
    client: Client | None = None
    resource: InfrastructureResource | None = None

    if client_id is not None:
        if not user.has_perm("clients.view_client"):
            return None, _problem(403, "You do not have permission to view clients.", "forbidden")
        client = scope_clients_for_user(user).filter(id=client_id).first()
        if client is None:
            return None, _problem(404, "Client not found.", "not_found")

    if resource_id is not None:
        if not user.has_perm("infrastructure.view_infrastructureresource"):
            return None, _problem(
                403,
                "You do not have permission to view infrastructure resources.",
                "forbidden",
            )
        resource = (
            scope_infrastructure_resources_for_user(user)
            .select_related("client")
            .filter(id=resource_id)
            .first()
        )
        if resource is None:
            return None, _problem(404, "Infrastructure resource not found.", "not_found")
        if client is not None and resource.client_id != client.id:
            return None, _problem(404, "Infrastructure resource not found.", "not_found")

    if client is None and resource is None and not user.has_perm("core.view_auditevent"):
        return None, _problem(
            403,
            "You do not have permission to view the platform audit trail.",
            "forbidden",
        )

    return ActivityContext(client_id=client_id, resource_id=resource_id), None


def _notification_out(notification: Notification) -> NotificationOut:
    return NotificationOut(
        id=notification.id,
        category=cast(Any, notification.category),
        severity=cast(Any, notification.severity),
        title=notification.title,
        body=notification.body,
        href=notification.href,
        client_id=notification.client_id,
        resource_id=notification.resource_id,
        read_at=notification.read_at,
        created_at=notification.created_at,
    )


@operational_polish_router.get(
    "/activity",
    response={
        200: ActivityPageOut,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def operational_activity(
    request: HttpRequest,
    client_id: int | None = None,
    resource_id: int | None = None,
    page: int = 1,
    page_size: int = 50,
) -> ActivityPageOut | StaffProblem:
    user, problem = _staff_user(request)
    if problem or user is None:
        return problem or _problem(401, "User not authenticated", "unauthenticated")
    context, context_problem = _resolve_activity_context(
        request,
        user,
        client_id,
        resource_id,
    )
    if context_problem or context is None:
        return context_problem or _problem(404, "Activity context not found.", "not_found")
    return activity_page(
        user=user,
        context=context,
        page=page,
        page_size=page_size,
    )


@operational_polish_router.get(
    "/notifications",
    response={200: NotificationListOut, 401: ProblemDetail, 403: ProblemDetail},
)
def list_notifications(
    request: HttpRequest,
    limit: int = 30,
) -> NotificationListOut | StaffProblem:
    user, problem = _staff_user(request)
    if problem or user is None:
        return problem or _problem(401, "User not authenticated", "unauthenticated")
    refresh_notifications(user)
    limit = min(max(limit, 1), 100)
    notifications = Notification.objects.filter(
        user=user,
        resolved_at__isnull=True,
        dismissed_at__isnull=True,
    ).order_by("read_at", "-severity", "-created_at", "-id")
    unread_count = notifications.filter(read_at__isnull=True).count()
    return NotificationListOut(
        items=[_notification_out(item) for item in notifications[:limit]],
        unread_count=unread_count,
    )


@operational_polish_router.post(
    "/notifications/{notification_id}/read",
    response={
        200: NotificationActionOut,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def read_notification(
    request: HttpRequest,
    notification_id: int,
) -> NotificationActionOut | StaffProblem:
    user, problem = _staff_user(request)
    if problem or user is None:
        return problem or _problem(401, "User not authenticated", "unauthenticated")
    notification = Notification.objects.filter(user=user, id=notification_id).first()
    if notification is None:
        return _problem(404, "Notification not found.", "not_found")
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at", "updated_at"])
    return NotificationActionOut(
        id=notification.id,
        read_at=notification.read_at,
        dismissed=notification.dismissed_at is not None,
    )


@operational_polish_router.post(
    "/notifications/{notification_id}/dismiss",
    response={
        200: NotificationActionOut,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def dismiss_notification(
    request: HttpRequest,
    notification_id: int,
) -> NotificationActionOut | StaffProblem:
    user, problem = _staff_user(request)
    if problem or user is None:
        return problem or _problem(401, "User not authenticated", "unauthenticated")
    notification = Notification.objects.filter(user=user, id=notification_id).first()
    if notification is None:
        return _problem(404, "Notification not found.", "not_found")
    now = timezone.now()
    notification.dismissed_at = now
    notification.read_at = notification.read_at or now
    notification.save(update_fields=["dismissed_at", "read_at", "updated_at"])
    return NotificationActionOut(
        id=notification.id,
        read_at=notification.read_at,
        dismissed=True,
    )


@operational_polish_router.post(
    "/notifications/read-all",
    response={200: NotificationCountOut, 401: ProblemDetail, 403: ProblemDetail},
)
def read_all_notifications(request: HttpRequest) -> NotificationCountOut | StaffProblem:
    user, problem = _staff_user(request)
    if problem or user is None:
        return problem or _problem(401, "User not authenticated", "unauthenticated")
    Notification.objects.filter(
        user=user,
        resolved_at__isnull=True,
        dismissed_at__isnull=True,
        read_at__isnull=True,
    ).update(read_at=timezone.now())
    publish_change(LiveChange("notifications", user_id=str(user.pk)))
    return NotificationCountOut(unread_count=0)


@operational_polish_router.post(
    "/audit-events/{event_id}/acknowledge",
    response={200: dict, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def acknowledge_security_event(
    request: HttpRequest,
    event_id: int,
) -> dict[str, object] | StaffProblem:
    """Record an explicit audit acknowledgement without mutating append-only history."""
    user, problem = _staff_user(request)
    if problem or user is None:
        return problem or _problem(401, "User not authenticated", "unauthenticated")
    if not user.has_perm("core.view_auditevent"):
        return _problem(403, "You do not have permission to view audit events.", "forbidden")
    source = scoped_audit_events(user).filter(id=event_id).first()
    if source is None:
        return _problem(404, "Audit event not found.", "not_found")
    acknowledgement = AuditEvent.record(
        action="audit.acknowledged",
        actor=user,
        target=source,
        target_label=source.target_label or source.action,
        client_id=source.client_id,
        resource_id=source.resource_id,
        metadata={"source_event_id": source.id},
    )
    return {"success": True, "event_id": acknowledgement.id}

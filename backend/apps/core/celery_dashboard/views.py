from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError
from ninja.security import django_auth

from adbsoftwaresolutions.celery import app
from apps.core.live.events import LiveChange, publish_change
from apps.core.models import AuditEvent, CeleryTaskExecution

from .schemas import (
    ActionOut,
    ExecutionOut,
    ExecutionPageOut,
    OverviewOut,
    TaskLogOut,
    TaskLogPageOut,
)
from .services import overview

celery_dashboard_router = Router(tags=["admin-celery"], auth=django_auth)


def require_administrator(request: HttpRequest) -> None:
    user = request.user
    if not user.is_authenticated:
        raise HttpError(401, "Authentication required.")
    if not user.is_active or not user.is_staff or not user.is_superuser:
        raise HttpError(403, "Full administrator access is required.")


@celery_dashboard_router.get("/celery/overview", response=OverviewOut)
def dashboard_overview(request: HttpRequest) -> OverviewOut:
    require_administrator(request)
    return overview()


@celery_dashboard_router.get("/celery/tasks", response=ExecutionPageOut)
def task_history(
    request: HttpRequest, state: str = "", search: str = "", page: int = 1, page_size: int = 25
) -> ExecutionPageOut:
    require_administrator(request)
    if state and state not in CeleryTaskExecution.State.values:
        raise HttpError(400, "Unknown task state.")
    page_size = min(max(page_size, 1), 100)
    page = max(page, 1)
    tasks = CeleryTaskExecution.objects.all()
    if state:
        tasks = tasks.filter(state=state)
    if search.strip():
        text = search.strip()[:255]
        tasks = tasks.filter(
            Q(task_name__icontains=text)
            | Q(id__icontains=text)
            | Q(worker__icontains=text)
            | Q(queue__icontains=text)
        )
    return ExecutionPageOut(
        items=[
            ExecutionOut.from_orm(task) for task in tasks[(page - 1) * page_size : page * page_size]
        ],
        total=tasks.count(),
        page=page,
        page_size=page_size,
    )


@celery_dashboard_router.get("/celery/tasks/{task_id}", response=ExecutionOut)
def task_detail(request: HttpRequest, task_id: str) -> ExecutionOut:
    require_administrator(request)
    task = CeleryTaskExecution.objects.filter(pk=task_id).first()
    if not task:
        raise HttpError(404, "Task execution not found.")
    return ExecutionOut.from_orm(task)


@celery_dashboard_router.get("/celery/tasks/{task_id}/logs", response=TaskLogPageOut)
def task_logs(
    request: HttpRequest, task_id: str, page: int = 1, page_size: int = 100, level: str = ""
) -> TaskLogPageOut:
    require_administrator(request)
    execution = CeleryTaskExecution.objects.filter(pk=task_id).first()
    if execution is None:
        raise HttpError(404, "Task execution not found.")
    levels = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
    if level and level not in levels:
        raise HttpError(400, "Unknown log severity.")
    page_size = min(max(page_size, 1), 200)
    page = max(page, 1)
    logs = execution.logs.order_by("-id")
    if level:
        logs = logs.filter(level__gte=levels[level])
    items = list(logs[(page - 1) * page_size : page * page_size])
    return TaskLogPageOut(
        items=[TaskLogOut.from_orm(item) for item in reversed(items)],
        total=logs.count(),
        page=page,
        page_size=page_size,
        truncated=execution.logs_truncated,
    )


@celery_dashboard_router.post("/celery/tasks/{task_id}/revoke", response=ActionOut)
def revoke_task(request: HttpRequest, task_id: str) -> ActionOut:
    require_administrator(request)
    with transaction.atomic():
        task = CeleryTaskExecution.objects.select_for_update().filter(pk=task_id).first()
        if not task:
            raise HttpError(404, "Task execution not found.")
        if task.state not in ("QUEUED", "RETRY") or task.revoke_requested_at:
            raise HttpError(
                409,
                "Only queued or retrying tasks without a pending revoke request can be revoked.",
            )
        # Cooperative revoke only: never terminate a worker or interrupt a business write.
        try:
            app.control.revoke(task.id, terminate=False)
        except Exception as exc:
            raise HttpError(503, "Unable to send the revoke request to Celery.") from exc
        task.revoke_requested_at = timezone.now()
        task.save(update_fields=["revoke_requested_at", "updated_at"])
        AuditEvent.record(
            action="celery.task.revoke_requested",
            actor=request.user,
            target=task,
            metadata={"task_id": task.id, "task_name": task.task_name},
        )
        publish_change(LiveChange("celery", global_scope=True, superuser_only=True))
    return ActionOut(
        message="Revoke requested. A task that has already started may still finish.",
        task_id=task.id,
    )


@celery_dashboard_router.post("/celery/schedules/{schedule_name}/run", response=ActionOut)
def run_schedule(request: HttpRequest, schedule_name: str) -> ActionOut:
    require_administrator(request)
    entry = app.conf.beat_schedule.get(schedule_name)
    if not entry:
        raise HttpError(404, "Scheduled job not found.")
    if entry.get("args") or entry.get("kwargs"):
        raise HttpError(
            409, "This job requires parameters and cannot be started from the dashboard."
        )
    if AuditEvent.objects.filter(
        actor_id=request.user.pk,
        action="celery.schedule.dispatched",
        target_label=schedule_name,
        created_at__gte=timezone.now() - timedelta(seconds=10),
    ).exists():
        raise HttpError(429, "This job was just dispatched. Wait before starting it again.")
    try:
        result = app.send_task(entry["task"], args=(), kwargs={}, **entry.get("options", {}))
    except Exception as exc:
        raise HttpError(503, "Unable to dispatch the scheduled job to Celery.") from exc
    AuditEvent.record(
        action="celery.schedule.dispatched",
        actor=request.user,
        target_label=schedule_name,
        metadata={"task_id": result.id, "task_name": entry["task"]},
    )
    return ActionOut(message="Scheduled job queued.", task_id=result.id)

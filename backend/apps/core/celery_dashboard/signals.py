from __future__ import annotations

import logging
from contextlib import suppress
from typing import Any

from celery import signals
from django.core.cache import cache
from django.db import DatabaseError, transaction
from django.utils import timezone

from apps.core.live.events import LiveChange, publish_change
from apps.core.models import CeleryTaskExecution

from .logs import append_log, exception_text, install

logger = logging.getLogger(__name__)
TERMINAL_STATES = {"SUCCESS", "FAILURE", "REVOKED", "IGNORED"}


def record(task_id: str | None, task_name: str, state: str, **metadata: Any) -> None:
    if not task_id or not task_name:
        return
    try:
        with transaction.atomic():
            execution, _ = CeleryTaskExecution.objects.select_for_update().get_or_create(
                id=str(task_id)[:255], defaults={"task_name": task_name[:255]}
            )
            now = timezone.now()
            # A publisher may report after a fast worker has already completed.
            if state != "QUEUED" and execution.state not in TERMINAL_STATES:
                execution.state = state
            if state == "QUEUED" and execution.published_at is None:
                execution.published_at = now
            if state == "STARTED" and execution.state == "STARTED":
                execution.started_at = now
                execution.finished_at = None
                execution.error_type = ""
            if state in TERMINAL_STATES and execution.finished_at is None:
                execution.finished_at = now
                if execution.started_at:
                    execution.runtime_seconds = max(0, (now - execution.started_at).total_seconds())
            for field in ("queue", "worker", "retries", "error_type"):
                if metadata.get(field) is not None:
                    value = metadata[field]
                    setattr(
                        execution,
                        field,
                        max(0, int(value))
                        if field == "retries"
                        else str(value)[: 150 if field == "error_type" else 255],
                    )
            execution.save()
            publish_change(LiveChange("celery", global_scope=True, superuser_only=True))
    except (DatabaseError, ValueError, TypeError):
        # Observability must not prevent a business task from executing; never log payloads.
        logger.warning("Celery execution telemetry could not be recorded.")


def published(
    sender: str | None = None,
    headers: dict[str, Any] | None = None,
    routing_key: str = "",
    **kwargs: Any,
) -> None:
    headers = headers or {}
    record(headers.get("id"), sender or "", "QUEUED", queue=routing_key)


def started(task_id: str | None = None, task: Any = None, **kwargs: Any) -> None:
    if task is None or task.request.is_eager:
        return
    record(
        task_id,
        task.name,
        "STARTED",
        worker=task.request.hostname,
        retries=task.request.retries,
        queue=(task.request.delivery_info or {}).get("routing_key", ""),
    )

    append_log(str(task_id), "Task execution started.", attempt=task.request.retries)


def finished(
    task_id: str | None = None, task: Any = None, state: str | None = None, **kwargs: Any
) -> None:
    if task is not None and not task.request.is_eager and state in TERMINAL_STATES | {"RETRY"}:
        record(task_id, task.name, state)
        if state in ("SUCCESS", "IGNORED"):
            append_log(
                str(task_id), f"Task execution finished: {state}.", attempt=task.request.retries
            )


def failed(
    task_id: str | None = None,
    sender: Any = None,
    exception: BaseException | None = None,
    **kwargs: Any,
) -> None:
    if sender is not None and not sender.request.is_eager:
        record(
            task_id,
            sender.name,
            "FAILURE",
            error_type=type(exception).__name__ if exception else "Error",
        )
        append_log(
            str(task_id),
            exception_text(exception) if exception else "Task execution failed.",
            level=logging.ERROR,
            attempt=sender.request.retries,
            task=sender,
        )


def retrying(sender: Any = None, request: Any = None, reason: Any = None, **kwargs: Any) -> None:
    if sender is not None and request is not None and not request.is_eager:
        record(request.id, sender.name, "RETRY", retries=request.retries + 1)
        append_log(
            str(request.id),
            f"Retry requested: {reason}" if reason else "Retry requested.",
            level=logging.WARNING,
            attempt=request.retries,
            task=sender,
        )


def revoked(request: Any = None, **kwargs: Any) -> None:
    if request is not None:
        record(request.id, request.name, "REVOKED", worker=request.hostname)
        append_log(str(request.id), "Task revoked by worker.", level=logging.WARNING)


def worker_changed(**kwargs: Any) -> None:
    with suppress(Exception):
        cache.delete("celery_dashboard:snapshot:v1")
    publish_change(LiveChange("celery", global_scope=True, superuser_only=True))


def heartbeat(**kwargs: Any) -> None:
    try:
        if not cache.add("celery_dashboard:worker_hint", True, timeout=10):
            return
    except Exception:
        return  # SSE reconciliation handles unavailable cache infrastructure.
    worker_changed()


def register() -> None:
    install()
    for signal, receiver in (
        (signals.after_task_publish, published),
        (signals.task_prerun, started),
        (signals.task_postrun, finished),
        (signals.task_failure, failed),
        (signals.task_retry, retrying),
        (signals.task_revoked, revoked),
        (signals.worker_ready, worker_changed),
        (signals.worker_shutdown, worker_changed),
        (signals.heartbeat_sent, heartbeat),
        (signals.after_setup_logger, install),
        (signals.after_setup_task_logger, install),
    ):
        signal.connect(
            receiver, weak=False, dispatch_uid=f"core.celery_dashboard.{receiver.__name__}"
        )

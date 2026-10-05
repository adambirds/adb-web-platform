from __future__ import annotations

from contextlib import suppress
from datetime import timedelta
from typing import Any

from celery.schedules import maybe_schedule
from django.core.cache import cache
from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncHour
from django.utils import timezone

from adbsoftwaresolutions.celery import app
from apps.core.models import CeleryTaskExecution

from .schemas import (
    HourOut,
    LiveTaskOut,
    OverviewOut,
    QueueOut,
    ScheduleOut,
    SnapshotOut,
    WorkerOut,
)

SNAPSHOT_KEY = "celery_dashboard:snapshot:v1"
RETENTION_DAYS = 14


def schedules() -> list[ScheduleOut]:
    return [
        ScheduleOut(
            name=name,
            task_name=entry["task"],
            schedule=str(maybe_schedule(entry["schedule"])),
            queue=entry.get("options", {}).get("queue", app.conf.task_default_queue),
            can_run=not entry.get("args") and not entry.get("kwargs"),
        )
        for name, entry in sorted(app.conf.beat_schedule.items())
    ]


def snapshot() -> SnapshotOut:
    # Short-lived cache bounds expensive worker broadcasts during task-event bursts.
    try:
        cached = cache.get(SNAPSHOT_KEY)
        if cached:
            return SnapshotOut.model_validate(cached)
    except Exception:
        pass  # Cache failure must still allow checking the broker.
    checked_at = timezone.now()
    workers: list[WorkerOut] = []
    queue_names = {app.conf.task_default_queue, *[entry.queue for entry in schedules()]}
    queues: list[QueueOut] = []
    warning = ""
    broker_available = False
    try:
        options = {
            **(app.conf.broker_transport_options or {}),
            "socket_connect_timeout": 2,
            "socket_timeout": 2,
        }
        with app.connection_for_read(connect_timeout=2, transport_options=options) as connection:
            connection.ensure_connection(max_retries=0)
            broker_available = True
            inspector = app.control.inspect(timeout=0.5, connection=connection)
            stats = inspector.stats() or {}
            if stats:
                active = inspector.active(safe=True) or {}
                reserved = inspector.reserved(safe=True) or {}
                scheduled = inspector.scheduled(safe=True) or {}
                subscriptions = inspector.active_queues() or {}
                # A partial response never implies that a missing worker has zero tasks.
                if any(
                    name not in reply
                    for name in stats
                    for reply in (active, reserved, scheduled, subscriptions)
                ):
                    warning = "Some workers did not answer every inspection request; task counts may be incomplete."
                for name, info in sorted(stats.items()):
                    names = sorted({item["name"] for item in subscriptions.get(name, [])})
                    queue_names.update(names)
                    tasks = []
                    for state, items in (
                        ("STARTED", active.get(name, [])),
                        ("RESERVED", reserved.get(name, [])),
                        ("SCHEDULED", scheduled.get(name, [])),
                    ):
                        if len(items) > 100:
                            warning = "Worker task details are limited to 100 tasks per state; counts may be incomplete."
                        for item in items[:100]:
                            request = item.get("request", item)
                            tasks.append(
                                LiveTaskOut(
                                    id=str(request.get("id", "")),
                                    task_name=str(request.get("name", "")),
                                    state=state,
                                    eta=str(item.get("eta", "")),
                                )
                            )
                    workers.append(
                        WorkerOut(
                            name=name,
                            concurrency=info.get("pool", {}).get("max-concurrency"),
                            processed=sum(info.get("total", {}).values()),
                            queues=names,
                            tasks=tasks,
                        )
                    )
            else:
                warning = "No workers responded. Check that workers are running and remote control is enabled."
            for name in sorted(queue_names):
                try:
                    channel = connection.default_channel
                    if connection.transport.driver_type == "redis":
                        # Redis removes an empty list key. Passive queue_declare would
                        # mistake a healthy drained queue for a missing queue. Kombu's
                        # Redis depth read sums LLEN across its priority buckets.
                        count = channel._size(name)
                    else:
                        count = channel.queue_declare(queue=name, passive=True).message_count
                    queues.append(QueueOut(name=name, depth=count))
                except Exception:
                    queues.append(QueueOut(name=name, depth=None))
                    warning = warning or "Some queue depths could not be read."
    except Exception:
        warning = "Celery broker inspection is unavailable. Check the broker and worker services."
        queues = [QueueOut(name=name, depth=None) for name in sorted(queue_names)]
    result = SnapshotOut(
        checked_at=checked_at,
        broker_available=broker_available,
        workers=workers,
        queues=queues,
        warning=warning,
    )
    with suppress(Exception):
        cache.set(SNAPSHOT_KEY, result.model_dump(mode="json"), timeout=10)
    return result


def overview() -> OverviewOut:
    now = timezone.now()
    cutoff = now - timedelta(hours=24)
    recent = CeleryTaskExecution.objects.filter(created_at__gte=cutoff)
    counts = dict.fromkeys(CeleryTaskExecution.State.values, 0)
    counts.update(
        {
            item["state"]: item["count"]
            for item in recent.values("state").annotate(count=Count("id"))
        }
    )
    completions = CeleryTaskExecution.objects.filter(finished_at__gte=cutoff)
    counts.update(
        {
            item["state"]: item["count"]
            for item in completions.values("state").annotate(count=Count("id"))
        }
    )
    series = (
        completions.annotate(hour=TruncHour("finished_at"))
        .values("hour")
        .annotate(
            succeeded=Count("id", filter=Q(state="SUCCESS")),
            failed=Count("id", filter=Q(state="FAILURE")),
            average_runtime=Avg("runtime_seconds"),
        )
        .order_by("hour")
    )
    start = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=23)
    data: dict[Any, Any] = {item["hour"]: item for item in series}
    hours = []
    for offset in range(24):
        hour = start + timedelta(hours=offset)
        item = data.get(hour, {})
        hours.append(
            HourOut(
                hour=hour,
                succeeded=item.get("succeeded", 0),
                failed=item.get("failed", 0),
                average_runtime=item.get("average_runtime"),
            )
        )
    first = (
        CeleryTaskExecution.objects.order_by("created_at")
        .values_list("created_at", flat=True)
        .first()
    )
    return OverviewOut(
        snapshot=snapshot(),
        schedules=schedules(),
        counts=counts,
        average_runtime=completions.aggregate(value=Avg("runtime_seconds"))["value"],
        history_since=first,
        retention_days=RETENTION_DAYS,
        hours=hours,
    )

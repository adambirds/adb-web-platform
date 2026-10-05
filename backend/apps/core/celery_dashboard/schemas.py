from datetime import datetime

from ninja import Schema


class ExecutionOut(Schema):
    id: str
    task_name: str
    state: str
    queue: str
    worker: str
    retries: int
    error_type: str
    published_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    runtime_seconds: float | None
    created_at: datetime
    updated_at: datetime
    revoke_requested_at: datetime | None


class ExecutionPageOut(Schema):
    items: list[ExecutionOut]
    total: int
    page: int
    page_size: int


class LiveTaskOut(Schema):
    id: str
    task_name: str
    state: str
    eta: str = ""


class WorkerOut(Schema):
    name: str
    concurrency: int | None
    processed: int
    queues: list[str]
    tasks: list[LiveTaskOut]


class QueueOut(Schema):
    name: str
    depth: int | None


class SnapshotOut(Schema):
    checked_at: datetime
    broker_available: bool
    workers: list[WorkerOut]
    queues: list[QueueOut]
    warning: str


class ScheduleOut(Schema):
    name: str
    task_name: str
    schedule: str
    queue: str
    can_run: bool


class HourOut(Schema):
    hour: datetime
    succeeded: int
    failed: int
    average_runtime: float | None


class OverviewOut(Schema):
    snapshot: SnapshotOut
    schedules: list[ScheduleOut]
    counts: dict[str, int]
    average_runtime: float | None
    history_since: datetime | None
    retention_days: int
    hours: list[HourOut]


class ActionOut(Schema):
    success: bool = True
    message: str
    task_id: str


class TaskLogOut(Schema):
    id: int
    created_at: datetime
    level: int
    logger_name: str
    message: str
    attempt: int


class TaskLogPageOut(Schema):
    items: list[TaskLogOut]
    total: int
    page: int
    page_size: int
    truncated: bool

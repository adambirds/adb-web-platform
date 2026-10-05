import datetime

from ninja import Schema


class MonitorCheckConfigIn(Schema):
    name: str
    check_type: str
    severity: str = "error"
    target: str
    port: int | None = None
    expected_value: str = ""
    forbidden_value: str = ""
    interval_seconds: int = 300
    timeout_seconds: int = 10
    failure_threshold: int = 3
    recovery_threshold: int = 2
    expiry_warning_days: int = 30
    credential_id: int | None = None


class MonitorCheckCreateIn(MonitorCheckConfigIn):
    resource_id: int


class MonitorCheckUpdateIn(MonitorCheckConfigIn):
    pass


class MonitorCheckConfigOut(MonitorCheckConfigIn):
    id: int
    resource_id: int
    resource_name: str


class MonitorCheckOut(Schema):
    id: int
    resource_id: int
    resource_name: str
    client_id: int | None
    client_name: str | None
    name: str
    check_type: str
    severity: str
    enabled: bool
    target: str
    port: int | None
    status: str
    consecutive_failures: int
    consecutive_successes: int
    last_checked_at: datetime.datetime | None
    next_run_at: datetime.datetime | None
    last_duration_ms: int | None
    last_message: str


class MonitorResultOut(Schema):
    id: int
    outcome: str
    started_at: datetime.datetime
    finished_at: datetime.datetime
    duration_ms: int
    status_code: int | None
    observed_value: str
    message: str


class MonitorIncidentOut(Schema):
    id: int
    check_id: int
    check_name: str
    resource_id: int
    resource_name: str
    client_id: int | None
    client_name: str | None
    status: str
    severity: str
    opened_at: datetime.datetime
    acknowledged_at: datetime.datetime | None
    resolved_at: datetime.datetime | None
    failure_count: int
    summary: str


class MonitorCheckDetailOut(MonitorCheckOut):
    expected_value: str
    forbidden_value: str
    interval_seconds: int
    timeout_seconds: int
    failure_threshold: int
    recovery_threshold: int
    expiry_warning_days: int
    credential_id: int | None
    uptime_24h_percent: float | None
    uptime_7d_percent: float | None
    average_response_24h_ms: int | None
    average_response_7d_ms: int | None
    results: list[MonitorResultOut]
    results_page: int
    results_page_size: int
    results_total: int
    trend_results: list[MonitorResultOut]
    incidents: list[MonitorIncidentOut]


class MonitoringOverviewOut(Schema):
    total_checks: int
    healthy_checks: int
    degraded_checks: int
    failing_checks: int
    pending_checks: int
    open_incidents: int
    checks: list[MonitorCheckOut]
    incidents: list[MonitorIncidentOut]


class MonitorResourceOptionOut(Schema):
    id: int
    name: str
    resource_type: str
    client_id: int | None
    client_name: str | None


class MonitoringOptionsOut(Schema):
    resources: list[MonitorResourceOptionOut]

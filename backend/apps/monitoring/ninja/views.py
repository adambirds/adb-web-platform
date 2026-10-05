from __future__ import annotations

from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db.models import Avg, Count, Q, QuerySet
from django.http import HttpRequest
from django.utils import timezone
from ninja import Router

from apps.credentials.models import StoredCredential
from apps.credentials.policies import scope_credentials_for_user
from apps.infrastructure.models import InfrastructureResource
from apps.infrastructure.policies import scope_infrastructure_resources_for_user
from apps.monitoring.models import MonitorCheck, MonitorIncident, MonitorResult
from apps.monitoring.services import acknowledge_incident
from authentication.ninja.schemas import ProblemDetail

from .schemas import (
    MonitorCheckConfigOut,
    MonitorCheckCreateIn,
    MonitorCheckDetailOut,
    MonitorCheckOut,
    MonitorCheckUpdateIn,
    MonitorIncidentOut,
    MonitoringOptionsOut,
    MonitoringOverviewOut,
    MonitorResourceOptionOut,
    MonitorResultOut,
)

monitoring_router = Router(tags=["admin-monitoring"])
StaffProblem = tuple[int, dict[str, object]]


def _problem(status: int, detail: str, code: str) -> StaffProblem:
    return status, {"message": detail, "success": False, "code": code}


def _permission_problem(request: HttpRequest, *permissions: str) -> StaffProblem | None:
    user = request.user
    if not user.is_authenticated:
        return _problem(401, "Authentication required.", "not_authenticated")
    if not user.is_staff:
        return _problem(403, "Staff access required.", "permission_denied")
    if not all(user.has_perm(permission) for permission in permissions):
        return _problem(403, "You do not have permission for this action.", "permission_denied")
    return None


def _visible_checks(request: HttpRequest) -> QuerySet[MonitorCheck]:
    return MonitorCheck.objects.select_related("resource", "resource__client").filter(
        resource__in=scope_infrastructure_resources_for_user(request.user)
    )


def _visible_check(request: HttpRequest, check_id: int) -> MonitorCheck | None:
    return _visible_checks(request).select_related("credential").filter(id=check_id).first()


def _check_out(check: MonitorCheck) -> MonitorCheckOut:
    resource = check.resource
    return MonitorCheckOut(
        id=check.id,
        resource_id=resource.id,
        resource_name=resource.name,
        client_id=resource.client_id,
        client_name=str(resource.client) if resource.client else None,
        name=check.name,
        check_type=check.check_type,
        severity=check.severity,
        enabled=check.enabled,
        target=check.target,
        port=check.port,
        status=check.status,
        consecutive_failures=check.consecutive_failures,
        consecutive_successes=check.consecutive_successes,
        last_checked_at=check.last_checked_at,
        next_run_at=check.next_run_at,
        last_duration_ms=check.last_duration_ms,
        last_message=check.last_message,
    )


def _check_config_out(request: HttpRequest, check: MonitorCheck) -> MonitorCheckConfigOut:
    return MonitorCheckConfigOut(
        id=check.id,
        resource_id=check.resource_id,
        resource_name=check.resource.name,
        name=check.name,
        check_type=check.check_type,
        severity=check.severity,
        target=check.target,
        port=check.port,
        expected_value=check.expected_value,
        forbidden_value=check.forbidden_value,
        interval_seconds=check.interval_seconds,
        timeout_seconds=check.timeout_seconds,
        failure_threshold=check.failure_threshold,
        recovery_threshold=check.recovery_threshold,
        expiry_warning_days=check.expiry_warning_days,
        credential_id=(
            check.credential_id
            if request.user.has_perm("credentials.view_storedcredential")
            else None
        ),
    )


def _result_out(result: MonitorResult) -> MonitorResultOut:
    return MonitorResultOut(
        id=result.id,
        outcome=result.outcome,
        started_at=result.started_at,
        finished_at=result.finished_at,
        duration_ms=result.duration_ms,
        status_code=result.status_code,
        observed_value=result.observed_value,
        message=result.message,
    )


def _incident_out(incident: MonitorIncident) -> MonitorIncidentOut:
    resource = incident.monitor_check.resource
    return MonitorIncidentOut(
        id=incident.id,
        check_id=incident.monitor_check_id,
        check_name=incident.monitor_check.name,
        resource_id=resource.id,
        resource_name=resource.name,
        client_id=resource.client_id,
        client_name=str(resource.client) if resource.client else None,
        status=incident.status,
        severity=incident.severity,
        opened_at=incident.opened_at,
        acknowledged_at=incident.acknowledged_at,
        resolved_at=incident.resolved_at,
        failure_count=incident.failure_count,
        summary=incident.summary,
    )


def _history_metrics(check: MonitorCheck, since: datetime) -> tuple[float | None, int | None]:
    stats = check.results.filter(started_at__gte=since).aggregate(
        total=Count("id"),
        successes=Count("id", filter=Q(outcome=MonitorResult.Outcome.SUCCESS)),
        average_ms=Avg("duration_ms"),
    )
    total = int(stats["total"] or 0)
    if total == 0:
        return None, None
    successes = int(stats["successes"] or 0)
    uptime = round((successes / total) * 100, 2)
    average = stats["average_ms"]
    return uptime, round(float(average)) if average is not None else None


def _check_detail_out(
    request: HttpRequest,
    check: MonitorCheck,
    results_page: int = 1,
    results_page_size: int = 50,
) -> MonitorCheckDetailOut:
    now = timezone.now()
    uptime_24h, average_24h = _history_metrics(check, now - timedelta(hours=24))
    uptime_7d, average_7d = _history_metrics(check, now - timedelta(days=7))
    results_page_size = max(1, min(results_page_size, 100))
    results_total = check.results.count()
    last_page = max(1, (results_total + results_page_size - 1) // results_page_size)
    results_page = max(1, min(results_page, last_page))
    offset = (results_page - 1) * results_page_size
    results = list(
        check.results.order_by("-started_at", "-id")[offset : offset + results_page_size]
    )
    timing_types = {
        MonitorCheck.CheckType.ICMP,
        MonitorCheck.CheckType.TCP,
        MonitorCheck.CheckType.HTTP,
        MonitorCheck.CheckType.CONTENT,
        MonitorCheck.CheckType.DNS,
        MonitorCheck.CheckType.TLS,
    }
    trend = (
        list(check.results.order_by("-started_at", "-id")[:200])
        if check.check_type in timing_types
        else []
    )
    incidents = list(check.incidents.order_by("status", "-opened_at", "-id")[:20])
    base = _check_out(check)
    return MonitorCheckDetailOut(
        **base.model_dump(),
        expected_value=check.expected_value,
        forbidden_value=check.forbidden_value,
        interval_seconds=check.interval_seconds,
        timeout_seconds=check.timeout_seconds,
        failure_threshold=check.failure_threshold,
        recovery_threshold=check.recovery_threshold,
        expiry_warning_days=check.expiry_warning_days,
        credential_id=(
            check.credential_id
            if request.user.has_perm("credentials.view_storedcredential")
            else None
        ),
        uptime_24h_percent=uptime_24h,
        uptime_7d_percent=uptime_7d,
        average_response_24h_ms=average_24h,
        average_response_7d_ms=average_7d,
        results=[_result_out(result) for result in results],
        results_page=results_page,
        results_page_size=results_page_size,
        results_total=results_total,
        trend_results=[_result_out(result) for result in reversed(trend)],
        incidents=[_incident_out(incident) for incident in incidents],
    )


def _resolve_credential(
    request: HttpRequest,
    credential_id: int | None,
) -> StoredCredential | StaffProblem | None:
    if credential_id is None:
        return None
    credential_problem = _permission_problem(request, "credentials.view_storedcredential")
    if credential_problem:
        return credential_problem
    credential = (
        scope_credentials_for_user(request.user)
        .filter(id=credential_id, status=StoredCredential.Status.ACTIVE)
        .first()
    )
    if credential is None:
        return _problem(404, "Credential not found.", "not_found")
    return credential


def _apply_check_config(
    check: MonitorCheck,
    payload: MonitorCheckUpdateIn | MonitorCheckCreateIn,
    credential: StoredCredential | None,
) -> None:
    check.credential = credential
    for field_name in (
        "name",
        "check_type",
        "severity",
        "target",
        "port",
        "expected_value",
        "forbidden_value",
        "interval_seconds",
        "timeout_seconds",
        "failure_threshold",
        "recovery_threshold",
        "expiry_warning_days",
    ):
        setattr(check, field_name, getattr(payload, field_name))


@monitoring_router.get(
    "/monitoring/options",
    response={200: MonitoringOptionsOut, 401: ProblemDetail, 403: ProblemDetail},
)
def monitoring_options(request: HttpRequest) -> MonitoringOptionsOut | StaffProblem:
    problem = _permission_problem(request, "monitoring.add_monitorcheck")
    if problem:
        return problem
    resources = (
        scope_infrastructure_resources_for_user(request.user)
        .exclude(
            lifecycle_status__in=[
                InfrastructureResource.LifecycleStatus.RETIRED,
                InfrastructureResource.LifecycleStatus.ARCHIVED,
            ]
        )
        .select_related("client")
        .order_by("name", "id")[:500]
    )
    return MonitoringOptionsOut(
        resources=[
            MonitorResourceOptionOut(
                id=resource.id,
                name=resource.name,
                resource_type=resource.resource_type,
                client_id=resource.client_id,
                client_name=str(resource.client) if resource.client else None,
            )
            for resource in resources
        ]
    )


@monitoring_router.get(
    "/monitoring/overview",
    response={200: MonitoringOverviewOut, 401: ProblemDetail, 403: ProblemDetail},
)
def monitoring_overview(
    request: HttpRequest,
    client_id: int | None = None,
    resource_id: int | None = None,
) -> MonitoringOverviewOut | StaffProblem:
    problem = _permission_problem(
        request,
        "monitoring.view_monitorcheck",
        "monitoring.view_monitorincident",
    )
    if problem:
        return problem
    checks = _visible_checks(request)
    if client_id is not None:
        checks = checks.filter(resource__client_id=client_id)
    if resource_id is not None:
        checks = checks.filter(resource_id=resource_id)

    current_checks = list(
        checks.filter(enabled=True).order_by("status", "resource__name", "name")[:100]
    )
    incidents = list(
        MonitorIncident.objects.select_related(
            "monitor_check",
            "monitor_check__resource",
            "monitor_check__resource__client",
        )
        .filter(monitor_check__in=checks, status__in=["open", "acknowledged"])
        .order_by("status", "-opened_at")[:100]
    )
    return MonitoringOverviewOut(
        total_checks=checks.filter(enabled=True).count(),
        healthy_checks=checks.filter(enabled=True, status=MonitorCheck.Status.HEALTHY).count(),
        degraded_checks=checks.filter(enabled=True, status=MonitorCheck.Status.DEGRADED).count(),
        failing_checks=checks.filter(enabled=True, status=MonitorCheck.Status.FAILING).count(),
        pending_checks=checks.filter(enabled=True, status=MonitorCheck.Status.PENDING).count(),
        open_incidents=len(incidents),
        checks=[_check_out(check) for check in current_checks],
        incidents=[_incident_out(incident) for incident in incidents],
    )


@monitoring_router.post(
    "/monitoring/checks",
    response={
        201: MonitorCheckOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def create_monitor_check(
    request: HttpRequest,
    payload: MonitorCheckCreateIn,
) -> tuple[int, MonitorCheckOut | dict[str, object]]:
    problem = _permission_problem(request, "monitoring.add_monitorcheck")
    if problem:
        return problem
    resource = (
        scope_infrastructure_resources_for_user(request.user).filter(id=payload.resource_id).first()
    )
    if resource is None:
        return _problem(404, "Infrastructure resource not found.", "not_found")
    credential = _resolve_credential(request, payload.credential_id)
    if isinstance(credential, tuple):
        return credential
    check = MonitorCheck(resource=resource)
    _apply_check_config(check, payload, credential)
    try:
        check.full_clean()
        check.save()
    except ValidationError as error:
        return _problem(400, "; ".join(error.messages), "validation_error")
    return 201, _check_out(check)


@monitoring_router.get(
    "/monitoring/checks/{check_id}/configuration",
    response={
        200: MonitorCheckConfigOut,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def monitor_check_configuration(
    request: HttpRequest,
    check_id: int,
) -> MonitorCheckConfigOut | StaffProblem:
    problem = _permission_problem(request, "monitoring.change_monitorcheck")
    if problem:
        return problem
    check = _visible_check(request, check_id)
    if check is None:
        return _problem(404, "Monitoring check not found.", "not_found")
    return _check_config_out(request, check)


@monitoring_router.get(
    "/monitoring/checks/{check_id}",
    response={
        200: MonitorCheckDetailOut,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def monitor_check_detail(
    request: HttpRequest,
    check_id: int,
    results_page: int = 1,
    results_page_size: int = 50,
) -> MonitorCheckDetailOut | StaffProblem:
    problem = _permission_problem(
        request,
        "monitoring.view_monitorcheck",
        "monitoring.view_monitorresult",
        "monitoring.view_monitorincident",
    )
    if problem:
        return problem
    check = _visible_check(request, check_id)
    if check is None:
        return _problem(404, "Monitoring check not found.", "not_found")
    return _check_detail_out(request, check, results_page, results_page_size)


@monitoring_router.put(
    "/monitoring/checks/{check_id}",
    response={
        200: MonitorCheckOut,
        400: ProblemDetail,
        401: ProblemDetail,
        403: ProblemDetail,
        404: ProblemDetail,
    },
)
def update_monitor_check(
    request: HttpRequest,
    check_id: int,
    payload: MonitorCheckUpdateIn,
) -> MonitorCheckOut | StaffProblem:
    problem = _permission_problem(request, "monitoring.change_monitorcheck")
    if problem:
        return problem
    check = _visible_check(request, check_id)
    if check is None:
        return _problem(404, "Monitoring check not found.", "not_found")
    credential: StoredCredential | None
    if (
        payload.credential_id is None
        and check.credential_id is not None
        and not request.user.has_perm("credentials.view_storedcredential")
    ):
        credential = check.credential
    else:
        resolved_credential = _resolve_credential(request, payload.credential_id)
        if isinstance(resolved_credential, tuple):
            return resolved_credential
        credential = resolved_credential
    _apply_check_config(check, payload, credential)
    try:
        check.full_clean()
        check.save()
    except ValidationError as error:
        return _problem(400, "; ".join(error.messages), "validation_error")
    return _check_out(check)


@monitoring_router.post(
    "/monitoring/checks/{check_id}/pause",
    response={200: MonitorCheckOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def pause_monitor_check(request: HttpRequest, check_id: int) -> MonitorCheckOut | StaffProblem:
    problem = _permission_problem(request, "monitoring.change_monitorcheck")
    if problem:
        return problem
    check = _visible_check(request, check_id)
    if check is None:
        return _problem(404, "Monitoring check not found.", "not_found")
    if check.enabled or check.status != MonitorCheck.Status.PAUSED:
        check.enabled = False
        check.status = MonitorCheck.Status.PAUSED
        check.next_run_at = None
        check.save(update_fields=["enabled", "status", "next_run_at", "updated_at"])
    return _check_out(check)


@monitoring_router.post(
    "/monitoring/checks/{check_id}/resume",
    response={200: MonitorCheckOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def resume_monitor_check(request: HttpRequest, check_id: int) -> MonitorCheckOut | StaffProblem:
    problem = _permission_problem(request, "monitoring.change_monitorcheck")
    if problem:
        return problem
    check = _visible_check(request, check_id)
    if check is None:
        return _problem(404, "Monitoring check not found.", "not_found")
    if not check.enabled or check.status == MonitorCheck.Status.PAUSED:
        check.enabled = True
        check.status = MonitorCheck.Status.PENDING
        check.next_run_at = timezone.now()
        check.consecutive_failures = 0
        check.consecutive_successes = 0
        check.save(
            update_fields=[
                "enabled",
                "status",
                "next_run_at",
                "consecutive_failures",
                "consecutive_successes",
                "updated_at",
            ]
        )
    return _check_out(check)


@monitoring_router.post(
    "/monitoring/incidents/{incident_id}/acknowledge",
    response={200: MonitorIncidentOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def acknowledge_monitor_incident(
    request: HttpRequest,
    incident_id: int,
) -> MonitorIncidentOut | StaffProblem:
    problem = _permission_problem(
        request,
        "monitoring.view_monitorincident",
        "monitoring.change_monitorincident",
    )
    if problem:
        return problem
    incident = (
        MonitorIncident.objects.select_related(
            "monitor_check",
            "monitor_check__resource",
            "monitor_check__resource__client",
        )
        .filter(id=incident_id, monitor_check__in=_visible_checks(request))
        .first()
    )
    if incident is None:
        return _problem(404, "Monitoring incident not found.", "not_found")
    return _incident_out(acknowledge_incident(incident))

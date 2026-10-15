# Celery operations

The operations workspace provides a native dashboard at `/admin/celery`, linked
under Administration. It shares the platform's Django authentication and SSE
connection. There is no separate monitoring service, OAuth application or port.

## Access and data boundaries

Only active staff Django **superusers** can read history, inspect workers, run
scheduled jobs or request task revocation. An Administrator group or ordinary
staff permissions do not grant this platform-wide access. Django checks this on
every endpoint; the sidebar and page apply the same rule. SSE checks current
superuser status before sending Celery invalidation hints.

History stores task ID/name, state, queue, worker, retry count, timestamps,
duration and exception **class**. Execution summaries never contain task payloads
or raw worker inspection replies. Each task has a separate administrator-only
log viewer for redacted diagnostic messages and failure tracebacks, without
local-variable snapshots. Arguments/keyword arguments/results are not dumped
automatically; Celery's automatic result-summary logs are excluded.

## Dashboard

- Broker reachability, workers responding and broker queue depths.
- Worker concurrency, processed count and current active/reserved/scheduled
  tasks. Worker counts can be partial; warnings report unanswered inspections.
- Filtered, server-paginated history and task detail, including revocation state.
- Per-task logs with timestamps, severity filters, attempt numbers, older/newer
  pages and Follow live. Logs render as text, including multiline tracebacks.
- Succeeded/failed completions and average durations for the last 24 hours,
  with hourly activity bars.
- Code-configured Beat jobs and their schedules. This is the configured schedule,
  not proof that Beat is running; operate exactly one Beat scheduler as before.

Lifecycle signals automatically track tasks from the updated API, Beat and
workers; individual business tasks do not need tracking wrappers. Recording
starts after deploying the migration and restarting those processes. Old result
backend records are not imported. Eager/in-process task executions are excluded.

Redis SSE invalidation updates the current view while retaining filters and
pagination. Worker heartbeats also issue bounded refresh hints. Inspection uses
short timeouts and a ten-second cache. Queue depths include Redis priority
buckets and exclude tasks already reserved by workers. No responding worker or
unavailable broker is reported explicitly; history remains readable during a
broker outage. Failed telemetry never prevents a business task executing.

History is the **last observed lifecycle state**. A crashed worker or a missed
signal can leave an unfinished row; worker inspection is the live view. The
dashboard does not incorrectly declare tasks failed solely because they are
absent from a short inspection response.

## Per-task logs

Open a task from the history table to view its captured logs. Follow live shows
the latest page and scrolls to the bottom; browsing older pages pauses following.
Filtering uses a minimum severity, so Error also includes Critical events.

Workers automatically capture Python logging associated with the executing task,
Celery redirected stdout/stderr, lifecycle events, retries and failure tracebacks.
Root/task/redirected logger handlers are installed again after Celery configures
logging. Association uses Celery's current task context, so concurrent worker
processes/threads do not mix task logs. Child threads without a task context and
external subprocess/container logs are outside this capture. A logger must reach
root or Celery's task logger for capture; do not suppress or bypass logging.

Known secret environment values, sensitive named task inputs, credential-shaped
fields, authentication headers, URL credentials, PEM blocks and account-token
links are redacted **before storage**. Credential patterns are matched before
known literal values, so short secrets cannot corrupt a field name, authentication
scheme or token-link prefix and prevent its value from being scrubbed.
Task code must still avoid logging secrets
or message bodies: redaction is best-effort protection, not a secret-storage
mechanism. Tracebacks omit local-variable dumps. Celery argument/result dumps and
SQL logging are excluded. Capture failure never interrupts the business task.

Capture is bounded to 2,000 entries per execution and 8,000 characters per entry;
the UI reports when the execution cap is reached. Logs are retained for 14 days,
including logs attached to unfinished executions. Task-row removal also cascades
to its logs. Existing task history has no recoverable logs until updated workers
execute tasks; past console output is not retroactively imported.

SSE transports only invalidation hints, never log text. The log API rechecks active
staff superuser access on every request. The log viewer handles denied access and
connection failures explicitly. Task messages and tracebacks remain sensitive
operational diagnostics even after secret redaction.

## Controls

**Run now** dispatches an extra execution of an existing, parameter-free Beat
job after confirmation. The normal schedule remains unchanged. It cannot invoke
an arbitrary task name or accept arbitrary payloads. A short per-user dispatch
cooldown limits accidental double submission.

**Revoke** requests cooperative revocation for queued/retrying executions.
Celery may already have started the task by the time the request arrives. The UI
shows “Revoke requested” until the worker reports revocation; a running task may
still finish. No worker termination, queue purge, arbitrary payload replay or
worker shutdown is exposed. Every control action is recorded in AuditEvent.

## Deployment

1. Run `python backend/manage.py migrate` with the normal backend environment,
   including the core task-log migration.
2. Deploy/restart the API, all workers, Beat and the operations frontend.
3. Keep existing PostgreSQL, Celery broker/result Redis and shared cache Redis.
   No new dependency, secret, Redis database or deployment image is required.
4. Preserve Celery remote control (enabled by default) and broker connectivity
   from the backend for worker inspection and cooperative revocation.
5. Keep the existing SSE ASGI/proxy configuration. No additional SSE endpoint
   is needed.
6. Beat dispatches `core.purge_celery_history` daily. Terminal history older than
   14 days is removed; unfinished executions are retained for investigation.

Remove any previously deployed standalone monitoring container/ingress and its
OAuth secrets from deployment configuration. Repository CI now builds only the
backend, Celery worker and Beat images.

## Code map

- `backend/apps/core/celery_dashboard/`: typed schemas, signals, services and API.
- `backend/apps/core/models.py`: `CeleryTaskExecution` metadata identity.
- `backend/apps/core/tasks.py`: terminal-history retention task.
- `backend/adbsoftwaresolutions/celery.py`: configured schedule.
- `sites/adb-software-solutions/src/app/(admin)/admin/celery/`: dashboard.
- `backend/apps/core/tests/test_celery_dashboard.py`: lifecycle and permissions.

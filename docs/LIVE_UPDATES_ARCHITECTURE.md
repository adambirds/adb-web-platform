# Shared live updates

The authenticated operations workspace uses one Server-Sent Events (SSE)
connection per browser tab at `GET /api/admin/events`. Django remains the source
of truth for business data, permissions and Client/Internal ownership.

## Flow

Reviewed model saves/deletes and explicit bulk-update hooks publish routing hints
through the existing default Redis connection **after database commit**. Rollbacks
publish nothing. Celery workers and web processes use the same Redis channel,
including processed GitHub webhooks and monitoring observations.

The ASGI stream checks the current staff session and capability, Client and Ticket
Queue scopes before forwarding each hint. It reloads the session/user for events
and every 15-second heartbeat, so expired sessions, logout, disabled accounts and
password changes close the stream. Notification events target only their owner.
The browser receives topic names, never record IDs, titles, bodies or secrets.
Origin restrictions use the backend's existing CORS allowed origins.

`LiveEventsProvider` in the admin layout shares the connection. Screens use
`useLiveRefresh` to subscribe to topics and re-fetch their existing permissioned
APIs. Changes are coalesced over 250 ms; filters, pagination and form state remain
owned by each screen. Permission hints refresh the current user silently.

Subscriptions cover GitHub (including selected run jobs), monitoring checks and
observations, the notification bell and dashboard, infrastructure resources,
credentials, knowledge-base browsing, clients, leads, projects, tasks, tickets,
calendar and personal activity changes. Celery operations subscribe to the
`celery` topic: task lifecycle changes and worker startup/shutdown/heartbeats
publish metadata-free refresh hints. Worker heartbeats are coalesced to at most
one hint per ten seconds. The stream checks current active staff superuser
access for every Celery hint; normal staff never receive this topic.
New screens should subscribe explicitly
rather than open their own stream. Mutation actions still use normal APIs.

## Recovery and limits

EventSource reconnects automatically with a three-second retry hint. Connection
readiness and returning to a visible tab refresh current data. Hidden tabs skip
refresh requests. While disconnected, screens reconcile every 30 seconds;
connected screens reconcile every two minutes to cover time-based computed
notifications and writes that bypass Django model signals.

Redis Pub/Sub is transient: these hints have no persistent history or replay IDs.
The database and existing integration recovery jobs retain the authoritative
state. Redis failure never fails a business write. Bulk `QuerySet.update()` does
not fire model signals: services must publish a scoped hint explicitly, or their
changes appear through reconciliation. GitHub initial synchronisation also emits
repository/installation saves after bulk changes.

SSE is for invalidating read state, not transporting logs or credential secrets.
GitHub log retrieval and workflow actions keep their separate permission and audit
checks. Delivery, worker scheduling and API availability determine latency.

## Deployment

- Run the backend with its existing **ASGI** application. Async streaming under
  WSGI consumes a worker and is not supported for this feature.
- Use the same default Redis configuration across API and Celery processes.
  No additional broker, port or signing key is needed.
- Permit authenticated GET requests to `/api/admin/events`. Preserve cookies and
  credentialed CORS for the configured frontend origin.
- Disable reverse-proxy buffering for this path. Responses include
  `X-Accel-Buffering: no` and `Cache-Control: no-store, no-transform`; do not cache
  or compress/buffer the stream. For nginx, set `proxy_buffering off` and an idle
  `proxy_read_timeout` comfortably above the 15-second heartbeat (e.g. 60 seconds).
- Prefer HTTP/2 at the browser-facing proxy for multiple tabs; HTTP/1 browsers have
  a small per-origin connection limit.
- Verify in browser Network tools that the events request stays open, a `ready`
  event arrives, and a monitoring result or processed GitHub webhook triggers a
  topic event and a follow-up API fetch without a page reload.

References: [Django streaming responses](https://docs.djangoproject.com/en/6.0/ref/request-response/#django.http.StreamingHttpResponse),
[MDN SSE](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events),
[redis-py asynchronous Pub/Sub](https://redis.readthedocs.io/en/stable/examples/asyncio_examples.html).

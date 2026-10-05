# Resource monitoring and technical health

Scheduled checks, historical results and failure/recovery incidents attached to Infrastructure resources.

## Code map

| Location                       | Responsibility                                       |
| ------------------------------ | ---------------------------------------------------- |
| [models.py](./models.py)       | Checks, results and incidents                        |
| [execution.py](./execution.py) | Network/protocol check execution                     |
| [services.py](./services.py)   | Observation recording and incident transitions       |
| [tasks.py](./tasks.py)         | Celery scheduling and execution                      |
| [ninja/](./ninja/)             | Global, Client and resource monitoring APIs          |
| [tests/](./tests/)             | Domain regression, API and permission-boundary tests |
| [migrations/](./migrations/)   | Ordered database history                             |
| [admin.py](./admin.py)         | Django admin registration                            |
| [apps.py](./apps.py)           | Django app configuration                             |

## Tests and related code

From the repository root, run `tools/test-backend apps.monitoring.tests`.
For a single module, use `tools/test-backend apps.monitoring.tests.test_<topic>`.

API routers are assembled in
[adbsoftwaresolutions/ninja/routers.py](../../adbsoftwaresolutions/ninja/routers.py).
Internal browser workflows live in
[the combined Software Solutions application](../../../sites/adb-software-solutions/README.md).

Read the [backend guide](../../README.md) for shared conventions and the
[canonical documentation map](../../../docs/README.md) before domain changes.

## ICMP runtime requirements

ICMP monitoring uses `icmplib` directly through Python sockets, with one echo
request per check and the configured reply timeout. No `ping` executable is
required. IPv4 and IPv6 targets are supported. Install the regenerated runtime
requirements in both Django/API and Celery worker environments and restart them
after updating dependencies.

On Linux, unprivileged ICMP datagram sockets require the process's group to be
included in `net.ipv4.ping_group_range`. Check that namespace's current value with:

```bash
cat /proc/sys/net/ipv4/ping_group_range
id -g
```

If the group is outside the permitted range, configure the host/container's
sysctl to include the monitoring worker group. For example, a worker running
with group ID 1000 can use `net.ipv4.ping_group_range=1000 1000`. Apply this in
the worker's network namespace (Docker Compose supports a service `sysctls`
setting). The application does not modify kernel settings or require root/raw
socket privileges on Linux. Other operating systems may require their own ICMP
socket permissions; Windows requires administrator permissions.

A target that does not reply is recorded as a failed reachability check.
Permission, name-resolution and socket setup failures are recorded as execution
errors, with actionable permission guidance rather than a missing executable
error. A hostname's DNS resolution is handled by the OS resolver; the configured
probe timeout bounds the echo reply wait, not DNS lookup time.

## Observation history pagination

The check workspace shows ten observations per page, newest first, with shared
Previous/Next controls and the total record count. Older results remain
accessible beyond the former latest-50 cutoff. Health metrics continue to use
all observations within their time windows, independently of the selected page.

The existing check detail endpoint accepts `results_page` and
`results_page_size`, and returns `results_page`, `results_page_size` and
`results_total` alongside `results`. API clients without query parameters retain
the default first page of 50. Page sizes are bounded to 1–100; out-of-range pages
resolve to the nearest available page. Ordering uses descending start time and
ID to handle matching timestamps. Existing history capabilities and resource
Client/Internal scope checks apply to every page.

## Timing history graph

ICMP, TCP, HTTP, expected/forbidden content, DNS and live TLS checks show an
interactive duration graph in the check workspace. The API's `trend_results`
contains the latest 200 observations in chronological order, independently of
the paginated result list. It uses the same history permissions and resource
scope checks as check detail. Stored Domain/Certificate expiry checks return no
timing series: local metadata lookup duration is not a useful health metric.

The graph plots successful **complete probe durations**, not pure ICMP RTT.
DNS resolution, connection setup and other probe work can contribute to those
stored durations. Failure and execution-error markers use a separate band and
break the successful timing line; timeout durations do not inflate that line's
scale. Hover, tap or keyboard-focus a sample for its timestamp, outcome, duration
and safe result message. Empty and failure-only histories are supported.

# Shared platform foundations

Brand identity, audit history, preferences and cross-domain operational projections. Brand identity is separate from Client/Internal ownership.

## Code map

| Location                                             | Responsibility                                                |
| ---------------------------------------------------- | ------------------------------------------------------------- |
| [models.py](./models.py)                             | Brands, audit events, Dashboard preferences and notifications |
| [ownership.py](./ownership.py)                       | Shared operational ownership validation                       |
| [dashboard.py](./dashboard.py)                       | Widget catalogue and saved Dashboard layouts                  |
| [operational_search.py](./operational_search.py)     | Permission-aware cross-domain search                          |
| [operational_activity.py](./operational_activity.py) | Scoped Activity projections                                   |
| [notifications.py](./notifications.py)               | Operational reminders                                         |
| [ninja/](./ninja/)                                   | Dashboard, search, Activity and shared operations APIs        |
| [management/commands/](./management/commands/)       | Deterministic development seed commands                       |
| [fixtures/](./fixtures/)                             | Development reference data                                    |
| [tests/](./tests/)                                   | Domain regression, API and permission-boundary tests          |
| [migrations/](./migrations/)                         | Ordered database history                                      |
| [admin.py](./admin.py)                               | Django admin registration                                     |
| [apps.py](./apps.py)                                 | Django app configuration                                      |

## Tests and related code

From the repository root, run `tools/test-backend apps.core.tests`.
For a single module, use `tools/test-backend apps.core.tests.test_<topic>`.

API routers are assembled in
[adbsoftwaresolutions/ninja/routers.py](../../adbsoftwaresolutions/ninja/routers.py).
Internal browser workflows live in
[the combined Software Solutions application](../../../sites/adb-software-solutions/README.md).

Read the [backend guide](../../README.md) for shared conventions and the
[canonical documentation map](../../../docs/README.md) before domain changes.

## Celery operations

[`celery_dashboard/`](celery_dashboard/) contains administrator-only worker
inspection, safe task metadata signals and APIs. `CeleryTaskExecution` in
`models.py` is the history projection; `tasks.py` purges terminal history.
See [the deployment and access guide](../../../docs/CELERY_DASHBOARD.md).

`celery_dashboard/logs.py` captures and redacts task-context worker logs.
`CeleryTaskLog` is the retained diagnostic projection; APIs and UI require
active staff superuser access.

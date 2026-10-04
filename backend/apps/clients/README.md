# Clients, Contacts, Projects and Time

The main operational context for Client work. This app also owns Projects, manual Time Entries and persistent Running Timers, including first-class Internal work.

## Code map

| Location                                                         | Responsibility                                                 |
| ---------------------------------------------------------------- | -------------------------------------------------------------- |
| [models.py](./models.py)                                         | Client, Contact, Project, Time Entry and Running Timer records |
| [services/time_tracking.py](./services/time_tracking.py)         | Authoritative timer and time-context rules                     |
| [ninja/admin_views.py](./ninja/admin_views.py)                   | Client, Contact and Project administration                     |
| [ninja/command_centre_views.py](./ninja/command_centre_views.py) | Client workspace projections                                   |
| [ninja/overview_views.py](./ninja/overview_views.py)             | Client overview                                                |
| [ninja/time_views.py](./ninja/time_views.py)                     | Timer and time-entry operations                                |
| [ninja/time_report_views.py](./ninja/time_report_views.py)       | Time reporting                                                 |
| [tests/](./tests/)                                               | Domain regression, API and permission-boundary tests           |
| [migrations/](./migrations/)                                     | Ordered database history                                       |
| [admin.py](./admin.py)                                           | Django admin registration                                      |
| [apps.py](./apps.py)                                             | Django app configuration                                       |

## Tests and related code

From the repository root, run `tools/test-backend apps.clients.tests`.
For a single module, use `tools/test-backend apps.clients.tests.test_<topic>`.

API routers are assembled in
[adbsoftwaresolutions/ninja/routers.py](../../adbsoftwaresolutions/ninja/routers.py).
Internal browser workflows live in
[the combined Software Solutions application](../../../sites/adb-software-solutions/README.md).

Read the [backend guide](../../README.md) for shared conventions and the
[canonical documentation map](../../../docs/README.md) before domain changes.

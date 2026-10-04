# Leads and commercial enquiries

Lead assignment, lifecycle, Client conversion and communication projections. Email remains part of the shared Ticket/Graph pipeline.

## Code map

| Location                                             | Responsibility                                       |
| ---------------------------------------------------- | ---------------------------------------------------- |
| [models.py](./models.py)                             | Lead records and status/outcome definitions          |
| [services.py](./services.py)                         | Lead business rules and conversion                   |
| [tasks.py](./tasks.py)                               | Background CRM work                                  |
| [ninja/admin_views.py](./ninja/admin_views.py)       | Lead administration                                  |
| [ninja/overview_views.py](./ninja/overview_views.py) | Lead workspace projections                           |
| [ninja/email_views.py](./ninja/email_views.py)       | Ticket-backed Lead email                             |
| [tests/](./tests/)                                   | Domain regression, API and permission-boundary tests |
| [migrations/](./migrations/)                         | Ordered database history                             |
| [admin.py](./admin.py)                               | Django admin registration                            |
| [apps.py](./apps.py)                                 | Django app configuration                             |

## Tests and related code

From the repository root, run `tools/test-backend apps.crm.tests`.
For a single module, use `tools/test-backend apps.crm.tests.test_<topic>`.

API routers are assembled in
[adbsoftwaresolutions/ninja/routers.py](../../adbsoftwaresolutions/ninja/routers.py).
Internal browser workflows live in
[the combined Software Solutions application](../../../sites/adb-software-solutions/README.md).

Read the [backend guide](../../README.md) for shared conventions and the
[canonical documentation map](../../../docs/README.md) before domain changes.

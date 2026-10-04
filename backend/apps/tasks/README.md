# Work management and Calendar

Standalone Internal, Client-owned and Project-owned Tasks, including lists, sections, subtasks, dependencies, recurrence and comments. Calendar Events share operational ownership rules.

## Code map

| Location                     | Responsibility                                                                        |
| ---------------------------- | ------------------------------------------------------------------------------------- |
| [models.py](./models.py)     | Tasks, workflow structure, comments and Calendar Events                               |
| [services.py](./services.py) | Task lifecycle, recurrence and relationship rules                                     |
| [ninja/](./ninja/)           | Task CRUD, quick capture, focus, workspace, timeline, comments and Calendar contracts |
| [tests/](./tests/)           | Domain regression, API and permission-boundary tests                                  |
| [migrations/](./migrations/) | Ordered database history                                                              |
| [admin.py](./admin.py)       | Django admin registration                                                             |
| [apps.py](./apps.py)         | Django app configuration                                                              |

## Tests and related code

From the repository root, run `tools/test-backend apps.tasks.tests`.
For a single module, use `tools/test-backend apps.tasks.tests.test_<topic>`.

API routers are assembled in
[adbsoftwaresolutions/ninja/routers.py](../../adbsoftwaresolutions/ninja/routers.py).
Internal browser workflows live in
[the combined Software Solutions application](../../../sites/adb-software-solutions/README.md).

Read the [backend guide](../../README.md) for shared conventions and the
[canonical documentation map](../../../docs/README.md) before domain changes.

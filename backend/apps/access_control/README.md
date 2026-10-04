# Staff capabilities and object scopes

Staff access profiles, Client grants and Ticket Queue grants. Django permissions supply capabilities; this app supplies object visibility.

## Code map

| Location                     | Responsibility                                       |
| ---------------------------- | ---------------------------------------------------- |
| [models.py](./models.py)     | Access profiles and scope grants                     |
| [policies.py](./policies.py) | Capability checks and scoped querysets               |
| [services.py](./services.py) | Staff and access administration                      |
| [ninja/](./ninja/)           | Users & Access API contracts and endpoints           |
| [tests/](./tests/)           | Domain regression, API and permission-boundary tests |
| [migrations/](./migrations/) | Ordered database history                             |
| [admin.py](./admin.py)       | Django admin registration                            |
| [apps.py](./apps.py)         | Django app configuration                             |

## Tests and related code

From the repository root, run `tools/test-backend apps.access_control.tests`.
For a single module, use `tools/test-backend apps.access_control.tests.test_<topic>`.

API routers are assembled in
[adbsoftwaresolutions/ninja/routers.py](../../adbsoftwaresolutions/ninja/routers.py).
Internal browser workflows live in
[the combined Software Solutions application](../../../sites/adb-software-solutions/README.md).

Read the [backend guide](../../README.md) for shared conventions and the
[canonical documentation map](../../../docs/README.md) before domain changes.

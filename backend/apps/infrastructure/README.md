# Technical resources and topology

Structured Client/Internal resources, specialist technical records and typed relationships. Legacy identity bridges and reconciliation remain explicit until migration is complete.

## Code map

| Location                                                           | Responsibility                                         |
| ------------------------------------------------------------------ | ------------------------------------------------------ |
| [models.py](./models.py)                                           | Django model entrypoint and specialist exports         |
| [resource_models.py](./resource_models.py)                         | Common resource identity and relationships             |
| [specialist_models.py](./specialist_models.py)                     | Compute/network specialists                            |
| [data_application_models.py](./data_application_models.py)         | Database, application and repository specialists       |
| [web_domain_models.py](./web_domain_models.py)                     | Website, Domain, DNS and TLS specialists               |
| [operational_models.py](./operational_models.py)                   | Containers, storage, backups and scheduled operations  |
| [legacy_models.py](./legacy_models.py)                             | Legacy records retained for reconciliation             |
| [legacy_reconciliation.py](./legacy_reconciliation.py)             | Legacy identity reconciliation                         |
| [legacy_specialist_promotion.py](./legacy_specialist_promotion.py) | Promotion into native specialists                      |
| [policies.py](./policies.py)                                       | Resource permissions and scope                         |
| [ninja/](./ninja/)                                                 | Resource, specialist, reconciliation and topology APIs |
| [tests/](./tests/)                                                 | Domain regression, API and permission-boundary tests   |
| [migrations/](./migrations/)                                       | Ordered database history                               |
| [admin.py](./admin.py)                                             | Django admin registration                              |
| [apps.py](./apps.py)                                               | Django app configuration                               |

## Tests and related code

From the repository root, run `tools/test-backend apps.infrastructure.tests`.
For a single module, use `tools/test-backend apps.infrastructure.tests.test_<topic>`.

API routers are assembled in
[adbsoftwaresolutions/ninja/routers.py](../../adbsoftwaresolutions/ninja/routers.py).
Internal browser workflows live in
[the combined Software Solutions application](../../../sites/adb-software-solutions/README.md).

Read the [backend guide](../../README.md) for shared conventions and the
[canonical documentation map](../../../docs/README.md) before domain changes.

Specialist `*_edit.py` modules implement writes; `*_snapshot.py` modules build
read projections. `legacy_*` modules are migration boundaries, not templates
for new resource types.

# Technical resources and topology

Structured Client/Internal resources, specialist technical records and typed relationships. InfrastructureResource is the sole inventory identity.

## Code map

| Location                                                   | Responsibility                                        |
| ---------------------------------------------------------- | ----------------------------------------------------- |
| [models.py](./models.py)                                   | Django model entrypoint and specialist exports        |
| [resource_models.py](./resource_models.py)                 | Common resource identity and relationships            |
| [specialist_models.py](./specialist_models.py)             | Compute/network specialists                           |
| [data_application_models.py](./data_application_models.py) | Database, application and repository specialists      |
| [web_domain_models.py](./web_domain_models.py)             | Website, Domain, DNS and TLS specialists              |
| [operational_models.py](./operational_models.py)           | Containers, storage, backups and scheduled operations |
| [policies.py](./policies.py)                               | Resource permissions and scope                        |
| [ninja/](./ninja/)                                         | Resource, specialist, technology and topology APIs    |
| [tests/](./tests/)                                         | Domain regression, API and permission-boundary tests  |
| [migrations/](./migrations/)                               | Ordered database history                              |
| [admin.py](./admin.py)                                     | Django admin registration                             |
| [apps.py](./apps.py)                                       | Django app configuration                              |

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
read projections. Historical migrations are retained; migration 0010 removes
the obsolete flat inventory tables and identity bridges.

## Expiry and metadata discovery

[metadata_refresh.py](./metadata_refresh.py) discovers public Domain registration
and TLS metadata; [tasks.py](./tasks.py) schedules locked background refreshes.
Resource details show refresh status. Automatic expiry checks use the existing
Monitoring app. See the
[operating guide](../../../docs/INFRASTRUCTURE_EXPIRY_TRACKING.md).

[summary.py](./summary.py) builds capability- and Client-scoped overview counts,
using the same native resources as every category register.

## Creation workflows

Every resource type is available through the permission-filtered Resources
chooser. Provider Accounts and Service Providers have dedicated entry points;
server networking and tags can be created in resource workspaces. See the
[creation guide](../../../docs/INFRASTRUCTURE_CREATION.md) for all locations.

[ninja/catalogue_views.py](./ninja/catalogue_views.py) manages vendors and provider
accounts. General inventory writes live beside collection/detail reads in
[ninja/resource_views.py](./ninja/resource_views.py); they cannot replace typed
specialist creation. [ninja/tag_views.py](./ninja/tag_views.py) manages shared tags
and scoped resource assignments.

Service Provider and tag catalogue updates, nested link updates and the unified
resource edit entry points are documented in
[`INFRASTRUCTURE_CREATION.md`](../../../docs/INFRASTRUCTURE_CREATION.md#editing-records).

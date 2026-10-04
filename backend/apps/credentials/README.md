# Encrypted Credential Vault

Client/Internal credential metadata and encrypted secret payloads. Metadata access and secret reveal/copy/download are separate permissioned capabilities.

## Code map

| Location                       | Responsibility                                       |
| ------------------------------ | ---------------------------------------------------- |
| [models.py](./models.py)       | Credential metadata, lifecycle and resource links    |
| [secrets.py](./secrets.py)     | Encrypted payload storage and key handling           |
| [templates.py](./templates.py) | Typed credential fields and templates                |
| [policies.py](./policies.py)   | Credential action authorisation                      |
| [health.py](./health.py)       | Expiry and rotation health                           |
| [ninja/](./ninja/)             | Metadata, explicit secret actions and lifecycle APIs |
| [tests/](./tests/)             | Domain regression, API and permission-boundary tests |
| [migrations/](./migrations/)   | Ordered database history                             |
| [admin.py](./admin.py)         | Django admin registration                            |
| [apps.py](./apps.py)           | Django app configuration                             |

## Tests and related code

From the repository root, run `tools/test-backend apps.credentials.tests`.
For a single module, use `tools/test-backend apps.credentials.tests.test_<topic>`.

API routers are assembled in
[adbsoftwaresolutions/ninja/routers.py](../../adbsoftwaresolutions/ninja/routers.py).
Internal browser workflows live in
[the combined Software Solutions application](../../../sites/adb-software-solutions/README.md).

Read the [backend guide](../../README.md) for shared conventions and the
[canonical documentation map](../../../docs/README.md) before domain changes.

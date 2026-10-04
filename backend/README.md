# Shared Django backend

Django owns business data, authentication, permissions and operational rules for
all three Brands. Django Ninja provides APIs; PostgreSQL stores records and
Redis/Celery support caching, sessions and background work.

## Navigation

| Location                                                | Responsibility                                        |
| ------------------------------------------------------- | ----------------------------------------------------- |
| [apps/](apps/README.md)                                 | Business domains and app-specific code maps           |
| [authentication/](authentication/README.md)             | Identity, sessions, TOTP and passkeys                 |
| [adbsoftwaresolutions/](adbsoftwaresolutions/README.md) | Settings, root URLs, API routing and Celery bootstrap |
| [requirements/](requirements/README.md)                 | Dependency sources and generated locks                |
| [manage.py](./manage.py)                                | Django management entrypoint                          |

## App conventions

Each domain keeps its models, services/policies, Ninja endpoints, migrations and
`tests/` together. `ninja/` contains HTTP contracts and adapters; reusable business
rules belong in domain services. Some mature apps use focused modules instead of
a single `services.py`; their README identifies the entrypoints.

Tests use importable `tests/` packages with `test_*.py` modules. Do not reintroduce
an adjacent `tests.py`, which conflicts with the package. Authentication already
keeps tests beside its auth-service, passkey and two-factor subdomains.

## Verification

Run these from the repository root in the configured development environment:

```bash
tools/test-backend
tools/test-backend apps.clients.tests
tools/test-backend apps.ticketing.tests.test_ingestion
tools/test-backend adbsoftwaresolutions.tests
tools/lint
```

The test wrapper selects `adbsoftwaresolutions.settings_test` and accepts Django
test labels/options. It uses the configured database and service environment;
keep `DEBUG` numeric (`0` or `1`). Stage intended new files before `tools/lint`
because its file discovery uses Git.

Read the [canonical platform docs](../docs/README.md) before architectural or
security changes. Public contact forms feed shared Lead/Ticket ingestion, and
Client/Internal scope is enforced in Django rather than browser components.

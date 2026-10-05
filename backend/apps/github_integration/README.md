# GitHub integration

GitHub App installations connect organisation/personal accounts to the internal
GitHub dashboard. Repository projections attach to the native infrastructure
SourceRepository; application repository links reuse those inventory records.

See [the setup and architecture guide](../../../docs/GITHUB_APP_SETUP.md) for
configuration, permissions, subscriptions, ownership and operational limits.

- `models.py`, `migrations/`: installations, repository links, work projections,
  durable webhook routing, personal filter preferences and action audits.
- `client.py`: JWT signing from the Infisical-injected `GITHUB_APP_PRIVATE_KEY` and REST transport.
- `services.py`: repository imports and safe issue/PR/workflow/run projections.
- `webhooks.py`, `tasks.py`: signed events, background updates and recovery.
- `ninja/views.py`: scoped dashboard APIs and workflow/log controls.
- `tests/`: scope, permissions, signatures, deduplication and sync regressions.

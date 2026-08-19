# Django Architecture & App Structure

> **Historical document — superseded.**
>
> This root-level architecture file predates the implemented multi-brand platform and labels existing applications/models as future work. It is retained only as a redirect for historical links.
>
> Do not use it as current implementation guidance.

Use the canonical documentation instead:

- `docs/PLATFORM_MASTER_PLAN.md` — current repository/application architecture and domain plan;
- `docs/CURRENT_STATE_AND_FOUNDATION_CHECKLIST.md` — implemented state and remaining operational work;
- `docs/DOMAIN_MODEL_AUDIT.md` — current Django domain-model decisions;
- `docs/PERMISSIONS_AND_ACCESS_MODEL.md` — permission/scope architecture;
- `docs/TICKETING_ARCHITECTURE.md` — implemented ticketing/communications architecture;
- `docs/MICROSOFT_GRAPH_TICKETING_SETUP.md` — Microsoft 365/Graph deployment runbook.

Current backend rules include:

- one shared Django backend for all ADB Brands;
- Django Ninja as the API layer;
- Django as the authentication, permission and business-rule authority;
- explicit Brand and Client/Internal ownership concepts;
- operational domains for Clients, CRM, Projects, Tasks, Time, Ticketing, Knowledge Base, Credentials and Infrastructure;
- Celery/Redis for asynchronous orchestration;
- encrypted credential secret services for sensitive integration/operational secrets;
- Microsoft Graph Shared Mailbox ingestion and replies as part of Ticketing.

Refer to the live Django apps and the canonical documents above for model details rather than this historical file.

# ADB Business Platform documentation

This directory contains the canonical architecture, implementation-state and
operational runbook documentation for the ADB Business Platform.

The platform is the shared internal operating system for the ADB businesses,
not merely the backend for three marketing websites. The documentation should
allow a developer or coding agent to understand the current product direction
without reconstructing decisions from chat history.

## Canonical precedence

When documents disagree, use this order unless a newer explicit architectural
decision says otherwise:

1. `PLATFORM_MASTER_PLAN.md` — product vision, architectural rules, UX doctrine
   and ordered build plan.
2. `PERMISSIONS_AND_ACCESS_MODEL.md` — capability, scope and sensitive-action
   authorisation rules.
3. `DOMAIN_MODEL_AUDIT.md` — current domain/model decisions and migration
   boundaries.
4. `CURRENT_STATE_AND_FOUNDATION_CHECKLIST.md` — what is implemented, what is
   next and what remains.
5. Domain architecture/runbooks such as `CREDENTIAL_VAULT_ARCHITECTURE.md`,
   `INFRASTRUCTURE_ARCHITECTURE.md`, `TICKETING_ARCHITECTURE.md` and
   `MICROSOFT_GRAPH_TICKETING_SETUP.md`.
6. `HISTORICAL_PLANNING.md` and the older root-level plans for historical
   context only.

## Product rules that cut across every domain

- **Current/actionable work is the default.** Active Clients, open Leads,
  actionable Tickets, current Projects, active Credentials and current
  Infrastructure should be the normal view. History remains available through
  explicit Inactive, Archived, Won, Lost, Resolved, Closed, Completed, Retired
  or All views.
- **Workspaces and drawers beat CRUD tables.** Registers are for finding and
  triaging records. Normal clicks should preserve context through right-side
  drawers or focused workspaces while full deep-link pages remain available.
- **Client is the main operational context.** Contacts, Tickets, Projects,
  Tasks, Time, Infrastructure, Credentials, Knowledge and later commercial
  history should converge on the Client workspace.
- **Internal work is first-class.** Never create a fake ADB Client simply to
  represent internal Projects, Tasks, Time, Credentials, Infrastructure or
  Knowledge.
- **Django is authoritative.** Permissions, scope, business rules, timer state,
  recurrence, relationship validity and sensitive actions are enforced in the
  backend.
- **Server-side operational queries are the norm.** Data-heavy screens use
  server-side filtering, sorting, pagination, counts and statistics rather
  than loading everything into the browser.
- **User preferences that should follow the user are server-backed.** Existing
  Ticket Queue defaults follow this rule; the configurable Dashboard will too.
- **Tailwind CSS is the frontend styling standard.** The internal operations
  console remains dark-only and information-dense; public Brand sites remain
  independent visual products.

## Documentation map

- `PLATFORM_MASTER_PLAN.md` — complete build plan and product architecture.
- `CURRENT_STATE_AND_FOUNDATION_CHECKLIST.md` — implementation snapshot and
  next work.
- `DOMAIN_MODEL_AUDIT.md` — domain/model decisions.
- `PERMISSIONS_AND_ACCESS_MODEL.md` — staff capability and object scope.
- `CREDENTIAL_VAULT_ARCHITECTURE.md` — encrypted Credential storage, typed
  templates, secret-action permissions, auditing, resource links, browser
  handling, key rotation and legacy-secret reconciliation.
- `INFRASTRUCTURE_ARCHITECTURE.md` — structured technical-resource graph,
  native specialists, Credentials, Knowledge and Monitoring direction.
- `INFRASTRUCTURE_EXPIRY_TRACKING.md` — Domain/TLS discovery, renewal detection,
  automatic expiry checks and Celery operating guidance.
- [INFRASTRUCTURE_CREATION.md](./INFRASTRUCTURE_CREATION.md) — resource/vendor
  creation and nested creation locations.
- `TICKETING_ARCHITECTURE.md` — unified communications and operational Ticket
  workflow.
- `MICROSOFT_GRAPH_TICKETING_SETUP.md` — Microsoft 365 Shared Mailbox app-only
  deployment runbook and Vault-backed certificate handling.
- `UNIFIED_OPERATIONAL_SEARCH_ARCHITECTURE.md` — Stage 9 permission-aware global
  and Client-context search, Ticket-message discovery and Credential secret
  boundaries.
- `UNIFIED_OPERATIONAL_POLISH_ARCHITECTURE.md` — complete Stage 9 integration:
  scoped Activity/audit UX, notifications, Credential lifecycle health, Ticket
  SLAs, resource topology, Calendar Events and navigation/security boundaries.
- `AUTH_FRONTEND_NEXTJS_MIGRATION.md` — completed authentication frontend
  migration record and guardrails.
- `DEVELOPMENT_DATA.md` — deterministic local development data.
- `HISTORICAL_PLANNING.md` — superseded assumptions and historical documents.

Credential security is defined by `CREDENTIAL_VAULT_ARCHITECTURE.md`. Other
technical domains must reference Credentials rather than introducing duplicate
plaintext password, token, certificate, private-key or sensitive-note fields.

## Updating these documents

Architectural changes should update the relevant canonical document in the
same PR as the implementation whenever possible. The current-state checklist
must distinguish clearly between:

- implemented capability;
- agreed next work;
- later/deferred work whose detailed design is intentionally unresolved.

Do not turn a long-term possibility into a present architectural requirement,
and do not let domain docs drift away from the implementation state on the
branch that will introduce them.

- [Shared live updates](LIVE_UPDATES_ARCHITECTURE.md) — SSE topics, scope checks, recovery and deployment.

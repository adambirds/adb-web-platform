# Current State and Operational Roadmap

## Purpose

This document is the implementation companion to `PLATFORM_MASTER_PLAN.md`.
It records what is implemented by the platform at this point in the build and
what remains in the agreed sequence.

Snapshot for this refresh:

- date: **2026-08-28**;
- implementation state: **Stages 1–9 implemented on the Stage 9 integration
  branch**;
- next sustained stage after merge: **Stage 10 — Commercial and analytics**.

Credential-specific security and operational rules are defined in
`CREDENTIAL_VAULT_ARCHITECTURE.md`. Stage 9 cross-domain behavior is defined in
`UNIFIED_OPERATIONAL_SEARCH_ARCHITECTURE.md` and
`UNIFIED_OPERATIONAL_POLISH_ARCHITECTURE.md`.

## 1. Repository/application foundation

### Implemented

- [x] One shared Django backend is the business-data/auth/scope authority.
- [x] Django Ninja is the API layer.
- [x] PostgreSQL/Redis/Celery foundations are established. Local development uses
      separate `redis-cache`, `redis-session` and `redis-celery` services, configured
      through `.devcontainer/.env`; Celery defaults to the `general` queue.
- [x] ADB Software Solutions, ADB Web Designs and ADB Technology are
      first-class Brands.
- [x] ADB Software Solutions public + `/admin` routes share one Next.js app.
- [x] Authentication/account security is a separate Next.js application.
- [x] Django session/TOTP/WebAuthn/passkey flows remain authoritative.
- [x] Tailwind CSS is the frontend styling standard.
- [x] The operations workspace is dark-only and workflow-oriented.
- [x] Brand-aware CMS/public content isolation exists.
- [x] Append-only AuditEvent infrastructure exists with explicit Client/resource
      context where relevant.
- [x] Deterministic development seeding and repository CI/devcontainer tooling
      exist.

## 2. Platform-wide operational UX rules

### Implemented direction

- [x] Active/current/actionable records are the default in operational domains.
- [x] History is retained behind explicit filters/views rather than deleted.
- [x] Shared right-side Task/Record drawer patterns preserve list/workspace
      context.
- [x] Full-page deep links remain available for refresh/bookmark/complex work.
- [x] Data-heavy operational pages use server-side pagination/filtering/sorting
      and statistics where implemented.
- [x] Client/Internal ownership is a first-class platform rule.
- [x] Django capability + scope remains authoritative regardless of frontend
      visibility.
- [x] Cross-device preferences such as Ticket Queue defaults and Dashboard
      layout are server-backed.

### Continue applying

- [ ] Keep commercial records and later portal/admin surfaces current-first
      where lifecycle/history makes that meaningful.
- [ ] Keep new cross-domain features as projections over authoritative domain
      services rather than parallel sources of truth.

## 3. Clients and Contacts

### Implemented

- [x] Client create/edit lifecycle management.
- [x] Active/Inactive/Archived Client lifecycle and Active-first global view.
- [x] Client statistics, filtering and server-side pagination.
- [x] Client records can open in a right-side record drawer.
- [x] ClientContact create/edit/deactivate and Primary/Billing/Technical roles.
- [x] Contact workspaces expose Contact-specific Tickets.
- [x] Client/Contact email identity participates in Ticket sender resolution.
- [x] Client Command Centre provides coherent Overview/Contacts/Projects/Tasks/
      Tickets/Time/Infrastructure/Credentials/Knowledge/Activity navigation.
- [x] Client Command Centre is current-first, permission-aware and provides
      selected-period Time summaries and contextual create/deep-link actions.
- [x] Client Activity can use explicit scoped AuditEvent context rather than
      relying on unsafe metadata inference.

### Later

- [ ] Add commercial history during Stage 10 without turning the Client
      workspace into an unstructured catch-all page.

## 4. CRM / Leads

### Implemented

- [x] Lead create/edit/detail/workspace.
- [x] Lead ownership/assignment and explicit open/won/lost outcomes.
- [x] Starter sales-stage/source catalogues, permission-controlled inline option
      creation, and immediate lead-list refresh after drawer mutations.
- [x] My active/open Leads default with Unassigned/All Active alternatives.
- [x] Won/Lost/All Leads history views.
- [x] Server-side Lead statistics, filtering and pagination.
- [x] Lead records can open/edit in a right-side drawer.
- [x] Website contact submissions create Leads and canonical Tickets.
- [x] Matching inbound/outbound Ticket communication appears on Leads.
- [x] Lead email sends through configured Microsoft 365 Shared Mailboxes and
      the Ticket/Graph layer.
- [x] Lead -> Client + primary Contact conversion retains communication history.

### Remaining/refinement

- [ ] Stronger manual contact matching/deduplication where sender matching is
      insufficient.
- [ ] Commercial value/follow-up metadata belongs in Stage 10 rather than a
      duplicate CRM-side commercial model.

## 5. Projects

### Implemented

- [x] Client/Internal Project ownership and lifecycle.
- [x] Current global Project views default to Planning/Active/Paused.
- [x] Completed/Archived/All are explicit history views.
- [x] Work-first Project workspace with Work, Timeline, Overview and Time.
- [x] Project List/Board surfaces with contextual Task creation and ordering.
- [x] Dependency-aware Project Timeline with Day/Week/Month zoom.
- [x] Dated Subtasks and dependency connector/blocked state.
- [x] Project Time ledger with tracked/billable/non-billable totals.
- [x] Project context can be reused by first-class Calendar Events.

### Remaining/refinement

- [ ] Project participants/ownership only if real collaboration workflows need
      more than current assignment/context.
- [ ] Richer commercial context arrives in Stage 10.

## 6. Tasks / ADB work management

### Implemented

- [x] Tasks may be standalone Internal, Client-owned or Project-owned.
- [x] My Tasks default plus Today, Upcoming, Overdue, Completed and All Tasks.
- [x] Server-authoritative counts for focus views.
- [x] Quick capture with ownership context and due-date shortcuts.
- [x] Shared Task drawer and direct-edit Task workspace.
- [x] Task Lists/Sections with List/Board/Timeline workspaces and ordering.
- [x] Subtasks, blocking dependencies and cycle detection.
- [x] Daily/weekly/monthly recurrence with next-occurrence materialisation.
- [x] Task comments/discussion and completion/reopen controls.
- [x] Embedded live timer and Task time history.
- [x] Assigned overdue Tasks participate in scoped operational notifications.

### Remaining/refinement

- [ ] Agree long-term delete/archive semantics if completion/history proves
      insufficient.
- [ ] Explicit Ticket-linked Tasks only after the workflow is intentionally
      designed.

## 7. Calendar / planning

### Implemented

- [x] Permission-aware Calendar API/workspace.
- [x] Dated Task and Project work appears on the Calendar.
- [x] First-class `CalendarEvent` model for Events, Meetings, Milestones and
      Reminders.
- [x] Calendar Events support Internal/Client ownership and optional Project
      context.
- [x] Timed/all-day ranges, status, location, meeting URL and attendee email
      metadata are supported.
- [x] Event create/update/delete actions are backend-authorised and scoped.
- [x] Upcoming Events can participate in operational notifications.

### Remaining/refinement

- [ ] External calendar integration only after explicit provider, ownership and
      conflict-resolution design.
- [ ] Add richer day/week planning only if real usage justifies the additional
      UI complexity.

## 8. Time Tracking

### Implemented

- [x] Manual Time Entries.
- [x] Client/Internal ownership with Internal time forced non-billable.
- [x] Project/Task/Ticket attribution and valid direct Client context.
- [x] Persistent server-side RunningTimer with one active timer per staff user.
- [x] Backend-calculated Start/Stop/Cancel lifecycle.
- [x] Task and Ticket live timers.
- [x] Contextual Time panels/history on Task/Ticket/Project surfaces.
- [x] Browse-oriented Client/Project/Internal Time Tracking workspace.
- [x] Useful period filters and scoped tracked/billable/non-billable summaries.
- [x] Client Command Centre period Time summaries.

### Remaining/refinement

- [ ] Edit/delete Time Entries with clear permission/audit policy.
- [ ] Richer staff breakdown/reporting where useful.
- [ ] Stage 10 invoice/commercial linkage without making invoicing a dependency
      of operational Time Tracking.

## 9. Ticketing and communications

### Implemented

- [x] TicketQueue, Ticket, TicketMessage, TicketNote and TicketAttachment.
- [x] Client + Ticket Queue capability/scope enforcement.
- [x] My Tickets default plus Unassigned, All Active, Queue and history views.
- [x] Server-backed per-user default Ticket Queues.
- [x] Ticket records can open in a shared right-side drawer.
- [x] Internal Notes merge chronologically into the conversation feed.
- [x] Graph connection/Shared Mailbox configuration and verification.
- [x] Certificate/client-secret app-only Graph support.
- [x] Persisted delta sync/cursors and worker locking.
- [x] Inbound normalisation/thread matching/idempotency.
- [x] Outbound replies/new Lead email through Graph/Celery.
- [x] Website contact forms feed canonical Ticket ingestion.
- [x] Deterministic routing/classification and Vendor/service sender routing.
- [x] Attachment quarantine/policy and optional ClamAV scanning.
- [x] Ticket Queue first-response/resolution SLA targets.
- [x] Recorded Ticket deadlines with healthy/warning/breached/waiting-customer
      health.
- [x] Service Levels workspace with attention filters and authorised Queue policy
      editing.
- [x] Assigned SLA warnings/breaches participate in scoped notifications.

### Remaining/refinement

- [ ] Harden the rare ambiguous-send case where Graph accepts mail but the
      worker loses the provider response before local persistence.
- [ ] Richer Task/KB/Infrastructure links only where normal workflows benefit.

## 10. Microsoft 365 deployment model

### Established architecture

- [x] One tenant/app-level MicrosoftGraphConnection can serve many Shared
      Mailboxes.
- [x] Production prefers certificate-based app-only authentication.
- [x] Exchange Online RBAC for Applications is the Microsoft-side mailbox
      boundary.
- [x] Enabled database Mailbox rows are the narrower operational allow-list.
- [x] Licensed user mailboxes are not intended Ticket sources.
- [x] Graph private-key/certificate material can use the encrypted Credential
      Vault rather than duplicate plaintext fields.
- [x] Preferred ADB Exchange management scope dynamically includes Shared
      Mailboxes so new Shared Mailboxes do not need a new RBAC assignment.

See `MICROSOFT_GRAPH_TICKETING_SETUP.md` and
`CREDENTIAL_VAULT_ARCHITECTURE.md`.

## 11. Infrastructure

### Implemented

- [x] `InfrastructureResource` common identity and Client/Internal ownership.
- [x] Lifecycle/environment/criticality/current-first filtering and resource
      tags.
- [x] Service Providers and resource-backed Provider Accounts.
- [x] Typed `ResourceRelationship` topology with ownership validation.
- [x] Permission-aware global/Client resource collections and details.
- [x] Creation entry points for all 29 resource types, Service Providers,
      server interfaces/IP addresses and resource tags.
- [x] Resource-only Infrastructure identity, native category registers and removal
      of obsolete inventory models/reconciliation.
- [x] Structured resource drawer/full-page workspaces.
- [x] Relationship management and Client-context Infrastructure workspace.
- [x] Resource workspaces surface linked active Credentials.
- [x] Native compute/network, Database, Application/Environment and Source
      Repository specialists.
- [x] Native Website/Endpoint, Domain/DNS and TLS Certificate specialists.
- [x] Daily Domain RDAP and verified TLS metadata discovery, renewal detection,
      automatic expiry monitoring and visible refresh errors. See
      `INFRASTRUCTURE_EXPIRY_TRACKING.md`.
- [x] Docker/Kubernetes, storage/backups, system services and scheduled-job
      specialist technical operations.
- [x] Bounded permission-aware resource topology traversal/workspace.

## 12. Credential Vault

### Implemented

- [x] StoredCredential Client/Internal ownership.
- [x] Typed credential templates for common secret types.
- [x] Encrypted, versioned secret payload service and MultiFernet key ring.
- [x] Active/Inactive/Archived lifecycle and Active-first views.
- [x] Searchable non-secret metadata only.
- [x] Permission-aware secure CRUD and separate reveal/copy/download actions.
- [x] Ordinary APIs expose metadata/field presence, never secret values.
- [x] Safe browser handling for explicit reveal without persistent browser
      storage/routes/normal caches.
- [x] Infrastructure links with Client-boundary validation.
- [x] Atomic legacy plaintext -> encrypted payload reconciliation.
- [x] Encryption fails closed when key-ring configuration is invalid.
- [x] Optional per-Credential rotation intervals.
- [x] Metadata-only Credential expiry/rotation health workspace.
- [x] Scoped expiry/rotation operational reminders.

### Later Vault work

- [ ] Remove reconciled legacy plaintext columns when production migration is
      verified.
- [ ] Bulk encryption-key rotation tooling/reporting.
- [ ] Richer template administration only if actually needed.
- [ ] Step-up/break-glass behavior only if a future threat model justifies it.

## 13. Knowledge Base

### Implemented

- [x] Client/Internal ownership.
- [x] Independent folder trees per Client and Internal, with mandatory context
      selection before folder/article browsing or creation.
- [x] File-browser folder navigation with list/grid contents, breadcrumbs,
      folder deep links and current-folder creation.
- [x] Document read/workspace experience and Markdown editing.
- [x] Immutable versions with author/editor context.
- [x] Protected attachments.
- [x] Tags/search metadata and permission-aware search foundations.
- [x] Infrastructure and Credential metadata links without secret duplication.
- [x] Client/resource contextual navigation.
- [x] Future portal visibility remains explicit and private by default.

## 14. Monitoring

### Implemented

- [x] Monitor checks attached to structured resources.
- [x] ICMP, TCP, HTTP/HTTPS, content, TLS, DNS and domain-expiry checks.
- [x] Schedules/timeouts/failure/recovery thresholds/severity.
- [x] Historical results and failure->recovery incidents.
- [x] Celery Beat/worker execution through reusable services.
- [x] Current-first global, Client and resource technical-health views.
- [x] Active incidents participate in scoped operational notifications.

### Deliberate boundary

- [ ] Authenticated Monitoring remains deferred until explicit authentication
      schemes are modelled; Credential type is not used to guess wire auth.

## 15. Users & Access

### Implemented

- [x] Django Groups/Permissions plus StaffAccessProfile capability/scope model.
- [x] Active-first staff list/detail and invitation lifecycle.
- [x] Group bundles plus additive direct business capabilities.
- [x] Client and Ticket Queue scope administration.
- [x] Server-backed default Ticket Queue preferences.
- [x] Effective capability/source display including sensitive capabilities.
- [x] Audited activation/deactivation and access changes.
- [x] Self/superuser safeguards and rejection of unsafe framework Groups.
- [x] Routine staff administration without requiring Django superuser access.

## 16. Dashboard / My Work

### Implemented

- [x] Configurable code-owned widget catalogue.
- [x] Per-user server-persisted layout/configuration.
- [x] Configurable ordering and 4/6/8/12-column widths.
- [x] My Tasks, My Tickets, Time, Leads, Projects, Technical Health, Agenda and
      personal Recent Activity widgets.
- [x] Live capabilities and normal domain scopes are reapplied on every load.
- [x] Saved widgets disappear from the effective layout immediately after
      permission loss.
- [x] No browser-persisted Dashboard layout and no Credential secret projection.

## 17. Search, Activity, notifications and SLA polish

### Implemented in Stage 9

- [x] Unified permission-aware global search.
- [x] Client-context search across mature operational domains.
- [x] Ticket message-text discovery without returning message bodies in search
      projections.
- [x] Metadata-only Credential search; decrypted/legacy/encrypted secret values
      are never indexed or returned.
- [x] Search input uses CSRF-aware POST body rather than URL query strings.
- [x] Explicit Client/resource AuditEvent context.
- [x] Permission-aware operational Activity workspace.
- [x] Sensitive audit request metadata hidden without explicit capability.
- [x] Audit acknowledgement appends history rather than mutating original
      events.
- [x] Bounded Infrastructure topology/navigation polish.
- [x] Server-backed per-user operational notifications.
- [x] Notifications cover overdue assigned Tasks, assigned Ticket SLA health,
      Credential health, Monitoring incidents and upcoming Calendar Events.
- [x] Credential expiry/rotation health and reminders.
- [x] Ticket SLA/escalation refinement with Queue policy editing.
- [x] First-class Calendar Event/Meeting/Milestone/Reminder behavior.

PostgreSQL/database-backed bounded search remains appropriate initially; do not
add dedicated search infrastructure without demonstrated need.

## 18. Commercial and analytics layer

### Stage 10 — agreed future scope, not implemented yet

- [ ] Products/services catalogue.
- [ ] Recurring services.
- [ ] Quotes/proposals.
- [ ] Contracts.
- [ ] Invoices/billing.
- [ ] Stripe/payment tracking.
- [ ] Profitability reporting.
- [ ] Client lifetime value.
- [ ] Time-versus-pay/revenue analysis.
- [ ] Lead-source conversion and revenue attribution.

Detailed signing/accounting/tax/retainer/forecasting models are not yet agreed
and should not be invented during unrelated implementation work.

## 19. Public websites

### Foundation implemented

- [x] Brand-aware CMS/public API isolation.
- [x] Contact-form Brand/source ingestion into Lead + Ticket pipeline.
- [x] Separate public Next.js applications exist.

### Public build phase now active

- [x] Confirm freelance positioning, Manchester location, form-only contact,
      related but distinct designs and dark-default public theme switching.
- [x] Inspect/organise the supplied assets into the ignored `website-assets/`
      library and inventory the old Web Designs sitemap URLs.
- [x] Confirm selective retention/rewrite of local service-area pages and honest
      Australia/USA remote-service pages, plus image generation for branded social
      imagery where useful.
- [x] Complete each Brand's public experience using the existing Brand-scoped
      CMS and Lead/Ticket contracts, including SEO and verified migration redirects.

The user has explicitly prioritised public websites before commercial features.
See [the website brief](PUBLIC_WEBSITES_PLAN.md) for the current decisions and
implementation details. Policy/trading copy and migrated CMS drafts still require
owner review before production launch; see `PUBLIC_WEBSITES_MORNING_REVIEW.md`.

Security/fix/integration work may still happen opportunistically.

## 20. Client portal

### Deferred to Stage 12

- [ ] Design explicit portal identity link to ClientContact.
- [ ] Design per-domain portal visibility.
- [ ] Expose only deliberately Client-visible Tickets/Projects/Documents/etc.
- [ ] Never expose Internal resources, Credential secrets, Ticket Notes or
      staff-only audit/security data implicitly.

## 21. Current ordered implementation sequence

1. **Core typed Infrastructure — implemented.**
2. **Web Infrastructure — implemented.**
3. **Monitoring + technical dashboards — implemented.**
4. **Knowledge Base redesign + resource links/search foundations — implemented.**
5. **Specialist technical operations — implemented.**
6. **Client Command Centre integration — implemented.**
7. **Users & Access — implemented.**
8. **Dashboard / My Work — implemented.**
9. **Unified operational polish — implemented.**
10. **Commercial + analytics layer — next.**
11. **Public websites as primary focus.**
12. **Client portal.**

Small dependency-driven slices may move, but major order changes should update
`PLATFORM_MASTER_PLAN.md` and this checklist.

## 22. Internal-platform readiness gate

The operational platform now satisfies the agreed pre-commercial readiness gate
for Stages 1–9:

- [x] Clients/Contacts managed through the custom UI.
- [x] Leads and tracked communication usable day to day.
- [x] Projects/Tasks/Time usable as ADB's work-management system.
- [x] Ticketing/Graph mail usable as the communication system.
- [x] Infrastructure/Credentials/Knowledge usable as the technical
      documentation system.
- [x] Monitoring surfaces current technical health.
- [x] Client Command Centre exposes major operational context.
- [x] Users & Access is safe and usable.
- [x] Dashboard/My Work is materially useful.
- [x] Cross-domain search/navigation/activity/notifications are coherent and
      permission-aware.
- [x] CI/security/dependency health remains part of the merge gate.

The next sustained implementation phase is Stage 10 commercial and analytics.
The public websites remain Stage 11 and the Client portal follows only after
internal/commercial visibility rules are mature.

### Infrastructure editing completeness

Service Provider metadata/status and shared tag metadata are editable with their
separate view/change capabilities and audit events. All 29 native resource types
use the standard Edit resource action in full pages and drawers. Server
interfaces/IPs, repository links and TLS domain coverage can be edited in place;
outgoing resource relationships retain editable notes and scoped targets.
See `INFRASTRUCTURE_CREATION.md` for entry points and API boundaries.

## GitHub and inventory navigation

Implemented category pages for all 29 creatable infrastructure resource types,
including Networks, Subnets and Source repositories. Application repository UI
distinguishes inventory records from application links.

Implemented a multi-installation GitHub App dashboard, signed durable webhooks,
Celery updates, my-work/Dependabot filters, workflow dispatch, failed-job reruns
and scoped log retrieval. Live account sync requires App registration, Infisical
`GITHUB_APP_PRIVATE_KEY` injection, subscriptions and installation approval; these external
setup steps remain deployment work. See `GITHUB_APP_SETUP.md`.

## Shared operational live updates

The admin workspace shares an authenticated, scoped SSE connection for GitHub,
monitoring, notifications and operational screens. Redis publishes after-commit
invalidation hints; existing Django APIs remain authoritative. See
[the live updates architecture](LIVE_UPDATES_ARCHITECTURE.md) for coverage, recovery
and ASGI/proxy deployment requirements.

## Configuration and deployment reference

The [root setup guide](../README.md#setup-and-configuration) is the consolidated
operator reference for all runtime/build variables, GitHub/Graph provisioning
and production services. Account verification/reset/invitation email uses the shared Infisical Graph
connection and the environment-configured `DEFAULT_FROM_EMAIL` Shared Mailbox. SSE shares default
cache Redis; the production worker defaults to `general`.

## Microsoft Graph configuration authority

The platform Graph connection now uses Infisical-injected environment values for
tenant/client IDs, certificate, private key and optional passphrase. None of
those values are copied into application records or the credential Vault.
An `environment_certificate` connection stores only routing identity/status;
it is discovered automatically from runtime configuration, without a bootstrap
command. Runtime token acquisition
reads environment values directly. Existing certificate/client-secret Vault
connections remain supported, but new platform setup uses Infisical. Graph secrets
must be scoped to backend/worker runtime identities, never frontend build contexts.

## Native Celery operations

Implemented `/admin/celery` for active staff superusers: worker/queue inspection,
automatic safe execution history, server-side filtering/pagination, hourly
completion charts, configured Beat schedules and audited dispatch/cooperative
revoke controls. Shared SSE updates task and worker views. The separate monitoring
image, OAuth variables, scripts and forwarded port have been removed. Deploy the
core migration and restart API/workers/Beat to begin tracking. See
[Celery operations](CELERY_DASHBOARD.md).

## Per-task Celery diagnostics

The full-administrator Celery dashboard now includes a per-task log viewer.
`CeleryTaskLog` stores redacted messages/severity/logger/attempt/timestamp linked
to an execution. Workers capture task-context Python logging, redirected stdout/
stderr, lifecycle and failure tracebacks without local-variable dumps. Known
secrets and credential-shaped fields are scrubbed before persistence; task
argument/result dumps and SQL logs are excluded. Capture is bounded (2,000 rows
per execution, 8,000 characters per message) and retained for 14 days. The API
rechecks active staff superuser access; SSE transports only refresh hints. Existing
execution summary fields remain metadata-only. See
[Celery operations](CELERY_DASHBOARD.md) for scope and capture limits.

### Manual enquiry retention review

Implemented: 36-month Lost/unconverted Lead review queue at `/admin/retention`,
daily scan, permissioned approval, reasoned keep decisions and attachment cleanup
retry. Automatic deletion is disabled by design. Deployment requires migration
`crm.0006_lead_retention_reviews`, existing workers/Beat and permission grants.
See [Lead retention](LEAD_RETENTION.md).

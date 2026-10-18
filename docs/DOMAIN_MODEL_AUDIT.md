# Domain Model Audit

## Purpose

This document records the current domain-model decisions for the ADB Business
Platform. It replaces the older foundation-phase audit that described several
now-implemented domains as future amendments.

The classifications used here are:

- **Keep** — current concept and ownership are suitable.
- **Keep / extend** — current model is established; add capability in focused
  slices without redesigning its identity.
- **Transitional** — retained safely while a newer structured model becomes the
  operational identity.
- **Defer** — valid future domain, but detailed modelling is intentionally not
  agreed yet.

Credential-specific field storage, encryption, permissions and migration rules
are defined in `CREDENTIAL_VAULT_ARCHITECTURE.md`.

Do not treat this audit as permission to implement every future field at once.

## 1. Cross-domain modelling rules

### Client/Internal ownership — Keep

Operational records that may belong to customers or ADB use explicit
Client/Internal ownership semantics:

```text
client-owned -> a real Client
internal     -> ADB itself, no Client
```

Do not create a fake ADB/Internal Client.

Null Client alone must not silently imply Internal where the domain requires an
explicit ownership type/validation.

### Brand — Keep

`apps.core.Brand` is the public/commercial communication identity for:

- ADB Software Solutions;
- ADB Web Designs;
- ADB Technology.

Brand is independent from operational ownership and Client access scope.

### AuditEvent — Keep / extend

Append-only audit records remain the foundation for security-sensitive and
materially privileged actions.

Audit metadata must be curated. Never put passwords, tokens, private keys,
secret payloads, message bodies or other sensitive material into audit
metadata merely because an action touched them.

Credential reveal/copy/download events record safe field names/context only.

## 2. Authentication and staff identity

### User — Keep

Keep the custom UUID/email-based Django User and `PermissionsMixin` identity
model.

Django remains the identity/session authority for staff and later Client portal
users.

Do not add a second identity system to Next.js. Portal relationships should be
designed through ClientContact later rather than adding ad-hoc customer fields
to User now.

### Django Group / CustomGroup — Keep

Django Group remains the capability-role bundle. A custom proxy/convenience
layer does not imply a parallel role engine.

### Passkey / TOTP / recovery / session models — Keep

These are established authentication/security domains. Continue hardening and
regression testing rather than replacing them.

## 3. Access control

### StaffAccessProfile — Keep / extend carefully

StaffAccessProfile is the staff object-scope/preferences anchor.

Established concerns include:

- all Clients versus selected Clients;
- all Ticket Queues versus selected Ticket Queues;
- server-backed default Ticket Queue preferences.

An empty stored default-queue selection means all accessible enabled queues;
an explicit subset narrows the user's normal Ticket work views.

Do not turn StaffAccessProfile into a generic dumping ground for every user
setting. Future Dashboard configuration may use its own appropriate model.

### ClientAccessGrant — Keep

Selected Client scope for staff who do not have `all_clients`.

Client scope applies transitively to Client-owned operational domains through
reusable policy/services.

### TicketQueueAccessGrant — Keep

Selected Ticket Queue scope for staff who do not have `all_ticket_queues`.

Queue scope remains independent from Client scope.

## 4. Clients and Contacts

### Client — Keep / extend

Client is the account/organisation and the primary operational context.

Established behaviour includes:

- Active/Inactive/Archived lifecycle;
- custom operations CRUD;
- active-first global overview;
- server-side stats/filtering/pagination;
- scoped Client workspace;
- contextual active Client-owned Credentials.

Future commercial fields should be added by the commercial phase rather than
pre-loading Client with invoice/accounting concepts now.

### ClientContact — Keep / extend

ClientContact is the person/email identity inside a Client.

Established behaviour includes:

- active/inactive lifecycle;
- primary, billing and technical flags;
- Contact workspace;
- Ticket/message context;
- email matching for inbound communication.

Future portal identities should link to ClientContact.

## 5. CRM

### LeadSource — Keep

Configurable lead-source taxonomy remains useful for current CRM and later
source-conversion/revenue analytics.

Prefer stable machine-readable identity where automation/reporting requires it.

### LeadStatus — Keep

LeadStatus remains configurable pipeline state with explicit outcome semantics:

- `open`;
- `won`;
- `lost`.

Do not infer outcome solely from display-name text in new code.

### Lead — Keep / extend

Lead remains the sales lifecycle record, not a support Ticket.

Established behaviour includes:

- Brand/source;
- owner/assignee;
- operational focus views;
- communication history through Tickets;
- outbound Lead email through the Ticket/Graph layer;
- transactional conversion to Client + primary Contact while retaining
  communication history.

Future commercial value/follow-up/source-revenue fields should be introduced
when the commercial/analytics contracts are designed.

## 6. Projects and work management

### Project — Keep / extend

Project is the operational delivery/work record and supports:

- Client-owned Projects;
- Internal Projects;
- lifecycle/current-history views;
- dates and current commercial-estimate metadata;
- Task/Task List/Time integration;
- work-first List/Board/Timeline/Overview/Time workspaces.

Operational Project is separate from public CaseStudy/Portfolio.

Future Project milestones/participants should be added only where the current
Task/date/assignment model does not meet the workflow.

### TaskList — Keep

Task Lists are optional organisational/workflow containers and may be
Client/Internal/Project scoped according to their established ownership
validation.

A Task does not need a Task List.

### Task Section/workflow column — Keep

Ordered Sections are first-class List/Board workflow columns. Preserve
server-authoritative ordering/ownership checks.

### Task — Keep / extend

Task is now a mature work-management model, not a skeleton.

Established requirements include:

- standalone Internal Task valid;
- Client Task valid;
- Project Task valid;
- Task List optional;
- single assignee model as implemented;
- priority/status/start/due dates;
- completion/reopen;
- recurrence;
- creator/audit context;
- ownership/project/list consistency validation.

A future Ticket relationship must be introduced with an actual workflow rather
than simply adding a nullable FK because one might be useful.

### Subtask relationship — Keep

Subtasks inherit and validate the surrounding work context. Preserve this
rather than allowing child Tasks to cross Client/Internal/Project boundaries.

### TaskDependency — Keep

Explicit blocking dependencies are established. Preserve cycle detection and
ownership/work-context validation.

### TaskComment — Keep

TaskComment is human discussion attached to a Task.

Audit metadata around comment actions must not copy comment bodies into
AuditEvent metadata.

## 7. Time Tracking

### TimeEntry — Keep / extend

TimeEntry supports manual and timer-recorded work across:

- Internal;
- direct Client;
- Project;
- Task;
- Ticket contexts.

Internal time is non-billable by rule. Context relationships must remain
consistent with ownership.

Future invoice linkage should be additive; invoicing is not a prerequisite for
recording Time.

### RunningTimer — Keep

RunningTimer is the backend-authoritative active timer state.

Keep the one-active-timer-per-user constraint unless a future explicit product
decision changes it. Browser tabs are not authoritative timer state.

## 8. Ticketing and communications

### MicrosoftGraphConnection — Keep

Represents one Microsoft tenant/application integration.

Authentication belongs at connection level, not per Mailbox. Sensitive
certificate/private-key/client-secret material belongs in the Credential Vault,
not duplicate plaintext Graph settings.

See `CREDENTIAL_VAULT_ARCHITECTURE.md` and
`MICROSOFT_GRAPH_TICKETING_SETUP.md`.

### Mailbox — Keep / extend

Represents one configured operational Shared Mailbox.

It carries Brand/purpose/default Queue and Graph sync state. Enabled database
Mailbox rows are the application-level operational allow-list.

Do not model each Shared Mailbox as a separate Entra application/certificate.

### TicketQueue — Keep

Operational routing and staff-scope unit.

Queue defaults/preferences are staff configuration, not a property of the
TicketQueue itself.

### Vendor / VendorSenderRule — Keep

Database-backed operational sender policy. These records classify/route
service/vendor mail without treating it as spam or requiring a code deploy.

### Ticket — Keep / extend

Ticket is the canonical communication thread.

It may carry Brand, Queue, Client, Contact, Vendor, classification, assignment,
priority/status and lifecycle timestamps.

The default operational experience is current/actionable-first; resolved/closed
history remains available.

Future links to Tasks/Projects/KB/Infrastructure should be introduced through
focused workflows when useful.

### TicketMessage — Keep

One inbound/outbound message. Provider/internet Message-ID/reference metadata
remains important for idempotency and threading.

### TicketNote — Keep

Internal staff-only conversation item. The UI renders Notes chronologically
within the Ticket feed rather than as a cramped side-panel silo.

### TicketAttachment — Keep

Governed/quarantined attachment metadata. Malware policy and authorised
download are separate from the Ticket message model.

## 9. Credentials

### CredentialType — Keep / typed template catalogue

Credential type/template metadata is the stable field-schema catalogue for the
Vault.

Built-in templates cover username/password, SSH, database, API token, OAuth,
service account, certificate/keypair, licence key, recovery codes, encryption
key and custom secret use cases.

Each field has a stable key, presentation kind, required state and storage
class. Safe metadata is separated from encrypted secret material.

See `CREDENTIAL_VAULT_ARCHITECTURE.md`.

### StoredCredential — Keep

`StoredCredential` is the Credential identity and now has a complete encrypted
Vault workflow.

Established behaviour includes:

- Client/Internal ownership;
- Active/Inactive/Archived lifecycle;
- safe searchable metadata;
- expiry/rotation metadata;
- versioned `encrypted_secret_payload`;
- ordered MultiFernet key ring through `CREDENTIAL_ENCRYPTION_KEYS`;
- typed secure create/edit/archive;
- separate reveal/copy/download actions;
- resource links;
- atomic legacy plaintext reconciliation;
- safe audit events that never contain secret values;
- fail-closed encryption/decryption behaviour.

Legacy plaintext columns remain temporarily for compatibility/migration only.
New Vault operations do not write sensitive values to them.

The long-term cleanup is to remove reconciled legacy plaintext columns only
after production migration is verified.

### CredentialResourceLink — Keep

Credentials link to one or more InfrastructureResource records with purpose and
primary semantics.

Client-owned Credentials may link only to resources owned by the same Client.
Internal Credentials may legitimately link to Internal or Client resources
where ADB operates shared provider/service access.

Link-target choices are permission-scoped before ownership validation.

### Secret browser state — Keep ephemeral

Revealed secret values are not part of the ordinary Credential model returned
by list/detail APIs. Frontend secret values may exist only in transient
component state for an explicit secret action and must not be stored in browser
storage, routes, analytics or normal caches.

## 10. Infrastructure

### InfrastructureResource — Keep

This is the common identity for structured technical resources.

It owns cross-cutting:

- Client/Internal ownership;
- name/type;
- lifecycle;
- environment;
- criticality;
- tags;
- creator/updater/archive timestamps;
- safe future portal-visibility metadata.

It does not replace specialist relational models with EAV/JSON.

### ServiceProvider — Keep

Provider identity belongs in data rather than hard-coded provider choice lists.
The vendor catalogue has a permissioned creation UI/API and is also available
inline while creating Provider Accounts.

### ProviderAccount — Keep

Represents a real provider account/tenant/project and is itself backed by an
InfrastructureResource so Credentials, KB, Monitoring and relationships can
attach consistently.

Secrets do not belong directly on ProviderAccount. They link through the Vault.
Accounts have resource-backed create/edit/archive APIs and dedicated browser
entry points, with capability and Client scope enforced in Django.

### ResourceRelationship — Keep

Cross-resource topology for directed relationships such as depends-on,
hosted-on, managed-by, uses, routes-to and related-to.

Preserve:

- self-link prevention;
- duplicate prevention;
- Client-boundary validation;
- permission-aware target selection.

Strong specialist foreign keys remain preferable for known technical
semantics; generic edges complement them rather than replace them.

### Flat inventory models and identity bridges — Remove

The system has no historical infrastructure inventory. `InfrastructureResource`
and its native specialist profiles are authoritative. Remove the obsolete flat
models, identity bridges, reconciliation/promotion services and APIs rather than
maintaining duplicate stores. Preserve historical migrations and append a removal
migration. Native resources, ownership, relationships and Vault links remain.

### Native typed specialist models/relationships — Keep / extend progressively

Implemented structured families now include:

- `ServerProfile`, Network, Subnet, Network Interface and IP Address;
- `DatabaseInstance` and `LogicalDatabase`;
- `ApplicationProfile` and `ApplicationEnvironment`;
- `SourceRepository` plus typed `ApplicationRepositoryLink` role/path context;
- `WebsiteProfile` and concrete `WebsiteEndpoint` URLs;
- `DomainProfile`, `DNSZone` and structured `DNSRecord`;
- `TLSCertificate` plus typed `TLSCertificateDomain` coverage.

These models remain resource-backed where they need cross-cutting identity and enforce Client/Internal boundaries. DNS Records are deliberately nested under a DNS Zone rather than each becoming a generic resource. Specialist authentication/private-key material references Vault Credentials rather than introducing password/token/private-key fields.

Future structured families still include:

- Docker/Kubernetes;
- storage/backups;
- system services/scheduled jobs;
- licences/subscriptions/email systems and other useful operations records.

Implement these progressively rather than redesigning every technical model in one migration.

## 11. Knowledge Base

### KnowledgeBaseSection / folder structure — Keep scoped hierarchy

Sections already have explicit Client/Internal ownership and enforce identical
ownership for parent/child folders and contained documents. Each Client and
Internal has an independent tree; identical folder names across owners are valid.
The workspace requires selecting one owner before returning folders or articles.
Folder/article creation inherits that owner and cannot silently fall back to
Internal. The UI browses immediate child folders/articles in one file browser
with breadcrumbs; subtree search keeps the same ownership boundary. Reusable
templates may be considered later without sharing live trees.

### KnowledgeBaseDocument — Keep / redesign workspace

Document remains the central KB content identity.

Future mature behaviour includes:

- Client/Internal ownership;
- Markdown/controlled rich-text content;
- author/editor context;
- tags/search metadata;
- attachments;
- Infrastructure/Ticket/Project/Credential links;
- explicit future portal visibility, private by default.

Knowledge content may link to a Credential but must not copy its decrypted
secret into the document.

### DocumentVersion — Keep / strengthen service ownership

Versions should be immutable history generated by document update services.
Arbitrary clients should not be trusted to manufacture version history
independently.

## 12. Monitoring — Defer detailed schema to the Monitoring slice

Monitoring is agreed as a separate cross-cutting subsystem attached to
InfrastructureResource.

The target includes Check, historical Result and Incident concepts rather than
adding `is_up` fields to infrastructure specialists.

Checks requiring authentication reference Vault Credentials; they do not own
plaintext passwords/tokens.

Detailed schedule/result-retention/escalation models should be decided in the
Monitoring implementation slice.

## 13. CMS/public content

### Portfolio / CaseStudy — Keep concept, reframe naming when worthwhile

Public case-study content is separate from operational Project.

A future rename is acceptable when its migration/API/UI value justifies the
cost; do not merge the models.

### Testimonial / BlogPost / taxonomy / FAQ — Keep

Brand-aware editorial content remains valid. Public APIs must continue to scope
content/taxonomy by Brand and never leak cross-Brand content accidentally.

Public content APIs never receive Credential secrets merely because they share
the Django backend.

## 14. Future commercial domains — Defer detailed models

Agreed future product areas include:

- Product/Service catalogue;
- recurring services;
- Quote/Proposal;
- Contract;
- Invoice/Billing;
- Stripe/Payment tracking;
- profitability/LTV/source analytics.

The exact signing, accounting, tax, forecasting, retainer and SLA schemas are
not agreed. Do not create speculative tables in advance of the commercial
phase.

Reuse existing Client/Lead/Project/Ticket/Time identity when that phase begins.
Commercial integration secrets belong in the Credential Vault.

## 15. Future Client portal — Defer

Portal identity should use the existing authentication subsystem and link to
ClientContact.

Per-domain portal visibility must be explicit and private by default. Do not add
implicit portal access merely because a record belongs to a Client.

Credential secret actions are staff-only unless a later explicit portal threat
model says otherwise.

## 16. Migration discipline

- Never delete/rewrite historical migrations that have been applied.
- Append new migrations.
- Infrastructure uses mandatory resource-backed specialist identity. The
  obsolete flat inventory is removed through an appended migration.
- Do not remove credential legacy plaintext columns until Vault reconciliation
  and production verification are complete.
- New secret-bearing fields belong in the encrypted Vault rather than new
  plaintext columns.
- Prefer reversible, explicit migrations where practical.

## 17. Current model priorities

The model work now follows the product roadmap:

1. mature typed Infrastructure specialists;
2. add Monitoring models/services;
3. redesign the KB hierarchy/editor/linking model;
4. complete Users & Access administration contracts;
5. add cross-domain Activity/Search models only where concrete requirements
   justify persistence;
6. add Credential health/rotation-support models only when real operations
   require them;
7. add commercial models only in the commercial phase;
8. add portal visibility/identity only in the portal phase.

### Infrastructure editing completeness

Service Provider metadata/status and shared tag metadata are editable with their
separate view/change capabilities and audit events. All 29 native resource types
use the standard Edit resource action in full pages and drawers. Server
interfaces/IPs, repository links and TLS domain coverage can be edited in place;
outgoing resource relationships retain editable notes and scoped targets.
See `INFRASTRUCTURE_CREATION.md` for entry points and API boundaries.

## GitHub integration additions

Keep native SourceRepository as the inventory authority. GitHub Repository is
a one-to-one integration attachment, not a second repository inventory. Keep
ApplicationRepositoryLink for application role/path metadata. GitHub Installation
defines the remote account and Client/Internal import context; Item stores safe
issue/PR/workflow/run projections. Delivery stores only durable event routing
metadata. Preference is a personal username filter, and WorkflowAction records
actor/action identifiers without secrets, workflow input values or log content.
App signing material lives only in Infisical-injected `GITHUB_APP_PRIVATE_KEY`
process configuration; no Vault credential reference or database key field is
required. Operators rotate it manually in Infisical and redeploy backend processes.
See `GITHUB_APP_SETUP.md` for ownership and synchronisation limits.

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

## CeleryTaskExecution — Keep safe operational metadata

CeleryTaskExecution is a platform-wide task-history projection, not a business
job identity or replacement scheduler. Store only task ID/name, state, queue,
worker, retries, timestamps, duration, exception class and revoke-request time.
Never retain task args/kwargs, results, tracebacks or exception text. Lifecycle
signals populate it automatically. Daily retention purges completed metadata
older than 14 days while preserving unfinished executions. Restrict all access
to active staff superusers. See [Celery operations](CELERY_DASHBOARD.md).

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

### Public editorial publishing and media (6 October 2026)

Keep public Portfolio separate from operational Project. Amend Portfolio,
Testimonial and FAQ with explicit publication state, defaulting to unpublished;
existing records require a publication review. Portfolio carries editable search
copy and service slugs; FAQs carry service slugs to join code-owned service pages.
Image alternative text is stored with editorial images. BlogPost retains its
existing publication fields and respects a future publication timestamp. No
marketing pages or operational models are moved into the CMS.

### Lead retention review (October 2026)

Keep Lead history for repeat enquiries; review Lost, unconverted records after
36 months without activity. `LeadRetentionReview` stores eligibility dates,
manual decisions, next review dates and retryable attachment cleanup keys. Its
nullable Lead link permits a non-personal decision record to survive approval.
Do not apply this policy automatically to Clients or unrelated Tickets. See
[Lead retention](LEAD_RETENTION.md).

### Offline WordPress draft migration (15 October 2026)

No new content models are required. A versioned JSON export retains public source
HTML/IDs/taxonomies/authors and original media bytes. The offline importer creates
BlogPost and Portfolio drafts scoped only to the matching Brand, preserves
existing records/publication and validates files before writes. Portfolio body
copy occupies `solution`; missing project claims are not invented. Original
marketing pages are archived for reference and remain code-owned. Existing
cross-Brand taxonomy collisions must stop import rather than extend visibility.
See [the archive guide](migrations/README.md) for the runbook and tests.

### Analytics workspace models — Keep / extend

Business and BusinessMembership define analytics-only scope and role selection,
separate from Brand and Client. Role capability bundles remain Django Groups,
applied by the existing EmailBackend only within verified Business membership.
GoogleConnection references the shared encrypted StoredCredential. ProviderProperty
links a Website to one GA4 or GSC property; ReportSnapshot stores exact aggregate
windows, SyncJob stores durable progress, EventDefinition stores provider config
metadata and AnalyticsPreference stores per-user selection. No raw visitor/event
store or second user/identity system is introduced. See [Analytics platform](ANALYTICS_PLATFORM.md).

### Analytics Google connection health — Amend

`GoogleConnection` retains encrypted tokens exclusively in `StoredCredential`.
Add only non-secret refresh metadata: last refresh time, consecutive failures and
next permitted attempt. The connection row serializes refresh, reauthorisation
and disconnection; no new identity, token database or scheduler is introduced.
See [Analytics operations](ANALYTICS_PLATFORM.md#settings-and-unattended-google-access).

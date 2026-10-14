# ADB Business Platform Master Plan

## Purpose

This is the canonical product, architecture and build-plan document for the
ADB Business Platform.

The platform is the shared internal operating system for the ADB businesses.
It is intended to replace or substantially reduce reliance on separate CRM,
helpdesk, task-management, time-tracking, technical-documentation,
credential-management, infrastructure-inventory and lightweight commercial
systems.

It takes useful product ideas from HubSpot, Asana, Jira/AutoTask/ServiceNow,
IT Glue and modern helpdesk products, but it must follow ADB's actual workflows
rather than reproduce another product feature-for-feature.

Older plans remain useful historical context, but this document wins when they
conflict with the current architecture.

---

## 1. Product vision

ADB operates three public Brands that share one operational platform:

1. **ADB Software Solutions** — bespoke software, SaaS/application delivery,
   APIs/integrations, automation, mobile applications and AI-built project/code
   reviews. A broader bounded software
   consultancy offer remains under review.
2. **ADB Web Designs** — web design/development with Next.js, WordPress, Shopify
   and Squarespace; ecommerce; hacked/malware site recovery; hosting, maintenance,
   technical SEO and local SEO.
3. **ADB Technology** — cloud/DevOps and infrastructure, migrations, deployment
   pipelines, server management, server rebuilds and app deployment/security
   hardening; no core-hours technical
   support commitment.

The Brands have separate public positioning and visual experiences. They do
not have separate business-data backends.

The internal platform should eventually cover:

- Clients and Contacts;
- CRM/Leads and sales communication;
- Tickets, email and other communication sources;
- Projects, Tasks and work planning;
- Time Tracking;
- Infrastructure and technical-resource relationships;
- encrypted Credentials;
- Knowledge Base/runbooks;
- Monitoring and operational health;
- Calendar and notifications;
- staff Users & Access;
- configurable Dashboard/My Work;
- audit/activity and cross-domain search;
- Brand-scoped CMS/public integrations;
- later products/services, quotes/proposals, contracts, recurring services,
  invoicing, Stripe/payment tracking and commercial analytics;
- later Client portal workflows.

The platform must be useful to ADB first. A future VastDesk/SaaS-style
productisation of reusable platform ideas is a **possibility**, not a current
requirement. Do not introduce premature generic multi-tenancy or abstraction
solely for that possibility.

---

## 2. Product and UX doctrine

### 2.1 Current/actionable-first

The default view of an operational domain should answer: **what needs attention
now?**

History remains available, but it must not dominate normal work.

Examples already established by the product:

- Clients default to **Active**; Inactive/Archived are explicit history views.
- Contacts inside a Client default to active contacts.
- Leads default to **My active/open Leads** with Unassigned and All Active
  alternatives; Won/Lost are history.
- Tickets default to **My actionable Tickets**; Unassigned, All Active and
  Queue views are explicit; Resolved/Closed are history; Waiting on Customer
  is intentionally quieter than work waiting on ADB.
- Projects default to Planning/Active/Paused; Completed/Archived are history.
- Tasks default to **My Tasks**, with Today, Upcoming, Overdue and Completed
  focus views; All Tasks is explicit.
- Infrastructure defaults to current resources; Retired/Archived are history.
- Credentials default to Active; Inactive/Archived are history.

This rule should be applied to new operational domains unless there is a good
reason not to.

### 2.2 Workspaces and drawers, not CRUD as the product

Large CRUD tables are not the primary user experience.

Registers exist for searching, filtering, sorting, pagination and triage.
Normal record interaction should preserve context through:

- focused domain workspaces;
- right-side record drawers;
- contextual panels inside Client/Project/Ticket/Infrastructure workspaces;
- full-page deep links for refresh/bookmark/share and complex work.

The existing shared Task/Record drawer patterns should be reused where they
fit rather than creating unrelated modal behaviour per domain.

### 2.3 Server-authoritative operational UX

For data-heavy screens, the backend should own:

- scope;
- filters;
- sorting;
- pagination;
- counts/statistics;
- business-state transitions.

User preferences that should follow a staff user between browsers/devices
belong server-side. Ticket default queues and Dashboard layout/configuration
both follow this rule.

### 2.4 Dark internal console, independent public Brands

The internal operations workspace is intentionally dark-only,
information-dense and workflow-focused. Tailwind CSS is the frontend styling
standard.

Public Brand applications share an identifiable ADB design family while retaining
distinct page compositions, imagery and messaging. Their public pages default to
dark mode and offer a header light/dark switch; internal operations stay dark-only.
Shared packages contain genuinely shared primitives/contracts/tooling. See
[the confirmed website brief](PUBLIC_WEBSITES_PLAN.md).

---

## 3. Repository and application architecture

The monorepo contains:

```text
backend/
packages/
sites/
    adb-software-solutions/
    adb-web-designs/
    adb-technology/
    auth-adb-software-solutions/
```

There is no separate `admin-adb-software-solutions` application.

### 3.1 Shared Django backend

`backend/` is the single business-data and operations backend. It owns:

- authentication and authorisation;
- staff users, capabilities and scopes;
- Brands;
- Clients/Contacts;
- CRM/Leads;
- Projects/Tasks/Time;
- Tickets/communications;
- Microsoft Graph connections and Shared Mailboxes;
- Knowledge Base;
- Credentials;
- Infrastructure and Monitoring;
- CMS/editorial content;
- audit/activity;
- Celery/background processing;
- future commercial and portal data.

Django remains authoritative for permissions, scope and business rules. The
API layer is Django Ninja.

### 3.2 ADB Software Solutions frontend

`sites/adb-software-solutions/` is one Next.js App Router application serving:

- the ADB Software Solutions public site; and
- authenticated internal operations under `/admin`.

Route/layout boundaries must keep the public and privileged concerns clearly
separated even though they share one deployment.

### 3.3 Other public frontends

`sites/adb-web-designs/` and `sites/adb-technology/` are separate Next.js
public applications.

Main marketing pages are code-owned. CMS-managed public content is limited to
editorial content that benefits from ongoing administration, such as Blog,
Testimonials, FAQs and optional public Case Studies/Portfolio.

Operational `Project` and public CaseStudy/Portfolio remain separate concepts.

### 3.4 Authentication/account frontend

`sites/auth-adb-software-solutions/` is the dedicated Next.js authentication
and account-security application.

Django remains the identity/session/TOTP/WebAuthn authority. Do not introduce
Auth.js/NextAuth, browser-stored JWTs or another identity authority by default.

---

## 4. Core domain rules

### 4.1 Brand is first-class and separate from ownership

Brand identifies the ADB business context for public content, communication
and commercial presentation. It is not a substitute for Client/Internal
ownership.

Example:

```text
Ticket
brand = ADB Web Designs
client = Welcome to Travel
```

### 4.2 Operational ownership is Client or Internal

Operational records deliberately belong to either:

```text
client-owned -> a real Client
internal     -> ADB itself, with no Client
```

Never create a fake ADB Client to represent internal work.

### 4.3 Client is the command-centre context

Client is not merely a company row. The implemented Client Command Centre is
organised around:

```text
Client
├── Overview
├── Contacts
├── Projects
├── Tasks
├── Tickets / communications
├── Time
├── Infrastructure
├── Credentials
├── Knowledge Base
├── Activity / history
└── later commercial + portal context
```

Completed/resolved/history records can remain useful in the Client context,
but current information should still be the initial view inside each section.

### 4.4 Contacts bridge people, Clients and communication

ClientContact email identity is a primary key for communication matching.
Contact workspaces should surface Contact-specific Tickets. Future Client
portal identities should link to ClientContact rather than introduce a second
customer-person model.

### 4.5 Permissions are capability + scope

Django Groups/Permissions answer **what** a staff user can do. Access-control
scope answers **where** they can do it.

Scopes include Clients and Ticket Queues and transitively constrain
Client-owned Projects, Tasks, Time, Infrastructure, Credentials, Knowledge and
other domains.

Sensitive actions such as credential reveal/copy/download or access changes
use explicit permissions and audit events.

---

## 5. Implemented operational foundation

The following are established platform architecture, not future-only ideas:

- Django-backed identity/session/TOTP/WebAuthn and dedicated auth frontend;
- Brand-aware CMS/public content isolation;
- capability permissions plus Client/Ticket Queue scope;
- append-only AuditEvent foundation with scoped Client/resource context;
- combined ADB Software Solutions public + `/admin` Next.js application;
- Client/Contact CRUD and lifecycle management;
- Client Command Centre with permission-aware section navigation, current-first
  cross-domain summaries, contextual actions, period Time totals and safe
  Activity metadata;
- Lead CRUD, assignment, outcome semantics and Lead -> Client/Contact
  conversion retaining communication history;
- Project CRUD with Client/Internal ownership and current/history views;
- Asana-style Tasks, Lists, Sections, Boards, Timelines, Subtasks,
  Dependencies, recurrence and comments;
- My Tasks/Today/Upcoming/Overdue/Completed focus views and quick capture;
- shared Task drawer and direct-edit Task workspace;
- server-authoritative RunningTimer and manual Time Entries;
- Task and Ticket live timers plus Project/Task/Ticket time context;
- Time Tracking drill-down by Client/Project/Internal and period rather than a
  giant global history table;
- a permission-scoped Calendar covering dated Tasks, Projects and first-class
  Events/Meetings/Milestones/Reminders;
- unified Ticketing with Messages, Notes, Attachments, queues and operational
  focus views;
- Microsoft Graph app-only Shared Mailbox sync and outbound delivery;
- Lead email through the Ticket/Graph layer rather than `mailto:`;
- per-user Ticket Queue defaults stored server-side;
- structured InfrastructureResource identity, Providers, tags and typed
  resource relationships;
- resource-only Infrastructure workspaces and typed specialist profiles;
- full typed Credential Vault with encrypted/versioned secrets, independent
  reveal/copy/download permissions, Client/Infrastructure context and atomic
  legacy-secret reconciliation;
- structured Monitoring checks/results/incidents with global, Client and
  resource-context technical-health views;
- Client/Internal Knowledge Base with hierarchical sections, Markdown editing,
  immutable versions, protected attachments and Infrastructure/Vault links;
- specialist technical operations for storage/backups, containers, Kubernetes,
  system services and scheduled jobs;
- custom Users & Access administration with Groups, direct business capabilities,
  Client/Ticket Queue scope, effective-access visibility, invitations and audited
  activation/access changes;
- configurable server-persisted Dashboard/My Work with permission-aware widgets,
  scoped current-work projections and personal audit activity;
- permission-aware global and Client-context operational search;
- bounded Infrastructure topology, richer Client/resource Activity and dedicated
  audit/security UX;
- scoped operational notifications, Credential expiry/rotation health and
  reminders, Ticket SLA/escalation health and Queue policy editing;
- deterministic development data and CI/container foundations.

The internal operational platform is implemented through Stage 9 unified
operational polish. The next sustained implementation stage is Stage 10 —
Commercial and analytics.

Credential-specific security and lifecycle rules are authoritative in
`CREDENTIAL_VAULT_ARCHITECTURE.md`.

---

## 6. Work management: Projects, Tasks, Calendar and Time

The Projects/Tasks/Time area is an integrated work-management system, not
separate registers.

### Projects

Opening a Project should be work-first. The established workspace separates:

- Work;
- Timeline;
- Overview;
- Time.

List/Board views support contextual creation and ordering. The Project Timeline
is dependency-aware and supports Day/Week/Month zoom for dated work.

Current Projects are the global default; Completed/Archived remain available
as history.

### Tasks

Tasks do not require Projects. Valid Task contexts include:

- standalone Internal work;
- Client work;
- Project work;
- later explicit Ticket-linked work where useful.

The normal experience includes My Tasks, quick capture, direct editing,
subtasks, blocking dependencies, recurrence, comments, List/Board/Timeline
views, completion controls and the embedded live timer.

### Calendar

The permission-aware Calendar is a unified planning surface for dated Tasks,
Projects and first-class `CalendarEvent` records. Events support Internal or
Client ownership, optional Project context, event/meeting/milestone/reminder
types, scheduled/completed/cancelled state, timed or all-day ranges, locations,
meeting URLs and attendee email metadata.

Calendar write actions remain Django-authorised and Client/Project scope is
validated in the backend. Upcoming Events can participate in operational
notifications. External calendar synchronisation remains deferred until an
explicit provider and conflict/ownership design is agreed.

### Time

Time is cross-domain. Timer lifecycle is backend-authoritative with one active
timer per user unless explicitly changed later.

The Time Tracking workspace should remain browse-oriented by:

- Client;
- Project;
- Internal;
- selected period.

Do not regress to one giant undifferentiated history table.

Future commercial work may link billable time to invoices without making
invoicing a dependency of current Time Tracking.

---

## 7. CRM and Client operations

### Clients

Global Client views are current-first and default to Active. Inactive/Archived
Clients are explicit history.

The **Client Command Centre** is the coherent Client-local operations workspace.
Authorised staff can move between Contacts, Projects, Tasks, Tickets, Time,
Infrastructure, Credentials, Knowledge and Activity without repeatedly returning
to global registers.

Its server-authoritative projection provides permission-aware current-work counts,
open communication, selected-period Time summaries and scoped recent Activity. The
frontend provides current/history section behaviour and contextual create/deep-link
actions while reusing the mature domain workspaces instead of duplicating them.

Active Client-owned Credential metadata is integrated through the existing Vault
capability; secret values remain behind the Vault's separate reveal/copy/download
boundaries. See `CLIENT_COMMAND_CENTRE_ARCHITECTURE.md` for the Stage 6 contract
and `UNIFIED_OPERATIONAL_POLISH_ARCHITECTURE.md` for the Stage 9 activity/search
extension.

### Leads

Lead operations are sales-pipeline focused:

- My Leads is the primary view;
- Unassigned and All Active are operational alternatives;
- Won/Lost are explicit history/outcomes, with direct workspace actions;
- conversion to Client marks the Lead Won atomically;
- editing can occur in the record drawer;
- communication is retained through Tickets;
- sending email from a Lead creates/continues an auditable Ticket conversation
  through the selected configured Shared Mailbox and Graph delivery path;
- conversion to Client/primary Contact preserves related Ticket history.

Future CRM work can add useful commercial metadata/deduplication, but should
not recreate a separate communication system.

---

## 8. Ticketing and Microsoft 365

Ticket is the canonical communication thread for:

- Microsoft 365 email;
- public website contact submissions;
- future portal communication;
- future API/integration sources where appropriate.

The main Ticket page is an operational work queue, not a global archive.
Established views include:

- My Tickets;
- Unassigned;
- All Active;
- enabled Queue views;
- Resolved;
- Closed;
- All Tickets.

Waiting on Customer is intentionally lower priority than work waiting on ADB.
Internal Notes appear chronologically in the conversation feed and remain
visually/staff-only distinct.

Per-user default Ticket Queues are server-backed. An empty stored selection
means all accessible enabled queues; an explicit subset narrows default work
views.

Queue-owned first-response and resolution SLA targets are supported. Ticket
SLA deadlines are recorded explicitly, current health is evaluated as healthy,
warning, breached or waiting-on-customer, and authorised Queue administrators
can edit the targets from the Service Levels workspace. Waiting on Customer
suppresses escalation without rewriting recorded deadlines.

### Microsoft Graph model

The normal ADB deployment is:

- one Microsoft Entra application;
- one tenant-level `MicrosoftGraphConnection`;
- certificate-based app-only authentication in production;
- many configured Microsoft 365 Shared Mailboxes;
- Exchange Online RBAC for Applications as the Microsoft-side boundary;
- enabled database Mailbox rows as the narrower operational allow-list;
- certificate/private-key material stored through the Credential Vault rather
  than duplicate plaintext Graph configuration.

For ADB's current tenant model, the preferred Exchange scope is dynamic by
`RecipientTypeDetails -eq 'SharedMailbox'`. This means a new Shared Mailbox
automatically falls inside the Exchange application boundary without creating
another RBAC rule. Licensed `UserMailbox` recipients remain outside it.

Adding a mailbox to the Ticket system should therefore be an application
configuration action: choose/enter the Shared Mailbox, Brand/purpose/default
queue, verify it and enable it. The operator should not re-enter the tenant ID,
client ID, certificate or create a new RBAC assignment for each mailbox.

See `TICKETING_ARCHITECTURE.md`, `MICROSOFT_GRAPH_TICKETING_SETUP.md` and
`CREDENTIAL_VAULT_ARCHITECTURE.md` for details.

---

## 9. Technical operations: Infrastructure, Credentials, Monitoring and KB

The technical-operations goal is IT Glue-style structured documentation for
software development, web delivery, DevOps, Linux/system administration and
support.

It is not a collection of flat asset tables.

### 9.1 Structured Infrastructure

`InfrastructureResource` is the common identity/ownership/lifecycle anchor.
Strongly typed specialist models retain domain-specific fields.

Generic `ResourceRelationship` edges provide cross-resource topology without
replacing normal relational modelling or requiring a graph database.

The merged foundation includes:

- Client/Internal resource ownership;
- lifecycle/environment/criticality;
- tags;
- Service Providers and resource-backed Provider Accounts;
- typed relationships;
- current-first resource views;
- one authoritative resource identity across all Infrastructure pages;
- Client-scoped/global structured resource workspaces;
- contextual links to active Credentials;
- native compute/network specialists;
- native Database Instance/Logical Database specialists;
- native Application/Application Environment specialists;
- native Source Repository specialists and typed Application/Repository links;
- native Website/Website Endpoint, Domain/DNS Zone/DNS Record and TLS Certificate specialists;
- nested Website endpoint, DNS record and TLS Domain-coverage operations in the shared resource workspace;
- safe resource-centric create/edit/archive workflows;
- a permission-filtered creation chooser for every resource type, dedicated
  Provider Account/vendor creation and nested server-network/tag controls;
- bounded permission-aware topology traversal over visible resource relationships.

Monitoring, Knowledge Base, specialist technical operations and topology extend
the same shared resource identity and are integrated into the Client Command
Centre. The operational implementation sequence is complete through Stage 9;
Stage 10 commercial/analytics is next.

### 9.2 Credential Vault

The Credential Vault is an implemented technical-operations subsystem, not a
future placeholder. Its authoritative architecture is
`CREDENTIAL_VAULT_ARCHITECTURE.md`.

It provides:

- typed credential templates;
- Client/Internal ownership;
- encrypted versioned secret payloads and key ring/rotation;
- metadata-only ordinary API responses;
- Active-first lifecycle;
- separate reveal, copy and download permissions/actions;
- audit events that record field/context but never secret values;
- links to one or more Infrastructure Resources with ownership validation;
- Client and Infrastructure contextual views;
- atomic reconciliation of legacy plaintext fields into encrypted payloads;
- fail-closed behaviour when encryption configuration is unavailable;
- metadata-only expiry and configurable rotation-interval health;
- scoped expiry/rotation reminders without indexing or projecting secret values.

Secret values must never enter normal search, logs, URLs, analytics, notification
text or audit metadata.

Infrastructure, Monitoring, Graph, KB and later specialist records reference
Credentials instead of duplicating secret material.

### 9.3 Monitoring

Monitoring is an implemented cross-cutting subsystem attached to structured
resources, not an `is_up` flag on Server/Website.

The current check types include:

- ICMP/ping;
- TCP port;
- HTTP/HTTPS;
- expected/forbidden text;
- TLS validity/expiry;
- DNS record checks;
- domain registration expiry.

Checks produce result history and incidents with failure/recovery semantics.
Celery Beat/workers schedule execution through reusable services. Global,
Client-scoped and resource-context technical-health views surface current
problems first. Active incidents can also participate in the scoped operational
notification layer.

Authenticated monitoring remains deliberately deferred until explicit
authentication schemes are modelled. A Credential type alone must not be used
to guess Basic/Bearer or another wire-authentication contract.

### 9.4 Knowledge Base

The Knowledge Base is an implemented Client/Internal documentation workspace
with a filesystem-like folder/section structure rather than a flat list.
Operators first open a Client or Internal Knowledge Base. Each owner has an
independent folder tree; folder/article lists and create forms never combine
Clients or default silently to Internal. The workspace is a single file browser
with list/grid views, inline folders and articles, breadcrumbs and Up one level.
Folder URLs preserve navigation, and creation uses the current folder.

Implemented behaviour includes:

- Markdown editing;
- immutable/versioned history;
- author/editor metadata;
- protected attachments;
- tags/search metadata and server-side search foundations;
- links to Infrastructure Resources and Credential metadata;
- resource and Client-context documentation projections;
- future portal visibility explicit and private by default.

The KB is not an alternative plaintext credential store. It links to Vault
records when a runbook needs access context and does not duplicate secret
payloads.

---

## 10. Users & Access

Users & Access is an implemented first-class custom operations area over the
existing Django Groups/Permissions and `StaffAccessProfile` scope model.

Implemented behaviour includes:

- active-first staff list/detail with search and pagination;
- staff invitation through the existing one-hour password-setup token flow;
- safe invitation resend while an account still has an unusable password;
- activate/deactivate lifecycle without deleting access history;
- Django Group membership as reusable capability bundles;
- additive direct business capabilities;
- Client scope;
- Ticket Queue scope and server-backed default Queue preferences;
- effective capability display with Group/Direct/Superuser sources;
- explicit sensitive capability presentation, including Credential secret actions;
- `access_control.manage_staff_access` as the routine administration boundary;
- non-superuser self-edit and superuser-target safeguards;
- exclusion of raw framework/identity permissions from the assignable catalogue;
- rejection of Groups containing excluded permissions;
- audit of invitation, access and activation lifecycle changes without secret/token data.

Routine staff administration therefore does not require Django superuser access.
Django remains authoritative for identity, permission and superuser semantics.

See `USERS_ACCESS_ARCHITECTURE.md` and `PERMISSIONS_AND_ACCESS_MODEL.md` for the
full capability/scope and security boundaries.

---

## 11. Dashboard / My Work

Dashboard/My Work is an implemented configurable, server-persisted personal
operations surface rather than a fixed statistics page.

The current widget catalogue includes:

- My Tasks with open/today/overdue focus;
- My Tickets using normal Client/Queue scope and server-backed default Queues;
- active timer and personal weekly Time;
- assigned Lead follow-up;
- current scoped Projects;
- Infrastructure-scoped Monitoring technical health;
- a seven-day Task agenda;
- the current user's own safe audit activity metadata.

The browser stores no Dashboard layout in local storage. One server-side
`DashboardPreference` row stores only ordered known widget keys and supported
column spans. Widget definitions and data queries remain code-owned.

Widget visibility and data obey live backend capabilities and ordinary domain
scope on every request. Stored preferences never grant access, and widgets are
removed from the effective layout immediately when their required capability is
lost. Technical Health uses the same Monitoring check + incident capability
boundary as the normal Monitoring overview.

Stage 9 extends the append-only AuditEvent foundation with explicit Client and
Infrastructure Resource context, allowing richer scoped operational Activity
without inferring object visibility from unsafe labels or metadata. Dashboard
Recent Activity remains intentionally personal; broader Activity lives in its
own permission-aware workspace.

Credential secret values are never surfaced through Dashboard widgets.

See `DASHBOARD_MY_WORK_ARCHITECTURE.md` for the Stage 8 implementation and
security boundary.

---

## 12. Search, activity, notifications and operational polish

Stage 9 is implemented as a coherent cross-domain operational layer rather than
independent search boxes, alert widgets and audit dumps.

### Search

Permission-aware global and Client-context search covers useful non-secret
metadata across Clients, Contacts, Leads, Tickets and visible Ticket message
text, Projects, Tasks, Knowledge Base, Infrastructure and Credential metadata.

Search is a CSRF-aware POST action so arbitrary operator-entered terms do not
enter URL/query-string logging or browser-history surfaces. Each result domain
reuses its normal capability and object scope, and decrypted Credential payloads,
legacy secret fields and encrypted payload data are never searched or returned.

PostgreSQL/database-backed bounded search is sufficient initially. Dedicated
search infrastructure remains unjustified until real scale or relevance quality
requires it.

### Activity and audit/security UX

AuditEvent is append-only and can carry explicit Client and Infrastructure
Resource context. The Activity workspace applies live scope before returning
records, exposes sensitive request metadata only to an explicit permission, and
supports acknowledgement by appending a new audit event rather than mutating the
original history.

Client/resource Activity is intentionally operational history, not a database
change feed. Credential activity can show safe metadata actions but never secret
values.

### Notifications and operational health

A server-backed Notification model provides deterministic, scoped operational
alerts for overdue assigned Tasks, assigned Ticket SLA warnings/breaches,
Credential expiry/rotation health, Monitoring incidents and upcoming Calendar
Events. Read/dismiss state is persisted per staff user and notifications resolve
when the underlying condition disappears.

Credential Health is metadata-only and supports optional per-Credential rotation
intervals. Service Levels records Queue-owned first-response/resolution targets
and Ticket deadlines, exposes warning/breach triage, and permits authorised Queue
policy editing. Infrastructure topology is bounded and permission-aware.

See `UNIFIED_OPERATIONAL_SEARCH_ARCHITECTURE.md` and
`UNIFIED_OPERATIONAL_POLISH_ARCHITECTURE.md` for the detailed Stage 9 contracts,
security boundaries and deliberate deferrals.

---

## 13. Commercial and analytics layer

The commercial layer is deliberately later than the current operational and
technical foundations, but its agreed scope should influence clean extension
points.

Agreed future areas include:

- products/services catalogue;
- recurring services;
- quotes/proposals;
- contracts;
- invoices/billing;
- Stripe/payment tracking;
- billable operational work flowing into commercial reporting where useful;
- Client profitability;
- Client lifetime value;
- time-versus-pay/revenue analysis;
- Lead-source conversion and revenue attribution.

Detailed contract signing, accounting, tax, forecasting, retainer and SLA
models beyond the implemented Ticket operational SLA layer are **not yet
agreed**. Do not invent them during unrelated work.

The commercial layer should reuse existing Client, Lead, Project, Ticket and
Time context rather than create duplicate customer/work models.

Commercial-provider API keys/payment secrets use the Credential Vault rather
than new plaintext secret columns.

---

## 14. Public websites and CMS

The user has moved the three public Brand websites into the active development
phase. The confirmed brief, asset organisation and Web Designs URL migration
inventory are recorded in [the public website brief](PUBLIC_WEBSITES_PLAN.md).
Commercial features remain deferred; public website work need not wait for them.

The proposed [page and service inventory](PUBLIC_WEBSITE_PAGE_INVENTORY.md)
records the multi-page, business-first website scope for review. Adam's full-time
platform engineer role means public copy must not advertise contracting, staff
augmentation or full-time availability. Confirmed services and the pending software consultancy decision are recorded
in the inventory; this does not remove operational/commercial models.

Retain purposeful local service-area pages and Australia/USA market pages with
individually written content. Manchester is the actual base; international work
is remote and must not imply overseas offices. Generate suitable branded social
imagery when needed, using the supplied logos and checking final image fidelity.

When public-site work becomes the primary phase:

- each Brand retains its own public experience;
- normal marketing pages remain code-owned;
- editorial CMS content remains Brand-scoped;
- public forms submit to the shared Django backend and identify Brand/source;
- contact forms continue feeding the Lead + Ticket communication pipeline;
- operational Project remains separate from public CaseStudy/Portfolio.

Public applications must never receive Credential secret payloads simply
because they share the backend repository.

---

## 15. Future Client portal

The Client portal comes after internal operations and relevant commercial
contracts are mature.

Portal identities should use the existing authentication system and link to
ClientContact.

Portal visibility must be explicit per domain and private by default.
Client ownership must never automatically expose:

- Internal resources;
- internal Ticket Notes;
- Credentials/secrets;
- private KB documents;
- staff-only audit/security information.

Credential Vault secret actions are staff-only unless a future explicit threat
model and portal design says otherwise.

---

## 16. Current ordered build plan

The Credential Vault, structured technical-operations stack, Client Command
Centre, Users & Access, Dashboard/My Work and Stage 9 Unified operational polish
are implemented. The next sustained implementation stage is Stage 10 —
Commercial and analytics.

### Stage 1 — Core typed Infrastructure — implemented

The platform now has:

- Server/compute and networking foundations;
- Database Instance/Logical Database structures;
- logical Application + Application Environment context;
- Source Repository plus typed Application/Repository links;
- Provider Account relationships;
- safe resource create/edit/archive lifecycle;
- Credential references rather than duplicate secret fields.

### Stage 2 — Web Infrastructure — implemented

- resource-backed Websites and concrete Website Endpoints;
- Domains with registration/expiry metadata;
- DNS Zones and structured DNS Records;
- non-secret TLS Certificate metadata plus typed Domain coverage;
- explicit registrar/DNS/CDN/WAF/hosting Provider Account context;
- Website Endpoint links to Application Environment, Domain and TLS Certificate;
- nested operational cards for Website Endpoints, DNS Records and TLS Domain coverage;
- Credential links through the shared resource identity for administrative/authentication material.

### Stage 3 — Monitoring and technical dashboards — implemented

- checks/results/incidents;
- current health views;
- uptime/response history;
- expiring TLS/domain alerts;
- global and Client-scoped technical dashboards;
- resource-context technical-health panels;
- authenticated checks deliberately deferred until explicit authentication
  schemes are modelled rather than inferred from Credential type.

### Stage 4 — Knowledge Base — implemented

- folder/section tree;
- Markdown editor;
- protected attachments;
- immutable versions;
- Client/Internal ownership;
- Infrastructure/resource backlinks;
- Credential links without secret duplication;
- contextual and global search foundations.

### Stage 5 — Specialist technical operations — implemented

- Docker/container structures;
- Kubernetes clusters/namespaces/workloads/services/ingresses/Helm/storage at a
  useful operational level;
- storage/backups;
- system services;
- scheduled jobs/cron/systemd timers;
- remaining specialist operations records.

### Stage 6 — Client Command Centre integration pass — implemented

- permission-aware Overview/Contacts/Projects/Tasks/Tickets/Time/Infrastructure/
  Credentials/Knowledge/Activity navigation;
- server-authoritative cross-domain summary and capability projection;
- current-first section defaults with explicit Project/Task history;
- contextual quick actions and Client-prefilled Project/Task creation;
- selected-period tracked/billable Time summaries and Client-scoped Time deep links;
- Ticket Queue-scoped Client communication summaries and history deep links;
- embedded Infrastructure, Monitoring, Credential Vault and Knowledge context;
- bounded safe Activity metadata foundation with no Credential secret values.

See `CLIENT_COMMAND_CENTRE_ARCHITECTURE.md` for the integration and security
boundary. Richer unified Activity/search is implemented in Stage 9.

### Stage 7 — Users & Access — implemented

- active-first staff register/detail and invitation lifecycle;
- Django Groups as reusable capability bundles;
- additive direct business capabilities with sensitive-action visibility;
- Client and Ticket Queue scope administration;
- server-backed default Ticket Queue preferences;
- effective capability/source display;
- audited activation/deactivation and access changes;
- self/superuser safeguards and unsafe Group/framework-permission rejection.

See `USERS_ACCESS_ARCHITECTURE.md` for the implementation and security boundary.

### Stage 8 — Dashboard / My Work — implemented

- one server-persisted personal layout per staff user;
- permission-filtered code-owned widget catalogue;
- My Tasks, My Tickets, Time, Lead follow-up, current Projects, Technical Health,
  Agenda and personal Recent Activity widgets;
- normal Client/Internal, Ticket Queue and Infrastructure scope reused inside
  each relevant projection;
- live permission loss immediately removes saved widgets from the effective
  layout;
- configurable ordering and 4/6/8/12-column widths in the `/admin` workspace;
- no browser-persisted layout and no Credential secret projection;
- audit of preference changes without storing widget data or secret values.

See `DASHBOARD_MY_WORK_ARCHITECTURE.md` for the implementation and security
boundary. Cross-domain Activity, search and notifications are implemented in
Stage 9.

### Stage 9 — Unified operational polish — implemented

- permission-aware global and Client-context search using body-only POST input;
- navigation polish and bounded permission-aware Infrastructure topology;
- explicit Client/resource AuditEvent context and richer scoped Activity;
- dedicated audit/security UX with append-only acknowledgement semantics;
- server-backed scoped operational notifications;
- Credential expiry/rotation health and reminders without secret projection;
- Ticket Queue first-response/resolution SLA policy, recorded deadlines,
  warning/breach triage and escalation suppression while waiting on customer;
- first-class Calendar Events/Meetings/Milestones/Reminders integrated with the
  dated Task/Project Calendar;
- canonical Stage 9 architecture/security documentation.

See `UNIFIED_OPERATIONAL_SEARCH_ARCHITECTURE.md` and
`UNIFIED_OPERATIONAL_POLISH_ARCHITECTURE.md` for the Stage 9 implementation and
security boundaries.

### Stage 10 — Commercial and analytics

Build the agreed products/services, recurring-services, quotes/proposals,
contracts, invoicing, Stripe/payment tracking and profitability/LTV/source
analytics layer.

### Stage 11 — Public websites as primary focus

Complete the three Brand websites against stable platform contracts. This stage
is now active at the user's direction before Stage 10 commercial work, following
the confirmed [website brief](PUBLIC_WEBSITES_PLAN.md).

### Stage 12 — Client portal

Add explicit, narrowly scoped Client-facing access only after the internal and
commercial models are mature enough to expose safely.

The order can move by a small slice when dependencies or real usage justify
it, but a change in major direction should update this document rather than
living only in chat history.

---

## 17. Security and reliability principles

- least privilege by default;
- backend-enforced authorisation and object scope;
- no secrets in Git, ordinary logs, URLs, analytics or audit metadata;
- secret fields opt-in through explicit Vault actions only;
- credential storage fails closed if encryption configuration is unavailable;
- CSRF protection for cookie-authenticated state changes;
- secure production cookies/CORS/trusted origins;
- validated return/redirect URLs;
- rate limiting for authentication and abuse-prone public endpoints;
- external ingestion/delivery is idempotent and retry-safe where practical;
- attachment quarantine/policy enforcement remains active even when malware
  scanning is disabled;
- infected/policy-blocked attachments are never downloadable;
- permission-boundary tests are mandatory for restricted APIs;
- Celery orchestrates asynchronous work but reusable domain logic belongs in
  services rather than only in tasks.

Credential-specific rules, including encryption-key rotation and browser secret
handling, are defined in `CREDENTIAL_VAULT_ARCHITECTURE.md`.

---

## 18. Important non-goals and prohibited shortcuts

Do not:

- create separate Django backends per Brand;
- recreate a separate admin frontend/deployment;
- make every public Brand a recoloured copy of one site;
- use Brand as a substitute for Client/Internal ownership;
- create a fake Internal Client;
- force Tasks to belong to Projects;
- merge operational Projects with public Case Studies;
- return credential secrets in normal list/detail/search APIs;
- duplicate plaintext secrets on Infrastructure, Monitoring, Graph, KB or
  commercial models;
- persist revealed credential secrets in browser storage/routes/analytics;
- implement authorisation only in React;
- give all staff superuser access;
- hard-code each Shared Mailbox as bespoke Graph configuration;
- require per-mailbox certificate/RBAC setup in the normal ADB tenant design;
- treat all Vendor/automated mail as spam;
- create separate email/contact-form/portal communication silos;
- rebuild Time Tracking as one giant history page;
- load entire operational datasets client-side merely to filter/sort them;
- implement speculative portal/accounting/SaaS complexity before its phase.

---

## 19. Architectural statement

> **The ADB Business Platform is one shared operational system serving multiple
> ADB Brands. Django is the business-data, authentication, authorisation and
> scope authority; ADB Software Solutions combines public routes and a protected
> `/admin` workspace in one Next.js application; operational resources are
> Client-owned or Internal; current/actionable work is the default; Client is
> the command-centre context; communications unify into Tickets; and technical
> operations converge on structured Infrastructure, an encrypted Credential
> Vault, Monitoring and linked Knowledge rather than disconnected CRUD
> registers.**

Major future architectural decisions should be checked against this statement
and the canonical documentation set.

### Infrastructure editing completeness

Service Provider metadata/status and shared tag metadata are editable with their
separate view/change capabilities and audit events. All 29 native resource types
use the standard Edit resource action in full pages and drawers. Server
interfaces/IPs, repository links and TLS domain coverage can be edited in place;
outgoing resource relationships retain editable notes and scoped targets.
See `INFRASTRUCTURE_CREATION.md` for entry points and API boundaries.

## GitHub operations dashboard

GitHub is a shared backend integration at `/admin/github`, implemented by
`apps.github_integration`. One GitHub App supports multiple organisation/personal
installations. Each installation is approved into one Client/Internal context;
repository inventory uses the native InfrastructureResource + SourceRepository
records. ApplicationRepositoryLink remains a relationship to that same record.
Signed webhooks and Celery update issue/PR/workflow/run projections automatically.
My-work filters exclude bots and keep Dependabot separately visible. Workflow
dispatch, failed-job reruns and log access have independent capabilities and audits.
Django remains the identity and permission authority; there is no separate GitHub
login or frontend token store. GitHub signing reads `GITHUB_APP_PRIVATE_KEY`
directly from Infisical-injected backend environments, with no Internal Vault
copy or bootstrap step. Operators rotate the PEM in Infisical and redeploy.
See `GITHUB_APP_SETUP.md` for deployment and limits.

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

Platform background-task operations live at `/admin/celery` in the combined
operations application. The shared Django backend tracks safe task lifecycle
metadata automatically and exposes bounded worker/queue inspection. Existing
Redis SSE transports task and worker invalidations. Access is limited to active
staff superusers; confirmed, audited controls dispatch existing parameter-free
Beat jobs and request cooperative revocation without terminating workers.
No separate monitoring application/image, OAuth registration or Redis database
is required. See [Celery operations](CELERY_DASHBOARD.md).

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

## Public website implementation

The initial implementation is checkpointed at `e74c153`. Its visual design is being
revised following user feedback; see [the reference review](PUBLIC_WEBSITE_DESIGN_REFERENCES.md).
The user has approved the current Web Designs site and requested a checkpoint.
Its services, locations, information, contact and editorial pages use the same
local visual language. Software Solutions and Technology now use that approved
family design with their own content and homepage compositions. Shared public
policy/analytics components receive Brand facts from local content files;
analytics is confined to public layouts and reads Infisical IDs at runtime.
The service scope, brand boundaries, CMS and communication architecture are unchanged.

All three public sites implement brand-specific homepage compositions,
individual service/area pages and a remembered dark/light public theme. Code-owned
copy lives in each site's `src/content/site.ts` and `home.ts`; shared public
primitives, metadata and safe Markdown rendering live under `packages/ui/src/public`.
The Software public/admin route boundaries keep operational providers out of the
marketing layout; authentication remains in the dedicated account app.

Portfolio, Testimonials and FAQs now have explicit `published` flags, defaulting
to drafts; BlogPost publication also respects future publication dates. Public
collections paginate at the Django database boundary and filter Brand at query
and nested-taxonomy boundaries. Editorial media uploads require the corresponding
Django `website.change_*` capability, allow bounded raster images and normalize
uploads to WebP. Public forms use fixed serving-site Brand identity and preserve
the existing Lead/Ticket ingestion flow. Runtime `API_INTERNAL_URL` can route
SSR and contact requests privately to the shared backend. Exact private hosts
are admitted through `INTERNAL_API_HOSTS`; `PUBLIC_MEDIA_URL` ensures editorial
images still resolve through a public media origin. No new data store or
identity authority is introduced.

The Web Designs WordPress migration uses relevant permanent redirects, conditional
CMS aliases and real 404s for retired content. Imported original articles remain
unpublished drafts pending review. See the page inventory, URL migration ledger
and morning review document before a production cutover.

### Enquiry retention

Unsuccessful enquiry history has a 36-month inactivity review period. The
operations workspace provides a manually approved deletion queue, with reasoned
keep/defer decisions. Daily Celery scans must never automatically delete Leads.
See [Lead retention](LEAD_RETENTION.md) for the authoritative workflow and scope.

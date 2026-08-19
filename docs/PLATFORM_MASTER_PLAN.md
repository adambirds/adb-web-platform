# ADB Business Platform Master Plan

## Purpose

This document is the canonical product and architecture plan for the ADB Business Platform. It describes the platform that exists today, the architectural rules that must remain true, and the ordered work required before the public websites become the main development focus.

When older root-level planning documents conflict with this document, this document takes precedence unless a newer explicit architectural decision updates it.

The platform is not merely three marketing websites with an admin area. It is intended to become the central operational system used to run the ADB businesses: CRM, clients, projects, tasks, time tracking, ticketing and email, documentation, credentials, infrastructure inventory, content publishing, staff access, dashboards, calendar/work planning, and later client-facing/commercial workflows.

The design must remain pragmatic. Future capabilities should influence clean boundaries where useful, but speculative features must not be implemented prematurely.

---

## 1. Product vision

ADB operates three public brands:

1. **ADB Software Solutions** — `adbsoftwaresolutions.co.uk`
   - bespoke software development;
   - SaaS and application development;
   - APIs and third-party integrations;
   - automation;
   - mobile applications;
   - software consultancy;
   - ADB-owned software products.
2. **ADB Web Designs** — `adbwebdesigns.co.uk`
   - website design and development;
   - WordPress and Next.js delivery;
   - website rescue/remediation;
   - performance improvements;
   - hosting and maintenance;
   - ongoing website support.
3. **ADB Technology** — `adbtechnology.co.uk`
   - DevOps;
   - cloud and infrastructure engineering;
   - IT consultancy;
   - systems administration;
   - technical support;
   - infrastructure and operational support services.

The three public brands have separate positioning and public experiences, but they share **one ADB Business Platform** behind them.

The internal platform should reduce dependence on separate CRM, helpdesk, task-management, documentation, infrastructure-inventory and lightweight commercial tools. It takes inspiration from systems such as HubSpot, IT Glue, Asana and modern ticket/helpdesk products, while being designed around ADB's actual workflows rather than reproducing those systems feature-for-feature.

---

## 2. Repository and application architecture

The repository is a monorepo with this current high-level layout:

```text
backend/
packages/
sites/
    adb-software-solutions/
    adb-web-designs/
    adb-technology/
    auth-adb-software-solutions/
```

There is **no separate `admin-adb-software-solutions` application**. The ADB Software Solutions Next.js application serves both its eventual public marketing routes and the authenticated internal operations workspace under `/admin`.

### 2.1 Shared Django backend

`backend/` is the single business-data and operations backend. It owns:

- authentication and authorisation;
- staff users and access scopes;
- Brands;
- clients and contacts;
- CRM/leads;
- projects;
- tasks;
- time tracking;
- ticketing and communications;
- Microsoft Graph connections and mailboxes;
- knowledge base;
- credentials/secrets;
- infrastructure inventory;
- CMS content;
- audit logging;
- Celery/background processing;
- future calendar/event persistence where required;
- future quoting/contracts/invoicing/payment data;
- future client-portal data and visibility rules.

Django remains authoritative for permissions, object scope and business rules. Frontend visibility is UX, never an authorisation boundary.

The API layer is **Django Ninja**. Do not reintroduce historical plans for DRF or GraphQL unless a future explicit decision requires them.

### 2.2 ADB Software Solutions application

`sites/adb-software-solutions/` is a Next.js App Router / TypeScript application with two distinct route concerns:

- public ADB Software Solutions marketing routes; and
- authenticated internal operations routes under `/admin`.

These concerns share one deployable application but must remain cleanly separated through App Router route groups/layout boundaries. The internal admin is a dark, information-dense operations console; public marketing UX must not leak privileged internal functionality.

### 2.3 Other public websites

`sites/adb-web-designs/` and `sites/adb-technology/` remain independent Next.js public applications. The three public sites must not become recoloured copies of one template. Shared packages are for genuinely shared primitives, contracts and tooling, not forced visual uniformity.

Normal marketing pages are code-owned. CMS-managed public content is intentionally limited to content that benefits from ongoing editorial management, including blog posts, testimonials, FAQs and optionally public case studies.

### 2.4 Authentication/account application

`sites/auth-adb-software-solutions/` is the dedicated Next.js authentication/account-security application. Django remains the identity/session authority.

It owns browser flows for:

- login/logout;
- registration where enabled;
- email verification;
- password reset;
- account/security settings;
- passkeys/WebAuthn;
- TOTP 2FA;
- recovery codes;
- sessions/devices.

Do not introduce Auth.js/NextAuth, browser-stored JWTs or another authentication authority without an explicit architectural decision.

---

## 3. Core domain rules

### 3.1 Brand is first-class

`Brand` represents the public ADB business under which public content, communication or work is presented. Initial Brands are ADB Software Solutions, ADB Web Designs and ADB Technology.

Brand is not a substitute for Client ownership.

Example:

```text
Ticket
brand = ADB Web Designs
client = Welcome to Travel
```

### 3.2 Operational ownership is Client or Internal

Operational resources must model their ownership context deliberately:

```text
Operational resource
├── client-owned
│   └── Client
└── internal
    └── ADB itself
```

Never create a fake ADB Client merely to represent internal resources.

### 3.3 Client is the primary operational context

A Client is an operational workspace, not merely a company row. The target Client workspace is:

```text
Client
├── Contacts
├── Tickets / communications
├── Leads / sales history where relevant
├── Projects
├── Tasks
├── Time entries and reports
├── Knowledge Base
├── Credentials
├── Infrastructure
├── Domains / licences / certificates
├── Activity / notes / audit context
└── future quotes, contracts, invoices and portal access
```

Staff should be able to move through this context without repeatedly searching unrelated modules.

### 3.4 Contacts bridge communications to Clients

ClientContact email addresses are a primary matching key for inbound communication. Known contacts should automatically enrich Tickets with Client context. Future portal identities should link to ClientContact rather than creating a duplicate customer-person model.

### 3.5 Permissions = capability + scope

Django Groups/Permissions grant capabilities. Scope determines which objects those capabilities apply to.

Examples:

- a user may have `view_ticket` but only for selected queues/clients;
- credential metadata view and credential secret reveal are separate capabilities;
- permission/access changes and sensitive reveals must be auditable.

The frontend should avoid showing unavailable actions but backend checks remain authoritative.

---

## 4. Current implemented platform foundation

The following foundations now exist and should be treated as implemented architecture rather than future proposals:

- Brand-aware CMS and public content isolation;
- Django-backed identity, session, TOTP and WebAuthn/passkey flows;
- capability permissions and Client access scopes;
- append-only audit-event foundation;
- internal operations shell under `/admin`;
- list/register views for Clients, Projects, Leads, Tasks, Time, Knowledge Base, Credentials and Infrastructure;
- Client detail context for contacts/projects/tickets;
- ticket queues, Tickets, Messages, Notes and Attachments;
- queue/client permission scoping;
- ticket assignment, status, priority and queue operations;
- Microsoft Graph application connections and Shared Mailbox configuration;
- app-only client-secret/certificate Graph authentication;
- Graph mailbox verification, delta sync and outbound replies;
- website contact-form Lead -> Ticket ingestion;
- deterministic message classification/routing;
- database-backed Vendor/service sender routing;
- attachment quarantine/policy enforcement and optional ClamAV malware scanning;
- Celery workers/beat and Redis-backed background orchestration;
- development seed data and multi-architecture devcontainer CI.

These implementations are foundations, not evidence that the operational modules are complete. Most non-ticket modules still need proper day-to-day CRUD/workflow UX.

---

## 5. Ticketing and communications architecture

Tickets are the unified communication thread. Email messages, website contact submissions and future portal communication must not become unrelated silos.

Core rules:

- Ticket is the operational thread;
- TicketMessage is one inbound/outbound message;
- TicketNote is internal-only;
- TicketAttachment is governed/quarantined content;
- Mailbox is first-class configuration;
- known Client/Contact resolution occurs before Vendor classification;
- unknown/non-client senders are not automatically spam;
- queues are permission-scopeable;
- threading uses message/provider references, never subject alone;
- classification/routing is deterministic first and does not require AI;
- Graph/Celery integrations must be idempotent and safely retryable.

See `docs/TICKETING_ARCHITECTURE.md` for the detailed implementation architecture and `docs/MICROSOFT_GRAPH_TICKETING_SETUP.md` for tenant/deployment configuration.

---

## 6. Microsoft 365 / Graph deployment model

ADB ticketing normally uses one Microsoft Entra application and one tenant-level `MicrosoftGraphConnection`, with many database `Mailbox` rows representing operational Microsoft 365 Shared Mailboxes.

Production should prefer certificate-based app-only authentication. Exchange Online RBAC for Applications provides the external mailbox boundary; database Mailbox rows provide the narrower application-level operational allow-list.

Do not grant broad unscoped Entra mail application permissions alongside scoped Exchange RBAC in a way that restores organisation-wide access. The permissions are additive.

Mailbox sync and outbound delivery run in Celery. Application/domain logic belongs in reusable services rather than only in tasks.

---

## 7. Knowledge Base, Credentials and Infrastructure

These domains form the IT Glue-style operational documentation workspace and are a major pre-public-site development priority.

### 7.1 Knowledge Base

Target capabilities:

- Client/Internal ownership;
- create/edit/archive/delete policy appropriate to documentation;
- categories/sections/tags;
- Markdown or controlled rich-text content;
- attachments where appropriate;
- author/editor metadata;
- change/version history;
- global and Client-context search;
- links to Infrastructure, Credentials, Tickets and Projects;
- permission-aware results;
- explicit future portal visibility, private by default.

### 7.2 Credentials vault

Target capabilities:

- Client/Internal ownership;
- encrypted-at-rest secret payloads;
- metadata-only list/search responses;
- explicit create/edit/rotate/archive flows;
- separate reveal and copy permissions;
- audited reveal/copy operations;
- safe clipboard/reveal UX;
- expiry/rotation metadata;
- links to Infrastructure/Application records;
- no secret values in ordinary logs, analytics or error payloads.

The platform already has encrypted `StoredCredential` secret services; operational CRUD/reveal UX still needs completion.

### 7.3 Infrastructure inventory

The target structured inventory includes Servers, Databases, Websites, Domains, SSL Certificates, Licences, logical Applications, Mobile Apps, APIs/services, Bots/automations, Email systems and related repository/provider metadata where useful.

Infrastructure should be navigable as a relationship graph in normal product UX without requiring a generic graph database. A logical Application may link to websites, APIs, databases, workers, domains, credentials, repositories and a Client.

Infrastructure records reference credentials; they do not duplicate plaintext secrets.

---

## 8. Operational CRUD and workflow completion

Before public-site development becomes the main focus, the internal platform must become genuinely usable for daily operations.

### 8.1 Clients and Contacts

Required work:

- create and edit Clients;
- archive/reactivate rather than relying on destructive deletion;
- create/edit contacts and contact roles/flags;
- Client detail workspace with coherent sections/tabs;
- Client-scoped Tickets, Infrastructure, KB, Credentials, Projects, Tasks and Time;
- Client activity/history where useful;
- permission-aware actions and navigation.

### 8.2 CRM / Leads

Required work:

- Lead list variants and filters;
- Lead detail view;
- create/edit/archive/convert workflows;
- owner/assignee;
- Brand/source/value metadata where useful;
- communication history;
- explicit relationship to Tickets/email threads;
- contact matching/deduplication;
- Lead -> Client/Contact conversion without losing communication history.

Website contact forms already create Leads and Tickets; the CRM UI must expose that relationship rather than treating them as separate records.

### 8.3 Projects

Required work:

- Project detail workspace;
- create/edit/archive/status workflows;
- Client/Internal context;
- staff ownership/participants where useful;
- milestones/dates;
- related Tasks, Time, Tickets, KB and Infrastructure links;
- reporting/summaries appropriate to actual delivery work.

Operational Project remains separate from public CaseStudy/Portfolio.

### 8.4 Tasks

Required work:

- create/edit/delete/archive as appropriate;
- mark complete/reopen;
- assignment;
- priorities, due/start dates and recurrence;
- standalone, Client, Project and future Ticket-related tasks;
- practical list modes such as My Tasks, Today, Upcoming, Overdue, Completed, by Project and by Client;
- filtering/sorting/pagination;
- quick actions from relevant Client/Project/Ticket contexts.

Tasks must never require a Project.

---

## 9. Calendar and work planning

The admin platform needs a calendar/work-planning surface that can aggregate dated operational items without forcing every source record into one table.

Initial calendar sources should include:

- Task start/due dates;
- Project milestones/deadlines;
- scheduled recurring work where materialised;
- later first-class Events/Meetings;
- future external calendar integration only when explicitly designed.

The calendar should support day/week/month views and permission-aware filtering by user, Client, Project and source type. A future Event/Meeting model can be added without pretending Tasks or Project milestones are events.

---

## 10. Time tracking

Time tracking is a cross-cutting operational capability, not merely a register.

Required behaviour:

- manually create/edit/delete time entries subject to permissions;
- start a running timer and stop it to calculate duration;
- only one active timer per user unless a future explicit decision changes that rule;
- start timers from Task, Project and Ticket contexts;
- optionally associate Client directly where no Project is required;
- description/notes and billable/non-billable metadata where useful;
- daily/weekly/monthly views;
- summaries by Client, Project, Task, Ticket and staff user;
- Client workspace time totals and period reporting;
- future billing/invoice linkage without making invoicing a current dependency.

Timer lifecycle operations must be backend-authoritative so browser refreshes or multiple tabs do not corrupt elapsed time.

---

## 11. Users and Access

The `/admin` Users & Access experience must be a functioning first-class administration area, not a dead navigation route.

Required behaviour:

- list/view staff users;
- create/invite/activate/deactivate according to the established identity model;
- manage Groups/capability permissions;
- manage Client access scopes;
- manage Ticket Queue access scopes;
- expose effective access clearly;
- audit permission/scope changes;
- never require routine operators to become Django superusers.

Security-sensitive identity changes remain in Django and must have explicit tests for permitted and denied paths.

---

## 12. Dashboard

The dashboard should evolve from a fixed overview into a configurable operations surface.

Target model:

- widget catalogue controlled by effective permissions;
- per-user persisted layout/configuration;
- movable/resizable/reorderable widgets where practical;
- sensible default dashboard;
- widgets own explicit filters/config rather than embedding one giant dashboard query.

Example widgets:

- Tickets assigned to me;
- Ticket Queue with a selected queue;
- unassigned/open/overdue Tickets;
- My Tasks / overdue Tasks / upcoming work;
- active timer and recent Time;
- Leads requiring follow-up;
- Project status/milestones;
- expiring Domains/Licences/Certificates;
- recent audit/security events for authorised users;
- calendar agenda.

Widget queries must obey the same backend permissions and object scopes as normal screens.

---

## 13. Search and cross-context navigation

Search is an important usability layer once CRUD/workspaces exist.

Client-context search should cover permitted records across:

- KB documents;
- credential metadata (never secret values);
- Infrastructure;
- Tickets/messages where appropriate;
- Projects;
- Tasks;
- Contacts;
- Leads/history where relevant.

A PostgreSQL-backed implementation is acceptable initially. Dedicated search infrastructure should only be added when scale/quality justifies it.

Search must never bypass normal permission scope.

---

## 14. API and service design principles

Backend APIs should remain domain-based and explicit, for example:

```text
/api/auth/...
/api/public/...
/api/admin/brands/...
/api/admin/clients/...
/api/admin/crm/...
/api/admin/projects/...
/api/admin/tasks/...
/api/admin/time/...
/api/admin/tickets/...
/api/admin/knowledge-base/...
/api/admin/credentials/...
/api/admin/infrastructure/...
/api/admin/staff/...
/api/admin/dashboard/...
/api/admin/calendar/...
/api/admin/audit/...
```

Rules:

- explicit schemas;
- consistent collection pagination;
- predictable errors;
- backend permission checks;
- sensitive fields opt-in only;
- avoid N+1 queries;
- public APIs explicitly Brand-scoped;
- reusable business logic lives in services;
- Celery orchestrates async work rather than owning all domain logic;
- external operations are idempotent/retry-safe where possible.

---

## 15. UI/UX principles for the operations platform

The admin is workflow-oriented, not a one-page-per-model CRUD generator.

Top-level operational areas include:

- Dashboard;
- Tickets;
- Clients;
- CRM/Leads;
- Projects;
- Tasks;
- Calendar;
- Time;
- Knowledge Base;
- Credentials;
- Infrastructure;
- Content;
- Users & Access;
- Audit/Security;
- Settings/Integrations.

Data-heavy pages use server-side pagination/filtering and clear drill-down navigation. Detail workspaces should surface related context rather than forcing operators to repeatedly return to global registers.

---

## 16. Ordered roadmap before public-site focus

The public websites remain important, but they are **not the next primary phase**. The internal platform must first become operationally complete enough to run day-to-day ADB work.

### Phase A — Architecture, deployment docs and dependency health

- reconcile canonical/current-state documentation;
- maintain complete Microsoft Graph deployment/setup documentation;
- keep dependencies/security fixes current;
- keep CI/devcontainer/deployment paths green.

### Phase B — Core operational CRUD and access

- Clients/Contacts full CRUD/workspaces;
- Leads full CRUD/detail/communication linkage;
- Projects detail/CRUD;
- Tasks full workflow/list modes;
- repair and complete Users & Access.

### Phase C — IT Glue-style workspace

- Knowledge Base CRUD, taxonomy, search and history;
- Credentials vault CRUD/reveal/copy/rotation/audit;
- Infrastructure CRUD/relationships;
- cross-links among Clients, KB, Credentials and Infrastructure;
- Client-context/global search.

Parts of B and C may proceed in parallel, but Client scope/ownership must remain the common foundation.

### Phase D — Time and planning

- timer-based and manual Time Tracking;
- integration with Clients/Projects/Tasks/Tickets;
- week/month/reporting views;
- Calendar aggregating Tasks, Project milestones and later Events/Meetings.

### Phase E — Integrated workspaces and configurable dashboard

- complete Client workspace across Tickets/Infra/KB/Projects/Tasks/Time;
- contextual Project/Ticket work surfaces;
- configurable per-user dashboard widgets/layout;
- operational summaries/alerts.

### Phase F — Public websites

Only after the internal platform above is usable should the three public sites become the main development focus. Public-site work can still occur opportunistically for fixes or stable integration needs.

### Phase G — Client-facing/commercial features

Deferred until the internal platform is mature:

- client portal;
- quotes;
- contracts/signatures;
- invoicing;
- recurring billing;
- Stripe payments;
- client-facing project/ticket/document views.

---

## 17. Security principles

- least privilege by default;
- backend-enforced authorisation;
- no secrets in Git or ordinary logs;
- no credential secrets in list/search responses;
- audit sensitive actions;
- use established cryptographic/auth libraries;
- validate redirects;
- CSRF protection for cookie-authenticated state changes;
- secure production cookies/CORS configuration;
- rate-limit authentication and abuse-prone public endpoints;
- verify external providers/webhooks;
- make background ingestion idempotent;
- infected/policy-blocked attachments never become downloadable;
- permission-boundary tests are mandatory as restricted APIs are added.

---

## 18. Important non-goals and anti-patterns

Do not:

- create separate Django backends per public Brand;
- recreate a separate admin Next.js deployment;
- duplicate CMS per Brand;
- turn the CMS into a generic page builder;
- force Tasks to belong to Projects;
- treat internal ADB as a fake Client;
- use Brand as a substitute for Client/Internal ownership;
- merge operational Project and public CaseStudy models;
- store plaintext secrets on Infrastructure models;
- implement authorisation only in React;
- give all staff superuser access;
- hard-code every mailbox as bespoke Graph logic;
- treat all automated/vendor mail as spam;
- create separate contact-form and email communication silos;
- build speculative client-portal/payment complexity before internal operations are mature.

---

## 19. Current architectural statement

> **The ADB Business Platform is one shared operational system serving multiple ADB brands. ADB Software Solutions combines its public site and authenticated `/admin` workspace in one Next.js application; Django is the shared business-data and authorisation authority; public editorial content is Brand-scoped; operational resources are Client-scoped or Internal; communications unify into Tickets; and every major operational domain should become navigable from the surrounding Client/work context.**

Substantial future architectural decisions should be checked against this statement and the canonical documentation set.
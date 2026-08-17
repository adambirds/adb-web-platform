# ADB Business Platform Master Plan

## Purpose of this document

This document is the canonical product and architecture plan for the ADB business platform. It is intentionally detailed so that a new developer, coding agent, or future conversation can understand the intended system without relying on historical chat context.

When older planning documents conflict with this document, this document takes precedence unless a newer architectural decision explicitly supersedes it.

The platform is not merely a collection of marketing websites with an admin area. It is intended to become the central system used to operate the ADB businesses: customer relationship management, project and task management, support and email ticketing, documentation, infrastructure inventory, credentials, content publishing, and eventually quoting, contracts, invoicing, payments and client portals.

The design must remain pragmatic. Features described as future work should influence data boundaries and extensibility where useful, but must not be implemented prematurely.

---

## 1. Product vision

ADB operates three distinct public brands:

1. **ADB Software Solutions** — `adbsoftwaresolutions.co.uk`
    - Bespoke software development.
    - SaaS and application development.
    - API and third-party integrations.
    - Automation.
    - Mobile applications.
    - Software consultancy.
    - ADB-owned software products.

2. **ADB Web Designs** — `adbwebdesigns.co.uk`
    - Website design and development.
    - WordPress and Next.js delivery.
    - Website rescue and remediation.
    - Performance improvements.
    - Hosting and maintenance.
    - Ongoing website support.

3. **ADB Technology** — `adbtechnology.co.uk`
    - DevOps.
    - Cloud and infrastructure engineering.
    - IT consultancy.
    - Systems administration.
    - Technical support.
    - Infrastructure and operational support services.

These brands have separate public websites and should not be treated as recoloured versions of one template. They share infrastructure and business operations, but their public positioning, information architecture, content and presentation may differ significantly.

Behind all three brands sits **one shared ADB Business Platform**.

The platform should eventually replace or reduce dependence on separate products such as CRM, helpdesk, task management, infrastructure documentation, password/documentation systems and lightweight invoicing tools.

Conceptually, it combines relevant capabilities from systems such as HubSpot, IT Glue, Asana and a ticket/helpdesk platform, but it should be designed specifically around ADB's workflows rather than reproducing those products feature-for-feature.

---

## 2. Repository/application architecture

The repository is a monorepo with this high-level layout:

```text
backend/
packages/
sites/
    adb-software-solutions/
    adb-web-designs/
    adb-technology/
    auth-adb-software-solutions/
    admin-adb-software-solutions/
```

### Backend

`backend/` is the single Django backend for the entire platform. It owns:

- authentication and authorisation;
- staff users;
- future client-portal users;
- brands;
- clients and contacts;
- CRM/leads;
- projects;
- tasks;
- time tracking;
- tickets and communications;
- mailbox and Microsoft Graph integrations;
- CMS content;
- credentials;
- knowledge base;
- infrastructure inventory;
- audit logging;
- Celery/background processing;
- future quoting/contracts/invoicing/payment data.

Django remains the authority for permissions and business rules. A frontend hiding a button is never sufficient access control.

### Public websites

The three public sites use Next.js App Router and TypeScript.

The majority of normal marketing pages are **code-owned**, not CMS pages. This includes home, about, services, service landing pages and other structured marketing pages.

The CMS is intentionally limited to content that benefits from ongoing editorial management:

- blog posts;
- testimonials;
- FAQs;
- optionally public case studies/projects.

This prevents the backend from becoming a generic page builder.

### Authentication frontend

`sites/auth-adb-software-solutions/` is the dedicated account and authentication UI. It is responsible for:

- login;
- logout;
- account registration where enabled;
- email verification;
- forgotten/reset password flows;
- account security settings;
- passkeys;
- TOTP two-factor authentication;
- recovery codes;
- sessions/devices.

It is deliberately separate from both the public sites and the internal admin application.

### Admin frontend

`sites/admin-adb-software-solutions/` is the internal operations UI. It will eventually expose the majority of the business platform features described in this plan.

It is not a marketing website and must not contain public marketing routes.

---

## 3. Core architectural concepts

### 3.1 Brand is a first-class concept

A `Brand` represents one of the public ADB businesses.

Initial brands are:

- ADB Software Solutions;
- ADB Web Designs;
- ADB Technology.

The platform must not encode these only as hard-coded strings scattered through application logic.

A Brand will eventually provide or reference configuration such as:

- display name;
- slug;
- primary domain;
- active/inactive status;
- public-site identity;
- default support mailbox;
- default sales/contact mailbox;
- default accounts mailbox where relevant;
- other brand-specific integration settings where genuinely required.

Brand scope and client ownership are **different dimensions**.

For example:

```text
Ticket
brand = ADB Web Designs
client = Welcome to Travel
```

A blog post may be brand-owned but have no client relationship.

An internal server may be internal to ADB and not belong to a public brand at all.

### 3.2 Operational ownership is client or internal

Operational resources should have an explicit ownership context.

The core rule is:

```text
Operational resource
├── Client-owned
│   └── belongs to a Client
└── Internal
    └── belongs to ADB itself
```

This applies to resources such as:

- knowledge-base documents;
- credentials;
- infrastructure inventory;
- projects where appropriate;
- tasks where appropriate;
- licences;
- documentation;
- future contracts and commercial records.

Do not misuse Brand as the ownership mechanism. A resource may be internal yet related to one brand, client-owned yet serviced under another brand, or not brand-specific at all.

### 3.3 Client is the main operational context

A Client represents a customer/business rather than merely a row of company details.

A client workspace should ultimately expose:

```text
Client
├── Contacts
├── Tickets and communications
├── Leads/history where applicable
├── Projects
├── Tasks
├── Time entries
├── Knowledge base
├── Credentials
├── Infrastructure
├── Domains
├── Licences
├── Notes/activity
├── Future quotes/contracts
├── Future invoices/payments
└── Future client-portal access
```

This relationship is central to the platform's value. When working on a support ticket, the operator should immediately have access to the relevant client's context rather than manually searching unrelated systems.

### 3.4 Contacts belong to clients

A client may have many contacts.

Contacts should support, at minimum:

- name;
- one or more useful contact details, especially email;
- role/job title where relevant;
- active/inactive status;
- primary-contact marker;
- technical-contact marker;
- billing-contact marker;
- future portal-access relationship.

Email addresses on client contacts are particularly important because they allow inbound mail to be automatically associated with the correct client.

### 3.5 Internal records are not fake clients

Do not create a fake `ADB Software Solutions` Client merely to represent internal ownership. Internal ownership should be a deliberate state in the model/domain design.

Likewise, avoid ambiguous nullable relationships where `client = null` can mean several unrelated things. Application services and schemas should make the difference between internal and client-owned resources clear.

---

## 4. Authentication and identity

Authentication is already one of the more mature subsystems and should be consolidated rather than replaced.

Required capabilities include:

- email/password authentication;
- email verification;
- password reset;
- TOTP two-factor authentication;
- recovery codes;
- WebAuthn/passkeys;
- session/device management;
- authentication/security event logging;
- rate limiting of sensitive endpoints.

### Internal staff and future client users

Long term, the same identity system should be capable of representing both:

```text
User
├── Internal staff user
└── Client portal user
```

Do not create an entirely separate authentication implementation for future client portals.

A future client user should be linked to a `ClientContact` and be constrained to that client's allowed portal resources.

The portal itself is explicitly **future work** and is not part of the current foundational implementation.

---

## 5. Permissions and authorisation

Fine-grained permissions are foundational and must be designed from the beginning.

The platform will have more than one internal user. Different staff may require different access to clients, features, ticket queues and sensitive resources.

The permission architecture should combine three concepts:

1. **Permission primitives** — what action a user may perform.
2. **Roles** — convenient bundles of permissions.
3. **Scope grants** — which clients/queues/resources those permissions apply to.

### 5.1 Permission primitives

Django model permissions may provide part of the foundation, but permissions must reflect meaningful business actions rather than only CRUD when required.

Examples:

```text
clients.view_client
clients.add_client
clients.change_client
clients.delete_client
clients.manage_contacts

projects.view_project
projects.add_project
projects.change_project
projects.archive_project

work.view_task
work.add_task
work.change_task
work.assign_task

support.view_ticket
support.reply_ticket
support.assign_ticket
support.change_priority
support.merge_ticket
support.close_ticket

knowledge_base.view_document
knowledge_base.change_document
knowledge_base.publish_document

credentials.view_credential
credentials.add_credential
credentials.change_credential
credentials.delete_credential
credentials.reveal_secret

infrastructure.view_asset
infrastructure.change_asset

staff.manage_users
staff.manage_roles
staff.manage_permissions
```

Names may change during implementation, but the principle is important: revealing a credential secret, replying to a ticket and changing staff permissions are distinct capabilities.

### 5.2 Roles

Roles are reusable starting points, not hard security boundaries.

Possible future roles include:

- Administrator;
- Support;
- Operations;
- Accounts;
- Read-only;
- Custom.

A user may receive a role and then explicit additions/removals where needed.

The initial system should not become excessively complicated by implementing every possible combination in the UI immediately. The data and backend policy model, however, must avoid assumptions that every staff member is a superuser.

### 5.3 Client scope

Possessing a permission does not necessarily grant access to every client.

A staff member may be scoped to:

- all clients;
- selected clients;
- internal resources;
- combinations supported by the eventual policy model.

The exact schema should be designed deliberately before feature APIs are implemented widely.

### 5.4 Ticket queue scope

Ticket access also needs queue-level restrictions.

For example, a staff member may have access to Support and Sales but not Accounts.

A user with `support.view_ticket` should still fail backend authorisation when the ticket belongs to a queue or client outside their permitted scope.

### 5.5 Credential restrictions

Credentials are unusually sensitive.

At minimum, distinguish:

- seeing that a credential record exists;
- viewing non-secret metadata;
- revealing/copying secret values;
- editing the secret;
- deleting the credential.

Credential reveals must be auditable.

### 5.6 Backend authority

Every API query and mutation involving restricted data must enforce permissions in Django.

The frontend may use permission data to:

- hide unavailable navigation;
- disable actions;
- avoid requesting inaccessible data;
- provide clearer UX.

It must never be the only enforcement layer.

---

## 6. Audit logging

Audit logging is part of the foundation because permissions, credentials and future financial/client features require traceability.

The platform should ultimately record meaningful security and administrative actions, including:

- authentication/security events;
- permission changes;
- staff-role changes;
- credential reveals;
- credential changes/deletions;
- changes to sensitive client data;
- ticket assignment/status changes where valuable;
- other high-value administrative changes.

An audit record should be able to retain relevant context such as:

- actor/user;
- event/action;
- object type and identifier where applicable;
- timestamp;
- IP address;
- session/device where available;
- safe structured metadata describing the change.

Never place plaintext credential secrets, passwords, tokens or similarly sensitive values in audit metadata.

---

## 7. CMS and public content

### 7.1 Code-owned pages

The main marketing pages remain in the appropriate Next.js site repository directory and are changed through code review/deployment.

Examples:

- home;
- about;
- services;
- service landing pages;
- contact page layout;
- static SEO/location/service content where appropriate.

### 7.2 CMS-owned content

The shared backend provides editorial management for:

- blog posts;
- blog categories/tags;
- testimonials;
- FAQs and FAQ categories;
- optionally public projects/case studies.

### 7.3 Brand-aware CMS

Every published content item must explicitly identify where it is eligible to appear.

A many-to-many Brand relationship is suitable for content that may legitimately appear on multiple brands, such as testimonials, FAQs or some case studies.

Blog ownership may normally be one brand, but the final implementation may still use a multi-brand relationship if it keeps the model consistent and permits deliberate cross-publication.

Public API queries must filter by brand and publication state. A public site must never accidentally display content belonging only to another brand.

### 7.4 Internal Project versus public Case Study

These are different concepts.

`Project` is an operational record used to run work:

- client/internal context;
- tasks;
- time entries;
- status;
- budget/billing metadata where relevant;
- internal notes.

A public case study/project is editorial content:

- title;
- public narrative;
- problem;
- solution;
- outcome;
- technologies;
- images/media;
- publication/SEO data;
- brand visibility.

A public case study may optionally reference an internal Project, but the two must not be the same model. This prevents internal/commercial details leaking into public APIs and allows editorial copy to differ from operational records.

---

## 8. CRM and leads

CRM is responsible for the sales/pre-client lifecycle rather than general support communication.

A Lead should eventually support concepts such as:

- originating brand;
- source/channel;
- contact information;
- status/stage;
- notes/activity;
- linked conversations/tickets;
- estimated value where useful;
- won/lost state;
- conversion to a Client.

Typical sources include:

- website enquiry;
- direct email;
- referral;
- social media;
- manual entry;
- marketplace/other channel.

When a lead becomes a client, its conversation history should remain connected rather than being duplicated or discarded.

---

## 9. Projects

Projects track real work being performed either for a client or internally.

A Project may include:

- client or internal ownership;
- title/name;
- description;
- status;
- start/end dates;
- project owner;
- linked tasks;
- linked tickets where useful;
- linked time entries;
- notes;
- future billing metadata such as billing type, budget, rate and currency.

Do not require every task to belong to a project.

---

## 10. Tasks and work management

Tasks are first-class operational work items.

A Task may optionally relate to:

- a Client;
- a Project;
- a Ticket;
- a task list/category;
- an assignee.

It may also be entirely internal and independent.

Example project task:

```text
Fix checkout bug
client = Example Ltd
project = Website Redesign
```

Example support-derived task:

```text
Investigate DNS issue
client = Example Ltd
ticket = 1234
project = null
```

Example standalone internal recurring task:

```text
Send monthly invoices
client = null
project = null
internal = true
recurrence = monthly
```

Required concepts over time include:

- title;
- description;
- todo/in-progress/blocked/done status;
- priority;
- due date/time;
- assignee;
- optional project/client/ticket;
- recurrence;
- overdue/due-soon views.

Recurrence must be a real domain capability rather than generating an infinite set of future rows manually.

---

## 11. Time tracking

Time entries are operational records used to understand work performed.

A time entry should support:

- user;
- date/time or duration;
- description;
- optional Client;
- optional Project;
- optional Task/Ticket where useful;
- billable/non-billable state;
- future rate/billing integration.

Time reporting should eventually support client and project totals.

---

## 12. Ticketing and communications

Tickets will be a core domain, not merely a contact-form table inside the CRM.

The ticket system unifies communication from:

- Microsoft Graph mailboxes;
- public contact forms;
- future portal-originated messages;
- possible future integrations/channels.

### 12.1 Core model

Conceptually:

```text
Ticket
├── brand
├── client (optional until identified)
├── contact (optional until identified)
├── mailbox/source
├── queue
├── subject
├── status
├── priority
├── assigned user/team
├── category
├── source
├── timestamps
└── messages

TicketMessage
├── ticket
├── direction (incoming/outgoing/internal-note where applicable)
├── sender
├── recipients
├── subject where needed
├── text body
├── HTML body
├── provider message identifiers
├── received/sent timestamps
└── attachments
```

The exact schema must be finalised when ticket implementation begins.

### 12.2 Contact form flow

A public contact form should not create a separate siloed `ContactSubmission` workflow that must later be reconciled manually.

Target flow:

```text
Public website form
    ↓
validate / abuse protection
    ↓
create or identify Lead/Contact
    ↓
create Ticket
    ↓
create initial TicketMessage
    ↓
route to appropriate queue
```

The ticket should retain originating brand and form/source metadata.

The implementation should take inspiration from the existing ticket/contact work in `stackedfinds.co.uk` where appropriate, but must be adapted to this platform's multi-brand, client-aware model rather than copied blindly.

### 12.3 Email threading

Incoming provider messages should use reliable provider/internet message identifiers and conversation/thread metadata where available to associate replies with an existing ticket.

Do not depend only on subject-line parsing.

### 12.4 Client auto-association

For an incoming message:

1. inspect sender address;
2. match to a known ClientContact email;
3. attach the ticket to that Contact and Client automatically;
4. expose that client's related knowledge base, credentials, infrastructure, projects and previous tickets in the operator UI.

Unknown senders remain unassigned/prospect contacts until resolved.

### 12.5 Queues

Tickets should support queues such as:

- Support;
- Sales;
- Accounts;
- Vendor/Automated;
- Internal/Monitoring;
- Spam/Quarantine as appropriate.

Queues must be permission-scopeable.

---

## 13. Microsoft Graph mailbox integration

The platform will connect to multiple Microsoft 365 mailboxes, including examples such as:

```text
support@adbwebdesigns.co.uk
support@adbsoftwaresolutions.co.uk
support@adbtechnology.co.uk
accounts@adbwebdesigns.co.uk
```

Additional addresses are expected.

### 13.1 Mailbox abstraction

Do not hard-code Graph logic directly around specific addresses.

A `Mailbox` domain object should eventually include concepts such as:

- Brand;
- email address;
- display name;
- mailbox type (support, accounts, sales, general, etc.);
- provider (`microsoft_graph` initially);
- provider account/tenant configuration;
- enabled state;
- default ticket queue;
- sync cursor/state;
- ingestion rules where needed.

Multiple mailboxes may share one Microsoft 365 tenant/provider configuration.

Certificate/private-key material and provider credentials must use secure configuration/secret storage and must never be committed to the repository.

### 13.2 Background processing

Mailbox synchronisation and message ingestion belong in Celery/background workers, not request-response handlers.

The system should be designed for idempotent processing so a Graph retry does not create duplicate tickets/messages.

### 13.3 Outbound replies

Replies created in the ticket UI should be sent through the correct originating/configured mailbox and persisted as TicketMessages with provider identifiers once sent.

---

## 14. Spam, automation and message classification

Inbound email should not be reduced to a binary spam/not-spam decision.

A target ingestion pipeline is:

```text
Incoming message
    ↓
provider validation / deduplication
    ↓
hard spam/abuse checks
    ↓
sender/contact/client recognition
    ↓
classification
    ├── client/support
    ├── sales enquiry
    ├── accounts/billing
    ├── vendor/automated
    ├── monitoring/system
    ├── newsletter/marketing
    ├── probable spam
    └── unknown
    ↓
queue + priority rules
    ↓
ticket creation/update
```

Vendor or automated mail should generally not be discarded simply because it is non-human. Useful provider notifications can go to a low-priority Vendor/Automated queue.

Spam classification should use deterministic rules first where practical and leave room for more advanced classification later. Do not make an AI dependency foundational unless there is a clear benefit.

---

## 15. Knowledge base

The internal knowledge base is intended to provide structured operational documentation similar in spirit to IT Glue.

A document is either:

- internal; or
- linked to a Client.

Required/likely capabilities include:

- title;
- structured sections/categories;
- Markdown or rich-text content with a controlled representation;
- tags;
- attachments where useful;
- author/editor;
- version history;
- search;
- audit trail;
- permissions and client scope.

The knowledge base is internal by default. Future client-portal publication should require an explicit visibility state and must not expose internal documents accidentally.

---

## 16. Credentials vault

Credentials are structured sensitive records, either internal or client-owned.

Examples include:

- website administrator credentials;
- hosting logins;
- API keys;
- database credentials;
- service accounts;
- tokens;
- licence keys where appropriate.

### Security requirements

- secret values encrypted at rest using a well-reviewed mechanism;
- encryption key stored outside the database/repository;
- reveal permission separate from metadata view permission;
- reveal operations audit logged;
- secrets never written to normal application logs;
- secrets never returned from list endpoints unnecessarily;
- frontend should request reveal only when explicitly required;
- sensitive values excluded from analytics/error-reporting payloads.

Credentials should be linkable to relevant infrastructure or systems without forcing the secret into those records themselves.

---

## 17. Infrastructure inventory

The infrastructure application is structured documentation, not merely free-form notes.

Resources should support client/internal ownership and relationships to one another.

Planned/established resource types include:

- Servers;
- Databases;
- Websites;
- Domains;
- SSL certificates;
- Licences;
- logical Applications;
- Mobile applications;
- APIs/services;
- Bots/automations;
- Email systems/configuration;
- repositories and related metadata where appropriate.

### Logical Application abstraction

A logical Application groups a system that may span several infrastructure components.

For example, one SaaS product may include:

- public web frontend;
- admin frontend;
- Django API;
- PostgreSQL database;
- Redis;
- workers;
- mobile apps;
- domains;
- GitHub repositories;
- licences.

Relationships should be explicit enough to navigate the system from a client/ticket context.

---

## 18. Search

Long-term global/contextual search is a major usability goal.

From a ticket for a known client, an operator should eventually be able to search within that client and obtain relevant results across:

- knowledge-base documents;
- credentials metadata (with reveal still permission-protected);
- infrastructure inventory;
- previous tickets;
- projects;
- project notes;
- contacts.

Search results must obey the same permission scopes as direct resource APIs. Search must never become a path around credential/client access restrictions.

A simple PostgreSQL-backed approach is acceptable initially. Dedicated search infrastructure should only be introduced when justified.

---

## 19. Celery and asynchronous workflows

Celery is the background execution layer for work that should not block web requests.

Expected responsibilities include:

- transactional email delivery;
- Microsoft Graph synchronisation;
- ticket ingestion/classification;
- notifications;
- scheduled/recurring task generation or scheduling;
- publishing/scheduled content actions where appropriate;
- future invoice reminders;
- future integrations and maintenance jobs.

Tasks should be designed for safe retry and idempotency when dealing with external systems.

Do not put ordinary domain logic exclusively inside Celery tasks. Reusable services should contain the business operation; the task should orchestrate its asynchronous execution.

---

## 20. Future client portal

A client portal is planned but not part of the current implementation phase.

Potential future portal capabilities include:

- viewing/opening tickets;
- replying to tickets;
- viewing project status;
- approved shared documents;
- invoices;
- quotes;
- contracts;
- payment links/status;
- carefully selected knowledge-base content.

Client portal users should use the existing identity system and be linked to ClientContact records.

Portal visibility must always be explicit. Internal resources must never become portal-visible merely because they belong to the same client.

---

## 21. Future commercial system

Future planned capabilities include:

### Quotes

- client/contact;
- line items;
- taxes/discounts where needed;
- acceptance status;
- versioning;
- conversion into project/contract/invoice workflow.

### Contracts

- contract templates;
- generated agreement documents;
- client/contact;
- project/quote relationship;
- signature workflow/provider integration;
- immutable signed-document retention.

### Invoicing

- client/contact;
- invoice number;
- line items;
- taxes;
- due date;
- status;
- payment status;
- recurring billing/invoice support where useful;
- links to time/project data where appropriate.

### Stripe payments

Stripe may be used for future card/payment functionality.

The platform should treat Stripe as an external payment provider, retaining local records of provider identifiers and state while verifying webhooks and avoiding storage of raw card details.

These areas are intentionally deferred. Current models may leave reasonable extension points, but should not acquire speculative complexity solely for these future features.

---

## 22. API design principles

The backend uses Django Ninja.

Target API groups should be coherent and domain based. Exact paths may evolve, but conceptually:

```text
/api/auth/...
/api/auth-service/...
/api/sessions/...

/api/public/content/...

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
/api/admin/content/...
/api/admin/staff/...
/api/admin/audit/...
```

Rules:

- schemas are explicit;
- responses should be consistently shaped;
- pagination is consistent for collections;
- errors have predictable contracts;
- permission checks occur in backend handlers/services;
- sensitive fields are opt-in, not returned by default;
- list APIs avoid N+1 database queries;
- public APIs are brand-scoped and read-only except explicit submission endpoints;
- admin APIs are staff-authenticated and permission scoped.

Shared TypeScript API contracts/helpers may live in `packages/api-client/` when genuinely shared across sites.

---

## 23. Data model principles

Before implementing new APIs widely, existing Django models must be reviewed against this plan.

Prefer explicit domain relations over generic untyped key/value stores for core records.

Important principles:

- client/internal scope is deliberate;
- Brand is separate from Client;
- avoid fake clients to represent ADB itself;
- public CaseStudy is separate from operational Project;
- credentials contain/refer to secrets; infrastructure links to credentials rather than duplicating them;
- Contacts are the identity bridge between inbound communications and Clients;
- tickets own communication history;
- leads own sales lifecycle;
- tasks do not require projects;
- future portal visibility is explicit;
- model choices should support permissions without requiring every query to load an unbounded permission graph.

Migrations should be incremental and safe. Existing data compatibility should be considered even while the system is pre-production.

---

## 24. UI/UX principles for the admin platform

The admin application should ultimately be organised around workflows, not merely a one-page-per-model CRUD generator.

Likely top-level areas include:

- Dashboard;
- Tickets;
- Clients;
- CRM/Leads;
- Projects;
- Tasks;
- Time;
- Knowledge Base;
- Credentials;
- Infrastructure;
- Content;
- Staff/Permissions;
- Audit/Security;
- Settings/Integrations.

### Client context

A client detail view should become one of the main navigation hubs, with tabs/sections for contacts, tickets, projects, docs, credentials, infrastructure and other permitted data.

### Ticket workspace

A ticket view should provide contextual client information without requiring the operator to open several unrelated browser pages.

### Permission-aware navigation

The admin frontend should receive enough effective-permission/scope data to avoid presenting actions the current user cannot perform. Backend checks remain authoritative.

---

## 25. Foundational implementation phase

The immediate phase is deliberately focused on making the repository accurately represent the target platform before building major new features.

### 25.1 Remove legacy/template residue

Remove or replace:

- `Project Template` names/descriptions;
- TechWiki-specific types, routes and comments accidentally retained in the ADB admin application;
- duplicate authentication contexts/clients;
- obsolete hard-coded local URLs where environment configuration exists;
- stale public-marketing metadata in the internal admin application;
- other clearly inherited code that no longer represents ADB.

Do not remove useful generic code solely because its history came from another project. Remove or adapt only incorrect domain-specific residue.

### 25.2 Stabilise auth/admin integration

- use one admin AuthContext implementation;
- ensure it consumes the actual `/api/auth/me` response contract correctly;
- keep staff/superuser checks authoritative in Django;
- redirect unauthenticated admin users to the auth frontend safely;
- support return URLs using validated `next` parameters;
- remove production-inappropriate debug logging from auth flows;
- add/update integration-oriented tests around these contracts.

### 25.3 Introduce Brand

Create the canonical Brand model and initial migration/seed strategy.

Do not rely on numeric IDs remaining identical between environments. Initial brands should be identifiable by stable slugs.

### 25.4 Make CMS content brand-aware

Review BlogPost, Testimonial, FAQ and public portfolio/case-study models.

Add explicit Brand relationships and update public/admin APIs so content cannot leak between brands.

### 25.5 Define ownership and permissions

Before adding broad CRUD APIs for the other business domains:

- document/finalise client/internal ownership conventions;
- implement the first backend permission/scoping primitives;
- establish audit-log foundation;
- define how effective permissions are exposed to the admin frontend.

### 25.6 Review existing domain models

Audit every current model in:

- clients;
- CRM;
- tasks;
- credentials;
- knowledge base;
- infrastructure;
- website/content;
- authentication.

Classify each model as:

- keep as-is;
- keep but amend;
- rename/reframe;
- remove before production;
- defer decision.

Do not add broad API/UI implementation until this review is complete.

### 25.7 Update repository documentation

Keep this master plan, architecture docs, AGENTS guidance and README aligned with the actual architecture.

---

## 26. Subsequent implementation roadmap

### Phase 1 — Platform foundations

- legacy/template cleanup;
- auth/admin consolidation;
- Brand model;
- brand-aware CMS;
- permissions/scopes foundation;
- audit-log foundation;
- domain-model review;
- architecture documentation.

### Phase 2 — Core business operations

Build coherent backend APIs and admin UI for:

1. Clients;
2. Contacts;
3. Projects;
4. CRM/Leads;
5. Tasks, including standalone and recurring tasks;
6. Time tracking.

The first objective is a genuinely useful system for running daily work, not merely completing every possible model.

### Phase 3 — Ticketing and communications

- Ticket/TicketMessage domain;
- queues;
- client/contact auto-association;
- Mailbox/provider models;
- Microsoft Graph certificate-based integration;
- Celery ingestion;
- threading/deduplication;
- custom spam/filtering/classification;
- ticket reply/send flow;
- contact forms creating tickets and leads;
- queue/client permission enforcement.

### Phase 4 — Documentation and infrastructure workspace

- internal knowledge base;
- credential vault;
- credential reveal auditing;
- structured infrastructure inventory;
- relationships between systems, credentials and clients;
- client-context search.

### Phase 5 — Public websites

The public websites can be developed in parallel where useful once the content contracts are stable, but the key shared integration work is:

- brand-aware blog;
- testimonials;
- FAQs;
- public case studies if CMS-managed;
- contact/ticket integration.

Main marketing pages remain code-owned.

### Phase 6 — Commercial/client-facing features

Deferred until the internal platform is mature:

- client portals;
- quotes;
- contracts/signatures;
- invoicing;
- recurring billing workflows;
- Stripe payments;
- client-facing project/ticket/document views.

---

## 27. Security principles

Security-sensitive areas include authentication, permissions, credentials, email integrations and future financial/client portal features.

Rules include:

- least privilege by default;
- backend-enforced authorisation;
- no secrets in Git;
- no secrets in normal logs;
- no credential secret in list/search responses;
- audit sensitive actions;
- use established cryptographic/authentication libraries;
- validate redirect URLs;
- protect state-changing requests against CSRF where session cookies are used;
- secure cookies in production;
- rate limit authentication and abuse-prone public endpoints;
- verify external webhooks/providers;
- make background ingestion idempotent;
- never rely on hidden UI as access control;
- tests for permission boundaries are mandatory as restricted APIs are added.

---

## 28. Testing and quality expectations

Every new domain should be developed with tests rather than adding tests only after the platform is feature complete.

Priority testing areas:

- authentication flows;
- permission and scope boundaries;
- credential reveal restrictions;
- brand filtering of public content;
- client/contact matching;
- ticket threading/idempotency;
- external Graph integration boundaries using mocks/fakes;
- recurring task behaviour;
- future payment/webhook verification.

Repository lint/type/test rules must not be weakened to make features pass.

---

## 29. Important non-goals and anti-patterns

Do not:

- create separate Django backends for each public brand;
- duplicate the CMS per brand;
- turn the CMS into a generic page builder;
- force all tasks to belong to projects;
- treat internal ADB as a fake Client;
- use Brand as a substitute for client/internal ownership;
- merge operational Project and public CaseStudy models;
- store plaintext credentials directly on infrastructure models;
- implement authorisation only in React;
- give every internal user superuser access because the team is currently small;
- hard-code every mailbox as bespoke Graph logic;
- treat every automated/vendor email as spam;
- create separate contact-form and email communication silos instead of tickets;
- build speculative Stripe/client-portal complexity during the foundation phase.

---

## 30. Current architectural statement

The concise definition of the platform is:

> **The ADB Business Platform is one shared operational system serving multiple ADB brands. Public-facing editorial content is brand-scoped; operational resources are client-scoped or internal; fine-grained permissions constrain staff by capability and scope; communications unify into tickets and are enriched automatically with client context.**

Any substantial future architectural decision should be checked against that statement and this document.

# Current State and Foundation Checklist

This document records the implementation state of the ADB Business Platform foundation phase. Read it together with:

- `docs/PLATFORM_MASTER_PLAN.md` — canonical product and architecture plan;
- `docs/PERMISSIONS_AND_ACCESS_MODEL.md` — canonical authorisation and object-scope design;
- `docs/DOMAIN_MODEL_AUDIT.md` — audit of the existing Django domain models.

The master plan describes the intended architecture. This document tracks what currently exists and the ordered cleanup/review work required before broad feature development.

## 1. Current application structure

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

The monorepo structure, pnpm workspace, per-application CI and Dockerfiles were established before this foundation phase.

## 2. Backend status

### Authentication

Authentication is currently the most mature backend subsystem.

Existing capabilities include:

- custom User model;
- email/password authentication;
- email verification;
- password reset;
- TOTP two-factor authentication;
- recovery codes;
- WebAuthn/passkeys;
- authentication logs;
- tracked sessions/devices;
- login/register/2FA rate limiting;
- staff/superuser-only `/api/auth` endpoints;
- general `/api/auth-service` account endpoints.

Foundation work completed so far:

- platform/template naming has been removed from the main API/settings;
- the legacy eBay-specific User field has been removed;
- the staff `/api/auth/me` response now exposes capability permissions and object scopes;
- verbose staff-auth stage logging has been removed;
- request bodies are no longer logged by the top-level API validation/error handlers;
- admin logout now uses the CSRF-safe API helper;
- admin/auth return URL configuration has been centralised and validated.

Remaining foundation work:

- remove remaining verbose logging from the general auth service/API client;
- continue reviewing API response conventions where practical;
- move verification/reset email delivery behind the future Celery/email service;
- verify all session/cookie/CORS/CSRF flows in local and production domain arrangements;
- strengthen automated auth/admin integration tests.

### Website/content app

Existing content models include:

- Portfolio;
- Testimonial;
- BlogCategory;
- BlogTag;
- BlogPost;
- FAQ;
- FAQCategory.

The models now support explicit Brand assignment. Public content APIs require a Brand slug and scope queries accordingly. Contact submissions also carry the originating Brand into CRM Leads.

The Django admin exposes Brand assignment. The custom Next.js content administration UI and its Django Ninja CRUD API still need to expose and persist Brand assignment consistently.

Portfolio remains public case-study content and is explicitly separate from operational `clients.Project`. A future model rename to `CaseStudy` remains optional and should only be performed when the migration/API/UI churn is justified.

Remaining foundation work:

- make custom admin CRUD fully Brand-aware;
- add brand assignment/filtering to the custom admin UI;
- populate Brand metadata accurately in admin API output;
- expand cross-brand isolation tests beyond the initial testimonial coverage;
- replace contact-submission-only behaviour with the future ticket/lead ingestion architecture when ticketing is implemented.

### Clients app

Existing data models and Django admin exist for client/business records. The admin Next.js client page is currently mostly a placeholder and the general business API surface is incomplete.

The model audit establishes that Client is the organisation/account root and ClientContact is the individual identity used for future email matching and portal access.

Future implementation must provide:

- improved Client field semantics;
- ClientContact primary/billing/technical contact flags;
- normalised contact email identity matching;
- future portal relationship extension points;
- client active/archive lifecycle;
- explicit client/internal operational ownership without a fake Internal Client.

### CRM app

Existing CRM models/admin primarily cover lead concepts. General admin APIs/UI are incomplete.

`Lead` now supports an originating Brand. CRM remains the sales pipeline and must remain separate from support ticketing.

Future work includes:

- linked communication/tickets;
- lead ownership/assignee;
- lead-to-client conversion;
- value/currency where useful;
- richer source metadata.

### Infrastructure app

The infrastructure model is broad and already contains structured records for servers, databases, websites, domains, certificates and other asset/application types.

The admin UI currently has an infrastructure landing page but several linked detail routes are not implemented.

The initial domain audit keeps the existing concepts but defers a deeper field-by-field redesign until the infrastructure workspace is implemented. Before then the platform must:

- apply client/internal ownership consistently;
- reference credentials rather than duplicate secrets;
- preserve logical Application as a grouping abstraction;
- modernise static provider/OS choices where appropriate;
- enforce permission boundaries and client scope.

### Credentials app

Credential models/admin exist, but the current secret fields remain plaintext legacy storage and are explicitly not production-ready.

The foundation now defines separate Django permissions for revealing and copying secrets. The final vault still requires:

- encrypted-at-rest secret storage and deliberate key management;
- client/internal ownership;
- metadata-only list/search APIs;
- audited secret reveal;
- related infrastructure/application references;
- safe rotation/expiry/export behaviour.

Do not put production credentials into the current table before this work is complete.

### Knowledge base app

Knowledge-base models/admin exist. The custom admin frontend is not yet a complete IT Glue-style documentation workspace.

Foundation requirements remain:

- client/internal ownership;
- sections/categories/tags;
- author/editor metadata;
- reliable document version history;
- permission scope;
- search strategy;
- future portal visibility that is explicit and private by default.

### Tasks app

Task-related models/admin exist, but the operational task product is incomplete.

The model audit confirms the target behaviour:

- tasks may be project-linked, client-linked, ticket-linked or standalone;
- project/list membership must not be mandatory;
- internal standalone tasks are valid;
- recurring tasks are required, including monthly invoice reminders;
- assignments and permissions must support multiple staff users over time.

### Platform core

A new `apps.core` domain now contains:

- `Brand` — first-class identity for the three public ADB brands;
- `AuditEvent` — append-only audit foundation for sensitive/important actions.

The initial migration deterministically seeds:

- `adb-software-solutions`;
- `adb-web-designs`;
- `adb-technology`.

### Access control

A new `apps.access_control` domain provides the first object-scope layer that complements Django's capability permissions.

Current models/helpers include:

- `StaffAccessProfile`;
- `ClientAccessGrant`;
- all-clients versus selected-client scope;
- a reserved all-ticket-queues flag for the future ticket domain;
- reusable `can_access_client` and `scope_clients_for_user` policy helpers;
- tests for selected-client scope, global client scope and superuser bypass.

TicketQueue grants are intentionally deferred until the ticket domain exists rather than inventing a generic ACL table prematurely.

### Celery/background work

Celery configuration and development worker commands already exist. Business background workflows remain incomplete.

Future Celery responsibilities include:

- transactional email;
- Microsoft Graph ingestion/sync;
- ticket classification/routing;
- notifications;
- recurring/scheduled task workflows;
- other integration jobs.

Business logic should live in reusable services; Celery tasks should orchestrate asynchronous execution.

## 3. Admin frontend status

Existing routes include areas for dashboard, clients, projects, leads, time tracking, credentials, content and infrastructure.

The content-management screens are considerably more complete than the other business-operation screens.

Foundation changes already made include:

- removed duplicate TechWiki-derived auth implementation;
- corrected the active AuthContext to the real `/api/auth/me` response;
- centralised API/auth URLs;
- removed stale marketing metadata;
- added CSRF-safe mutating API requests;
- exposed effective permissions and client/ticket-queue scope in the AuthContext;
- added a `hasPermission()` helper for future UI affordances.

Remaining issues include placeholder business pages, missing infrastructure detail routes, brand assignment in CMS forms and actual permission-driven navigation/action affordances.

## 4. Auth frontend status

Existing routes/capabilities include login, signup, logout, email verification, password reset, passkeys, TOTP, account security and session/device management.

Foundation changes already made include updated redirect allow-list/defaults for all ADB applications and removal of verbose logging from the AuthContext.

Remaining work:

- remove verbose diagnostic logging from the underlying API utility;
- review security-sensitive API types;
- verify CSRF/session behaviour in local and production domain arrangements;
- ensure all return flows use validated `next` URLs;
- later support client portal users through this same identity system.

## 5. Foundational domain decisions

### Brand

Implemented as first-class `apps.core.Brand`. Brand is independent of Client ownership.

### Ownership

The architectural rule is decided: operational resources are either client-owned or explicitly internal. The reusable model/validation pattern has not yet been implemented across every operational domain.

### Permissions

The permission architecture is documented in `PERMISSIONS_AND_ACCESS_MODEL.md`.

Capability uses Django Permission/Group primitives. Object scope is independent. Client scope has an initial concrete implementation. TicketQueue scope will be implemented with ticketing. Credential reveal/copy are explicit sensitive permissions.

### Audit logging

`apps.core.AuditEvent` is the initial append-only audit foundation. Sensitive actions still need to begin emitting events as their APIs are implemented.

### API conventions

Still to standardise progressively:

- response contracts;
- error representation;
- collection pagination;
- reusable capability checks;
- reusable queryset scoping;
- secret-field handling.

## 6. Foundation branch checklist

### Legacy/template cleanup

- [x] Add canonical platform master plan.
- [x] Update root AGENTS guidance to make the master plan authoritative.
- [x] Remove duplicate TechWiki admin AuthContext/types/exports.
- [x] Correct active admin authentication response handling.
- [x] Centralise admin API/auth frontend URLs.
- [x] Remove stale public marketing metadata from the internal admin root layout.
- [x] Update auth redirect configuration for the current multi-site local layout.
- [x] Remove `Project Template` API/site names from Django settings/router.
- [ ] Search for remaining TechWiki/wiki-specific identifiers outside intentionally unrelated history/docs.
- [ ] Search for stale `auth-frontend`, `admin-website`, old port and old path references.
- [ ] Remove or gate remaining verbose auth debug logging.
- [ ] Review stale comments and TODOs that describe superseded architecture.

### Authentication/admin consolidation

- [ ] Add/adjust admin authentication tests for the real backend contract.
- [x] Ensure admin logout uses CSRF handling.
- [x] Preserve staff/superuser enforcement on `/api/auth`.
- [x] Ensure admin login preserves a validated return URL.
- [ ] Complete production-domain session cookie/CORS/CSRF review and tests.
- [x] Define and expose the initial effective-permission/scope payload.

### Brand and CMS

- [x] Decide Brand app/module location.
- [x] Add Brand model/migration.
- [x] Add deterministic initial Brand data strategy.
- [x] Add Brand administration.
- [x] Make testimonials brand-aware at model/public-API level.
- [x] Make FAQs brand-aware at model/public-API level.
- [x] Make blog content brand-aware at model/public-API level.
- [x] Reframe public Portfolio as separate public case-study content while retaining its existing name for now.
- [x] Update public content APIs to scope by Brand.
- [ ] Update custom content admin API/UI for Brand assignment/filtering.
- [x] Add initial test proving cross-brand content isolation.
- [ ] Expand cross-brand tests across content types.

### Permissions and audit

- [x] Review existing User/Group/custom-group implementation.
- [x] Document role versus direct-permission representation.
- [x] Design and implement initial Client access grants.
- [x] Document TicketQueue access strategy; implementation deferred until ticketing.
- [x] Define credential metadata/reveal/copy permission boundary.
- [x] Add initial reusable backend client-scope policy helpers.
- [x] Add audit-event model/service foundation.
- [x] Add initial client-scope tests for denied/allowed paths.
- [ ] Add capability+scope enforcement to each operational API as those APIs are implemented.
- [ ] Begin emitting AuditEvents from sensitive actions.

### Existing model audit

- [x] Authentication models.
- [x] Client/ClientContact/Project/Time models.
- [x] CRM/Lead models.
- [x] Task models.
- [x] Credential models and current encryption state.
- [x] Knowledge-base models/versioning.
- [x] Initial infrastructure model/relationship audit; deeper implementation audit deferred.
- [x] Content models.

The decisions are recorded in `docs/DOMAIN_MODEL_AUDIT.md`.

### Documentation

- [ ] Reconcile/update historical `ADB_SOFTWARE_SOLUTIONS_BUILD_PLAN.md`.
- [ ] Reconcile/update historical `DJANGO_ARCHITECTURE.md`.
- [ ] Update README once foundation architecture changes land.
- [x] Add canonical permissions/access-control document.
- [x] Add domain model audit document.
- [x] Keep this checklist current as work is completed.

## 7. Next phases after foundation

After the checklist above is sufficiently complete, implement in this order unless a new explicit decision changes it:

1. Clients and Contacts.
2. Projects.
3. CRM/Leads.
4. Tasks/recurrence.
5. Time tracking.
6. Tickets/queues.
7. Microsoft Graph Mailboxes and background sync.
8. Contact forms -> tickets/leads.
9. Spam/classification/routing.
10. Knowledge base.
11. Credentials vault.
12. Infrastructure workspace.
13. Client-context/global search.
14. Public-site integration with the stable brand-aware CMS.
15. Future client portals/commercial features after the internal platform is mature.

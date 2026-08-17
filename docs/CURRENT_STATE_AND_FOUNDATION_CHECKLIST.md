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

Existing capabilities include custom users, email/password authentication, email verification, password reset, TOTP two-factor authentication, recovery codes, WebAuthn/passkeys, authentication logs, tracked sessions/devices, rate limiting, staff `/api/auth` endpoints and general `/api/auth-service` account endpoints.

Foundation work completed so far includes removal of template naming and the legacy eBay-specific User field, exposing staff capability permissions/object scopes, reducing verbose staff-auth logging, removing request bodies from top-level validation/error logs, CSRF-safe admin logout and centralised/validated return URL configuration.

Remaining foundation work:

- remove remaining verbose logging from the general auth service/API client;
- continue reviewing API response conventions where practical;
- move verification/reset email delivery behind the future Celery/email service;
- verify session/cookie/CORS/CSRF flows in local and production domain arrangements;
- strengthen automated auth/admin integration tests.

### Website/content app

Existing content models include Portfolio, Testimonial, BlogCategory, BlogTag, BlogPost, FAQ and FAQCategory.

The models support explicit Brand assignment. Public content APIs require a Brand slug and scope queries accordingly. Contact submissions carry the originating Brand into CRM Leads. The Django admin exposes Brand assignment and the Django Ninja administration API accepts `brand_ids` and returns `brand_slugs`.

The custom Next.js CMS is being brought onto that contract. A reusable Brand selector has been introduced and testimonial administration now supports required multi-brand assignment, editing and brand filtering. Blog, FAQ and portfolio administration still need the same treatment before this foundation item is complete.

Portfolio remains public case-study content and is explicitly separate from operational `clients.Project`. A future model rename to `CaseStudy` remains optional and should only be performed when the migration/API/UI churn is justified.

### Clients app

Existing data models and Django admin exist for client/business records. The admin Next.js client page is currently mostly a placeholder and the general business API surface is incomplete.

The model audit establishes that Client is the organisation/account root and ClientContact is the individual identity used for future email matching and portal access. The first operational phase after foundation will implement these concepts properly.

### CRM app

Existing CRM models/admin primarily cover lead concepts. `Lead` supports an originating Brand. CRM remains the sales pipeline and must remain separate from support ticketing.

### Infrastructure app

The infrastructure model is broad and already contains structured records for servers, databases, websites, domains, certificates and other asset/application types. A deeper field-by-field redesign remains deferred until the infrastructure workspace is implemented.

### Credentials app

Credential models/admin exist, but current secret fields remain plaintext legacy storage and are explicitly not production-ready. Separate Django permissions for viewing metadata, revealing secrets and copying secrets have been established. Do not put production credentials into the current table before the encrypted vault work is complete.

### Knowledge base app

Knowledge-base models/admin exist. The custom admin frontend is not yet a complete IT Glue-style documentation workspace. Client/internal ownership, versioning, permission scope, search and future portal visibility remain required.

### Tasks app

Task-related models/admin exist, but the operational task product is incomplete. Tasks may be project-linked, client-linked, ticket-linked or standalone; project/list membership must not be mandatory; internal standalone and recurring tasks are valid requirements.

### Platform core

`apps.core` contains first-class `Brand` and append-only `AuditEvent` foundations. Initial data deterministically seeds ADB Software Solutions, ADB Web Designs and ADB Technology.

### Access control

`apps.access_control` complements Django capability permissions with object scope. Current foundations include `StaffAccessProfile`, `ClientAccessGrant`, all-clients versus selected-client scope, reusable client policy helpers and tests. TicketQueue grants remain deferred until the ticket domain exists.

### Celery/background work

Celery configuration and development worker commands exist. Future responsibilities include transactional email, Microsoft Graph ingestion/sync, ticket classification/routing, notifications and recurring task workflows. Business logic belongs in reusable services; Celery tasks orchestrate asynchronous execution.

## 3. Admin frontend status

Existing routes include dashboard, clients, projects, leads, time tracking, credentials, content and infrastructure. Content administration is substantially more complete than the other operational screens.

Foundation work has removed the duplicate TechWiki auth implementation, corrected the real AuthContext contract, centralised API/auth URLs, removed stale marketing metadata, added CSRF-safe mutations, exposed effective permissions/scopes and added `hasPermission()` for UI affordances.

The CMS now has a reusable brand-selection primitive. Testimonial CRUD uses it and can filter the list by Brand. Blog, FAQ and portfolio screens remain to migrate to the same pattern.

## 4. Auth frontend status

Existing capabilities include login, signup, logout, email verification, password reset, passkeys, TOTP, account security and session/device management. Redirect configuration supports all current ADB applications. Remaining work includes diagnostic-log cleanup, security-sensitive type review, production cookie/session verification and validated return-flow coverage.

## 5. Foundational domain decisions

### Brand

Implemented as first-class `apps.core.Brand`. Brand is independent of Client ownership.

### Ownership

Operational resources are either client-owned or explicitly internal. The reusable model/validation pattern has not yet been implemented across every operational domain.

### Permissions

Capability uses Django Permission/Group primitives. Object scope is independent. Client scope has an initial concrete implementation. TicketQueue scope will be implemented with ticketing. Credential reveal/copy are explicit sensitive permissions.

### Audit logging

`apps.core.AuditEvent` is the initial append-only audit foundation. Sensitive actions still need to emit events as their APIs are implemented.

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
- [x] Search for remaining TechWiki/wiki-specific identifiers outside intentionally unrelated history/docs.
- [x] Search for stale `auth-frontend` and `admin-website` path references.
- [ ] Search for stale old-port references and confirm intentional development ports.
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
- [x] Add reusable Brand selector to the custom admin frontend.
- [x] Make testimonial custom-admin CRUD and filtering Brand-aware.
- [ ] Make blog custom-admin CRUD and filtering Brand-aware.
- [ ] Make FAQ custom-admin CRUD and filtering Brand-aware.
- [ ] Make portfolio custom-admin CRUD and filtering Brand-aware.
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

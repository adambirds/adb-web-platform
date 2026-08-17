# Current State and Foundation Checklist

This document records the implementation state at the start of the ADB Business Platform foundation phase. Read it together with `docs/PLATFORM_MASTER_PLAN.md`.

The master plan describes the intended architecture. This document describes what currently exists and the ordered cleanup/review work needed before broad feature development.

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

Known foundation work:

- remove stale Project Template naming;
- consolidate API response conventions where practical;
- keep staff/admin auth and general account auth responsibilities explicit;
- remove production-inappropriate diagnostic logging from the auth frontend/backend where present;
- review verification/reset email delivery and move asynchronous delivery behind the platform's Celery/email service when that service is implemented;
- verify return URL handling across admin/auth/public applications;
- add permission/effective-access data after the permission foundation is defined.

### Website/content app

Existing content models include:

- Portfolio;
- Testimonial;
- BlogCategory;
- BlogTag;
- BlogPost;
- FAQ;
- FAQCategory.

Existing Django Ninja APIs include public content, contact submission and substantial admin CRUD for content.

Existing admin UI includes substantial screens for:

- blog;
- portfolio;
- testimonials;
- FAQs.

Known foundation work:

- make content Brand-aware;
- determine whether `Portfolio` becomes/reframes as public CaseStudy;
- keep operational Project separate from public CaseStudy;
- ensure categories/tags are scoped appropriately where needed;
- ensure public APIs require/derive Brand and cannot leak cross-brand content;
- decide whether the Django app remains named `website` or is renamed to `content` after migration impact review;
- replace contact-submission-only thinking with the future ticket/lead ingestion architecture.

### Clients app

Existing data models and Django admin exist for client/business records. The admin Next.js client page is currently mostly a placeholder and the general business API surface is incomplete.

Foundation review must determine:

- final Client fields;
- ClientContact capabilities and email identity matching;
- primary/billing/technical contact flags;
- future portal relationship extension points;
- client active/archive lifecycle;
- internal ownership must not be represented as a fake Client.

### CRM app

Existing CRM models/admin primarily cover lead concepts. General admin APIs/UI are incomplete.

Foundation review must align CRM with:

- Lead sales lifecycle;
- originating Brand;
- source/channel;
- linked communication/tickets;
- lead-to-client conversion;
- separation between sales pipeline and support ticketing.

### Infrastructure app

The infrastructure model is broad and already contains structured records for many areas such as servers, databases, websites, domains, certificates and other asset types.

The admin UI currently has an infrastructure landing page but several linked detail routes are not implemented.

Foundation review must:

- apply client/internal ownership consistently;
- review every existing model and relationship;
- ensure credentials are referenced rather than secrets duplicated on infrastructure rows;
- keep logical Application as a useful grouping abstraction;
- identify outdated provider/OS/static choice lists that should become extensible or modernised;
- define permission boundaries;
- avoid implementing broad UI until the model audit is complete.

### Credentials app

Credential models/admin exist, but the final secure vault behaviour and admin UI are incomplete.

Foundation requirements:

- review current encryption implementation rather than assuming it is production-ready;
- separate metadata-view from secret-reveal permissions;
- audit secret reveals;
- never return secrets in list/search APIs;
- link credentials to client/internal ownership and related systems;
- define secure key-management/configuration expectations.

### Knowledge base app

Knowledge-base models/admin exist. The custom admin frontend is not yet a complete IT Glue-style documentation workspace.

Foundation requirements:

- client/internal ownership;
- categories/sections/tags;
- document version history;
- permission scope;
- search strategy;
- future portal visibility must be explicit and default-private.

### Tasks app

Task-related models/admin exist, but the operational task product is incomplete.

Required target behaviour:

- tasks may be project-linked, client-linked, ticket-linked or standalone;
- internal standalone tasks are valid;
- recurring tasks are required, including examples such as monthly invoice reminders;
- assignments and permissions must support more than one staff user;
- do not force Project membership.

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

Existing routes include areas for:

- dashboard;
- clients;
- projects;
- leads;
- time tracking;
- credentials;
- content/blog;
- content/portfolio;
- content/testimonials;
- content/FAQs;
- infrastructure.

The content-management screens are considerably more complete than the other business-operation screens.

Known foundation issues at the start of this branch included:

- a duplicate TechWiki-derived auth implementation under `src/lib/auth`;
- the active admin AuthContext assuming the wrong `/api/auth/me` response shape;
- hard-coded localhost auth/API URLs;
- stale marketing-site metadata in the internal admin app;
- placeholder business pages whose backend APIs do not yet exist;
- infrastructure links pointing at routes not yet implemented.

The foundation branch has begun removing these issues. Do not recreate the deleted TechWiki auth abstraction.

## 4. Auth frontend status

Existing routes/capabilities include:

- login;
- signup;
- logout;
- email verification;
- forgot/reset password;
- passkey setup/login;
- TOTP setup;
- account security dashboard;
- passkey management;
- password change;
- session/device management.

Known foundation work:

- align redirect allow-list/defaults with all current ADB application ports/domains;
- remove diagnostic logging before production;
- review API types and avoid unnecessary `unknown`/untyped security-sensitive response handling;
- verify CSRF/session behaviour in local and production domain arrangements;
- ensure admin return flows use validated `next` URLs;
- eventually accommodate future client portal users using the same identity system rather than a duplicate auth application.

## 5. Required foundational domain decisions

The following decisions must be completed before broad business CRUD implementation:

### Brand

Create a first-class Brand domain with stable slugs for:

- `adb-software-solutions`;
- `adb-web-designs`;
- `adb-technology`.

Brand is not Client ownership.

### Ownership

Define a consistent client/internal ownership strategy for operational resources.

Do not use `client = NULL` ambiguously without domain validation, and do not create a fake internal Client.

### Permissions

Implement permission primitives, role grouping and resource scope.

At minimum, design scope for:

- features/actions;
- Clients;
- ticket queues;
- credential reveal;
- staff/permission administration.

### Audit logging

Add an audit foundation before credential reveal or fine-grained permission administration is considered complete.

### API conventions

Define and apply consistent:

- response contracts;
- error representation;
- collection pagination;
- staff-auth enforcement;
- permission checks;
- query scoping;
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
- [ ] Remove `Project Template` API/site names from Django settings/router.
- [ ] Search for remaining TechWiki/wiki-specific identifiers outside intentionally unrelated history/docs.
- [ ] Search for stale `auth-frontend`, `admin-website`, old port and old path references.
- [ ] Remove or gate verbose auth debug logging.
- [ ] Review stale comments and TODOs that describe superseded architecture.

### Authentication/admin consolidation

- [ ] Add/adjust admin authentication tests for the real backend contract.
- [ ] Confirm admin logout includes required CSRF handling.
- [ ] Confirm non-staff authenticated users cannot access admin APIs.
- [ ] Confirm admin login preserves a validated return URL.
- [ ] Review session cookie/CORS/CSRF production-domain configuration.
- [ ] Define future effective-permission payload for admin bootstrap/current-user API.

### Brand and CMS

- [ ] Decide Brand app/module location after existing model review.
- [ ] Add Brand model/migration.
- [ ] Add deterministic initial Brand data strategy.
- [ ] Add Brand administration.
- [ ] Make testimonials brand-aware.
- [ ] Make FAQs brand-aware.
- [ ] Make blog content brand-aware.
- [ ] Decide public Portfolio -> CaseStudy direction.
- [ ] Update public content APIs to scope by brand.
- [ ] Update content admin UI for brand assignment/filtering.
- [ ] Add tests proving cross-brand content isolation.

### Permissions and audit

- [ ] Review existing User/Group/custom-group implementation.
- [ ] Design role versus direct-permission representation.
- [ ] Design Client access grants.
- [ ] Design TicketQueue access grants.
- [ ] Define credential metadata/reveal permissions.
- [ ] Define reusable backend policy/query-scope helpers.
- [ ] Add audit-event model/service.
- [ ] Add tests for denied and allowed paths.

### Existing model audit

- [ ] Authentication models.
- [ ] Client/ClientContact/Project/Time models.
- [ ] CRM/Lead models.
- [ ] Task models.
- [ ] Credential models and encryption.
- [ ] Knowledge-base models/versioning.
- [ ] Infrastructure models/relationships.
- [ ] Content models.

For each model record one of: keep, amend, rename/reframe, remove, defer.

### Documentation

- [ ] Reconcile/update historical `ADB_SOFTWARE_SOLUTIONS_BUILD_PLAN.md`.
- [ ] Reconcile/update historical `DJANGO_ARCHITECTURE.md`.
- [ ] Update README once foundation architecture changes land.
- [ ] Keep this checklist current as work is completed.

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

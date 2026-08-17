# Current State and Foundation Checklist

This document records the implementation state of the ADB Business Platform foundation phase. It is an implementation companion to the canonical architecture documents:

- `docs/PLATFORM_MASTER_PLAN.md` — product vision and target architecture;
- `docs/PERMISSIONS_AND_ACCESS_MODEL.md` — authorisation and object-scope rules;
- `docs/DOMAIN_MODEL_AUDIT.md` — decisions from the existing Django model review.

The master plan describes what the platform is intended to become. This file records what currently exists, what has been completed during the foundation phase, and what must still happen before broad business-feature development begins.

## 1. Repository structure

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

The repository is a pnpm workspace. Each browser-facing application remains independently buildable and deployable, while shared frontend/tooling code belongs under `packages/`.

The shared Django backend is the source of truth for authentication, permissions, CMS content, business data, and future operational APIs.

## 2. Foundation decisions already made

### Brand

`apps.core.Brand` is the first-class identity for the public ADB brands:

- ADB Software Solutions;
- ADB Web Designs;
- ADB Technology.

Brand is deliberately separate from Client ownership. A resource can belong to a Brand, a Client, both, or neither depending on its domain purpose.

### Operational ownership

Operational resources must be either:

- client-owned; or
- explicitly internal.

Do not create a fake "Internal Client" merely to satisfy a foreign key. Each operational domain should represent internal ownership deliberately when that domain is implemented.

### Permissions

Django permissions/groups define capabilities such as `view`, `add`, `change`, `delete`, and sensitive custom capabilities. Object scope is independent of capability.

Current object-scope foundations include:

- `StaffAccessProfile`;
- all-clients versus selected-client access;
- `ClientAccessGrant`;
- reusable client-scope policy helpers;
- superuser bypass behaviour.

Ticket-queue scope remains deferred until the ticket domain exists.

### Audit

`apps.core.AuditEvent` is the append-only audit foundation. Sensitive APIs should emit audit events as they are implemented. Credential reveal/copy, permission changes, ticket assignment changes, and later financial actions are expected audit targets.

### Public content

Static marketing/service pages are code-owned. CMS content is limited to dynamic content that benefits from administration:

- blog posts/categories/tags;
- testimonials;
- FAQs/categories;
- public case studies/Portfolio.

All CMS content is explicitly Brand-aware.

## 3. Authentication and account system

Authentication remains the most mature subsystem.

Existing capabilities include:

- custom User model;
- email/password authentication;
- email verification;
- password reset;
- TOTP two-factor authentication;
- recovery codes;
- WebAuthn/passkeys;
- authentication/security logs;
- tracked sessions/devices;
- login/register/2FA rate limiting;
- staff-only administration authentication endpoints;
- general account/authentication endpoints;
- account-security UI for passwords, 2FA, passkeys, and sessions.

Foundation work completed:

- [x] Remove duplicate TechWiki-derived admin authentication implementation.
- [x] Correct the active admin AuthContext to the real backend response contract.
- [x] Preserve staff/superuser enforcement on the administration auth API.
- [x] Centralise admin API/auth application URLs.
- [x] Validate return URLs used by admin -> auth flows.
- [x] Ensure admin logout uses CSRF-aware API handling.
- [x] Expose effective capability permissions and object scopes to the admin frontend.
- [x] Add frontend `hasPermission()` helper for UI affordances.
- [x] Remove template/eBay-specific User residue identified during the first audit.
- [x] Remove public marketing metadata from the internal admin application.

Remaining authentication foundation work:

- [ ] Remove remaining verbose diagnostic logging from the general auth API utility.
- [ ] Tighten security-sensitive frontend API types where practical.
- [ ] Verify cookie, CSRF, CORS and session behaviour against the eventual production-domain arrangement.
- [ ] Strengthen admin/auth integration tests around redirects and authenticated state.
- [ ] Move transactional verification/reset email delivery behind the future email/Celery service when that service is implemented.

## 4. Brand-aware CMS

Backend foundation completed:

- [x] Add Brand relationships to Portfolio/case studies.
- [x] Add Brand relationships to testimonials.
- [x] Add Brand relationships to blog posts.
- [x] Add Brand relationships to blog categories.
- [x] Add Brand relationships to blog tags.
- [x] Add Brand relationships to FAQs.
- [x] Add Brand relationships to FAQ categories.
- [x] Require Brand context on public CMS APIs.
- [x] Return `brand_slugs` from CMS API representations.
- [x] Accept `brand_ids` in CMS administration mutations.
- [x] Add `/api/admin/brands` for administration UI use.
- [x] Enforce Django capability permissions on CMS administration endpoints.

Custom administration UI foundation completed:

- [x] Add reusable `BrandSelector` component.
- [x] Make testimonial creation/editing Brand-aware.
- [x] Add testimonial Brand filtering/display.
- [x] Make FAQ and FAQ-category creation/editing Brand-aware.
- [x] Add FAQ/category Brand filtering/display.
- [x] Make Portfolio/case-study creation/editing Brand-aware.
- [x] Add Portfolio Brand filtering/display.
- [x] Make blog post creation/editing Brand-aware.
- [x] Make blog category/tag creation/editing Brand-aware.
- [x] Add blog/category/tag Brand filtering/display.

CMS tests:

- [x] Test testimonial public Brand isolation.
- [x] Test blog public Brand isolation.
- [x] Test FAQ public Brand isolation.
- [x] Test Portfolio public Brand isolation.
- [x] Test CMS capability denial/allow behaviour.
- [x] Test multi-brand testimonial persistence.
- [x] Test multi-brand blog-post persistence.
- [x] Test multi-brand FAQ persistence.
- [x] Test multi-brand Portfolio persistence.
- [x] Test invalid Brand IDs are rejected.

Remaining CMS refinement, not blocking the first operational phase:

- [ ] Consider shared Brand-aware category/tag selection helpers to reduce repeated UI code.
- [ ] Validate that selected post/FAQ categories are compatible with the resource Brand set.
- [ ] Decide whether `Portfolio` should eventually be renamed to `CaseStudy`; do not perform migration churn without a clear benefit.
- [ ] Replace direct contact-submission handling with ticket/lead ingestion when ticketing exists.

## 5. Clients and contacts

Existing Django models/admin provide an initial data structure, but the custom admin page and operational API are not yet complete.

Canonical decisions:

- Client is the organisation/account root.
- ClientContact represents individual people belonging to the client.
- Contact email addresses will later drive automatic ticket/client matching.
- Client records must support active/archive lifecycle rather than destructive deletion for ordinary business use.
- Contacts need explicit primary/billing/technical semantics where useful.
- Future client portal identities should link to contacts rather than create a second customer-data model.

This is the first broad operational phase after foundations.

## 6. CRM and leads

Existing CRM models primarily cover Lead concepts. `Lead` supports an originating Brand.

CRM remains the sales pipeline and must not become the support-ticket domain.

Future work includes:

- lead owner/assignee;
- richer source metadata;
- potential value/currency fields;
- linked communications/tickets;
- lead-to-client conversion;
- contact deduplication/matching.

## 7. Projects, tasks and time

Operational `Project` is separate from public Portfolio/case-study content.

Projects represent real work performed internally or for clients. Tasks may be associated with projects but must not require a project.

Target task behaviour includes:

- project-linked tasks;
- client-linked tasks;
- future ticket-linked tasks;
- standalone internal tasks;
- recurrence rules;
- due dates/priorities;
- staff assignment;
- recurring business operations such as monthly invoice reminders.

Time entries will later connect staff work to clients/projects and eventually billing/invoicing where appropriate.

## 8. Tickets and communications

Ticketing has not yet been implemented and remains a major later phase.

The intended architecture is documented in `PLATFORM_MASTER_PLAN.md`. Key rules are:

- ticketing is a dedicated domain rather than part of CRM;
- incoming email and website forms become ticket messages;
- mailboxes are first-class configuration records;
- Microsoft Graph is the initial mailbox provider;
- known ClientContact email addresses automatically resolve Client context;
- tickets expose client KB/credential/infrastructure context without broadening permissions;
- queues have explicit access scope;
- spam classification is not purely binary and can route vendor/automated messages into low-priority queues.

Expected mailboxes include support/accounts/sales addresses across multiple ADB brands.

## 9. Knowledge base, credentials and infrastructure

These domains form the IT Glue-style structured-documentation side of the platform.

### Knowledge base

Required future behaviour includes:

- client/internal ownership;
- sections/categories/tags;
- version history;
- author/editor metadata;
- permission scope;
- global/client-context search;
- explicit future portal visibility that defaults private.

### Credentials

The current legacy credential secret fields are plaintext and must not be treated as a production vault.

Foundation already defines separate capabilities for:

- viewing credential metadata;
- revealing secrets;
- copying secrets.

Before production credential storage is used, implement:

- encrypted-at-rest secret storage;
- explicit key-management design;
- metadata-only list/search APIs;
- audited reveal/copy operations;
- client/internal ownership;
- infrastructure/application relationships;
- safe rotation/expiry behaviour.

### Infrastructure

The existing model set already covers structured concepts such as servers, databases, websites, domains, certificates and applications.

A deeper field-by-field redesign remains deferred until the infrastructure workspace is implemented. Infrastructure records must use the same client/internal scope and permission model and should reference credentials rather than duplicate secrets.

## 10. Celery and integration architecture

Celery plumbing and local worker commands exist, but broad business workflows are not yet implemented.

Planned responsibilities include:

- transactional email;
- Microsoft Graph mailbox ingestion/sync;
- ticket classification/routing;
- notifications;
- recurring task generation;
- scheduled integration work.

Reusable business logic belongs in services. Celery tasks should orchestrate asynchronous execution rather than contain the only implementation of business rules.

## 11. Legacy/template cleanup status

- [x] Remove `Project Template` naming from active Django API/settings.
- [x] Remove TechWiki-specific active admin authentication code.
- [x] Search active code for remaining `TechWiki` identifiers.
- [x] Search active code for stale `auth-frontend` and `admin-website` path names.
- [x] Replace the README's old generic project description with the current platform architecture.
- [ ] Review remaining comments/TODOs as touched and remove statements that describe superseded architecture.
- [ ] Perform a final old-port/reference scan before marking foundation complete.

## 12. Historical documentation status

The repository contains historical planning files that pre-date the multi-brand platform design. They remain useful context but are no longer authoritative.

Canonical documentation priority is:

1. `docs/PLATFORM_MASTER_PLAN.md`;
2. `docs/PERMISSIONS_AND_ACCESS_MODEL.md`;
3. `docs/DOMAIN_MODEL_AUDIT.md`;
4. this checklist;
5. historical root-level planning documents.

Where historical documents conflict with the canonical `docs/` architecture, the canonical documents win.

Remaining documentation work:

- [ ] Add explicit superseded/canonical-document notices to `ADB_SOFTWARE_SOLUTIONS_BUILD_PLAN.md`.
- [ ] Add explicit superseded/canonical-document notices to `DJANGO_ARCHITECTURE.md`.
- [x] Update the repository README to describe the multi-brand business platform.
- [x] Keep root/scoped AGENTS guidance pointed at canonical architecture documents.

## 13. Foundation completion gate

Before moving to Clients + Contacts, the following are considered blocking:

- [x] Canonical architecture/product documentation exists.
- [x] Existing backend model audit exists.
- [x] Brand exists as a first-class domain model.
- [x] CMS backend is Brand-aware.
- [x] Custom CMS administration is Brand-aware.
- [x] Capability permissions and initial Client object scope exist.
- [x] Audit-event foundation exists.
- [x] TechWiki/template residue has been substantially removed.
- [x] README reflects the real platform.
- [ ] CI/lint/tests are green for the completed foundation branch.
- [ ] Remaining auth diagnostic logging is removed or deliberately gated.
- [ ] Historical architecture docs are clearly marked as superseded where appropriate.

Production-domain cookie/CORS verification is important but can only be completely validated once deployment hostnames are defined; this must remain documented rather than block all operational development indefinitely.

## 14. Ordered phases after foundation

Unless a later explicit architecture decision changes the order:

1. Clients and Contacts.
2. Projects.
3. Tasks and recurrence.
4. Time tracking.
5. CRM/Leads.
6. Tickets and queues.
7. Microsoft Graph Mailboxes and background sync.
8. Website contact forms -> tickets/leads.
9. Spam/classification/routing.
10. Knowledge base.
11. Credentials vault.
12. Infrastructure workspace.
13. Client-context/global search.
14. Public-site integration with the stable CMS.
15. Client portals and commercial features such as quotes, contracts, invoicing and Stripe payments once the internal platform is mature.

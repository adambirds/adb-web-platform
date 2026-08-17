# Domain Model Audit

## Purpose

This document records the foundation-phase review of existing Django models against the canonical architecture in `PLATFORM_MASTER_PLAN.md`.

Each model is classified as one of:

- **Keep** — concept and shape are broadly suitable.
- **Amend** — concept is correct but fields/relationships/behaviour need work.
- **Rename/Reframe** — useful data concept, but its name or purpose needs clarification.
- **Remove** — legacy/template residue not part of the ADB platform.
- **Defer** — concept remains valid but detailed design should wait for its implementation phase.

This is an architectural audit, not permission to implement every amendment immediately.

## Authentication

### User — Amend

Keep the custom UUID/email-based User model and Django `PermissionsMixin`.

Required amendments/decisions:

- retain Django Group/Permission primitives for capability permissions;
- remove unrelated legacy fields, including the eBay-account email flag;
- do not add client-portal-specific fields directly until the portal identity relationship is designed;
- current verification/password-reset fields are acceptable for now but token lifecycle/security should continue to be reviewed;
- eventually expose effective staff permissions/scopes through the admin current-user/bootstrap contract.

### CustomGroup — Keep for now

This is currently a proxy over Django Group rather than a separate role model. That is compatible with the permissions architecture. Do not create an independent role database unless a concrete need emerges.

### Passkey / TOTP / recovery / session models — Keep

These represent real authentication/security capabilities. Continue hardening and testing rather than replacing them.

## Platform core

### Brand — New / Keep

A first-class `apps.core.Brand` model is now the shared identity for public ADB brands.

Stable seed slugs:

- `adb-software-solutions`;
- `adb-web-designs`;
- `adb-technology`.

Brand is deliberately independent of Client ownership.

### AuditEvent — New / Keep

Append-only audit foundation for security-sensitive and important operational actions. Metadata must be curated and must never contain secrets.

## Clients

### Client — Amend

The concept is central and must remain the root of each customer's operational context.

Current issues:

- `name` plus `company` is ambiguous for a company/client record;
- a single email/phone on Client overlaps with ClientContact;
- address is unstructured enough for now but may need billing/company address semantics later;
- no explicit business metadata such as legal/display name distinction;
- no permission-scope integration yet.

Direction:

- treat Client as organisation/account;
- keep active/inactive/archive lifecycle;
- contacts own individual email identities;
- do not create an "Internal" fake Client;
- future billing/portal/commercial fields should be added only when required.

### ClientContact — Amend

This becomes the key identity-matching object for incoming email and future client portals.

Required future fields/capabilities:

- first/last or display name strategy;
- unique/normalised email identity appropriate for matching;
- primary contact flag;
- billing contact flag;
- technical contact flag;
- active/archive state;
- future optional relationship to a portal User;
- potential support/contact preferences later.

### Project — Amend

Keep as the operational project/work record for internal or client work.

Current project requires a Client. Target architecture must also support internal projects without inventing a fake Client.

Required future changes:

- explicit client-owned versus internal scope;
- optional Client when internal;
- billing type/currency where useful;
- project members/ownership later;
- tasks linked optionally, not required;
- tickets may optionally link to projects.

This model is completely separate from public portfolio/case-study content.

### TimeEntry — Amend

Keep time tracking but review whether every entry must belong to a Project. Initial business workflows primarily expect project time, but future internal/general time may justify optional project/client scope.

Add user/staff ownership of time entries when the operational API is implemented.

### ProjectNote — Amend

Keep internal project notes. Add author/audit metadata when project collaboration is implemented.

## CRM

### LeadSource — Keep

Configurable source taxonomy is useful. It should eventually support deterministic defaults and perhaps machine-readable slugs.

### LeadStatus — Keep

Configurable sales-pipeline status remains useful. Add machine-readable semantics if automation requires them.

### Lead — Amend

Keep exclusively for the sales lifecycle; do not turn this into the support ticket model.

The originating Brand relationship has now been added.

Future amendments:

- conversion relationship/state to Client;
- links to ticket/conversation records;
- assignee/owner;
- estimated value/currency where useful;
- richer source metadata without storing entire inbound emails in `message`.

## Tasks

### TaskStatus — Keep

Useful configurable workflow concept.

### TaskList — Amend

Keep optional organisational lists, but a task must not be forced into a list.

Lists may later be internal, client-specific or project-specific depending on actual UX needs.

### Task — Amend substantially

The current model is only a skeleton.

Target requirements:

- task list optional;
- project optional;
- client optional;
- future ticket optional;
- completely standalone/internal task valid;
- assignee(s) or clear single-assignee model;
- due date/time strategy;
- recurring rule/schedule;
- completion state/history;
- creator and audit metadata;
- scope validation so client/project combinations cannot conflict.

Monthly recurring invoice reminders are a canonical example of a valid task with no Project.

## Credentials

### CredentialType — Keep

Useful configurable metadata taxonomy.

### StoredCredential — Amend urgently before production use

The existing model stores secret fields in plaintext and explicitly contains encryption TODOs. It is not production-ready as a credential vault.

Required before any real secrets are stored:

- encrypted-at-rest secret payload with deliberate key management;
- client/internal ownership;
- metadata/secret separation;
- no secret values in list/search APIs;
- explicit `reveal` permission separate from normal view permission;
- reveal audit event;
- related infrastructure/application references;
- rotation/expiry metadata where useful;
- safe export/copy behaviour;
- tests proving secret non-disclosure.

Do not populate this table with production credentials until the security work is complete.

## Knowledge base

### KnowledgeBaseSection — Amend

Keep organisational sections, but define whether sections are global templates, per-client/internal containers, or both. Avoid forcing every client to recreate identical structural categories manually if reusable templates are useful.

### KnowledgeBaseDocument — Amend

Core concept remains correct.

Required future changes:

- client/internal ownership;
- author/editor metadata;
- tags/search metadata;
- explicit future portal visibility defaulting to private;
- attachments if needed;
- better version creation service rather than manual version rows.

### DocumentVersion — Amend

Keep immutable historical versions. Add editor and timestamp context; ensure versions are generated by document update services, not trusted directly from arbitrary clients.

## Infrastructure

The broad infrastructure inventory remains part of the platform. The individual models are useful but need a separate deeper implementation review before APIs/UI are expanded.

### Server — Amend

Keep. Add client/internal scope, related credentials, ownership/access policy and modernise static provider/OS choices.

### Database — Amend

Keep. Add client/internal scope, credential references and clearer managed/self-hosted semantics.

### Website — Amend

Keep as an operational website/application component record, not public CMS content. Add client/internal scope and continue linking servers/databases/domains/credentials.

### WebsiteTechStack — Amend

Keep, but consider a reusable Technology catalogue later rather than free-text duplication if actual data volume warrants it.

### Domain — Amend

Keep. Add client/internal scope and renewal/registrar relationships where useful.

### SSLCertificate — Amend

Keep where manual certificate tracking is useful. Automated Let's Encrypt certificates may eventually be derived/monitored rather than manually managed.

### Licence and remaining asset/application models — Amend/Defer

Keep the concepts described in the master plan. Review fields and relationships when the infrastructure workspace is implemented rather than aggressively redesigning all of them in this foundation PR.

## CMS / website content

### Portfolio — Rename/Reframe eventually

The data is public case-study content, not an operational Project. The model may eventually become `CaseStudy`, but a rename can wait until migration/API/UI impact is worth it.

It is now brand-aware.

### Testimonial — Keep / Amend

Keep. Brand assignment is many-to-many because a testimonial may legitimately be reused across brands.

### BlogPost — Keep / Amend

Keep. Brand assignment is many-to-many to permit deliberate cross-brand publishing. Public APIs must always scope by requested brand.

### BlogCategory / BlogTag — Keep / Amend

Keep and make brand-aware. This allows each public brand to expose only relevant taxonomy while still permitting deliberate reuse.

### FAQ / FAQCategory — Keep / Amend

Keep and make brand-aware. Public APIs must not leak FAQ content or taxonomy across brands.

## Ownership pattern

Operational models need a consistent rule:

- **client-owned**: references a real Client;
- **internal**: explicitly marked/internal-scoped with no Client;
- never infer internal ownership from an ambiguous null without validation;
- never create a fake internal Client.

The exact reusable implementation should be designed before changing every operational table. It may be an abstract model/constraint helper where this improves consistency without introducing generic polymorphic complexity.

## Next audit actions

1. Remove the legacy eBay User field with a migration.
2. Complete the deeper infrastructure-model field review before infrastructure APIs are built.
3. Design the client/internal ownership helper/validation pattern.
4. Design ClientAccessGrant alongside the Clients API rather than as a generic content-type ACL.
5. Harden StoredCredential before any production secrets are stored.
6. Expand Task/Project models only when their operational APIs are implemented, preserving the requirements above.

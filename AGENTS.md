# AGENTS.md

Guidance for AI coding agents working in this repository.

## Canonical platform documentation

Before making architectural, domain-model, permissions, CMS, CRM, ticketing, credential, infrastructure, authentication or operations-platform changes, read the relevant canonical documents:

- `docs/PLATFORM_MASTER_PLAN.md` — overall product and architecture plan;
- `docs/PERMISSIONS_AND_ACCESS_MODEL.md` — authorisation, roles, sensitive capabilities and object scoping;
- `docs/DOMAIN_MODEL_AUDIT.md` — model review and keep/amend/defer decisions;
- `docs/CURRENT_STATE_AND_FOUNDATION_CHECKLIST.md` — current implementation state and ordered operational roadmap;
- `docs/TICKETING_ARCHITECTURE.md` — ticketing and communication architecture;
- `docs/MICROSOFT_GRAPH_TICKETING_SETUP.md` — Microsoft 365/Graph deployment runbook.

These documents are canonical. Older root-level planning documents are historical context and must not override them when they conflict.

Do not invent a new architecture from partial code or stale documentation. If code conflicts with the canonical plan, determine whether the code is legacy/incomplete before copying its pattern into new work.

## Project

This repository is the shared application platform for the ADB businesses. It contains one shared Django backend, shared packages, three public brand applications, a dedicated authentication/account application, and the internal operations workspace.

The ADB Software Solutions public routes and internal operations workspace are intentionally one Next.js deployable application. Privileged internal routes live under `/admin` and remain clearly separated from public routes through App Router route/layout boundaries.

## Repository layout

- `backend/` — Django backend, Django Ninja APIs, CRM, Clients, Projects, Tasks, Time, Ticketing/Graph, Knowledge Base, Credentials, Infrastructure, CMS, Celery and shared business data.
- `sites/adb-software-solutions/` — combined ADB Software Solutions Next.js app: public routes plus authenticated operations under `/admin`.
- `sites/adb-web-designs/` — public ADB Web Designs website.
- `sites/adb-technology/` — public ADB Technology website.
- `sites/auth-adb-software-solutions/` — dedicated Next.js authentication/account frontend including login, TOTP, passkeys and session management.
- `packages/ui/` — genuinely reusable UI primitives and brand-neutral types.
- `packages/api-client/` — shared API helpers/contracts used by multiple frontends.
- `packages/eslint-config/` — shared ESLint configuration.
- `packages/typescript-config/` — shared TypeScript configuration.
- `tools/` — repository linting, testing and development tooling.

There is no `sites/admin-adb-software-solutions/` application. Do not recreate it unless an explicit future architectural decision reverses the combined-app topology.

## Architectural priorities

1. Keep Django as the single business-data/operations backend for all ADB brands.
2. Keep Django authoritative for authentication, permissions, scope and business rules.
3. Keep public routes and authenticated `/admin` routes clearly separated even though ADB Software Solutions serves both from one Next.js app.
4. Preserve the dedicated authentication/account application rather than duplicating security flows into every site.
5. Treat ADB Software Solutions, ADB Web Designs and ADB Technology as first-class Brands; do not scatter brand identity as hard-coded business-logic strings.
6. Keep Brand separate from Client/Internal operational ownership.
7. Treat Client as the main operational context linking Contacts, Tickets, Projects, Tasks, Time, KB, Credentials and Infrastructure.
8. Unify inbound communication around Tickets. Graph email, website forms and future portal communication must not become unrelated silos.
9. Keep Microsoft 365/Graph integration in the shared backend/operations platform, not individual public sites.
10. Fine-grained capabilities and object scopes are foundational. Never assume all staff are superusers.
11. Sensitive actions such as credential reveal, access changes and governed attachment actions must be explicitly permissioned/auditable.
12. Prefer maintainable domain services over logic hidden only inside Celery tasks or frontend components.
13. Keep strict typing and explicit Django/TypeScript contracts.
14. Shared packages contain genuinely shared code, not forced brand uniformity.
15. Keep CI/container images application-focused even though the repository uses pnpm workspaces.

## Stack

- Backend: Python 3.12+, Django, Django Ninja, PostgreSQL, Redis and Celery.
- ADB Software Solutions: Next.js App Router, React, TypeScript and Tailwind CSS; internal operations live under `/admin`.
- Authentication/account frontend: Next.js App Router, React and TypeScript.
- Other public websites: Next.js App Router, React, TypeScript and Tailwind CSS.
- Tooling: pnpm, repository `tools/` suite, Ruff, mypy, pytest, ESLint, Prettier and Stylelint.

Do not replace Django, Django Ninja, the existing authentication subsystem or the established deployment pipeline without an explicit architectural decision.

## Authentication and permissions

Authentication is security-sensitive. Preserve `sites/auth-adb-software-solutions/` and the Django-backed identity/session/TOTP/WebAuthn flows unless a task explicitly changes them. Do not introduce Auth.js/NextAuth, local-storage JWTs or a second identity authority by default.

Public marketing routes must not expose privileged operations. Internal operations belong under `sites/adb-software-solutions/.../admin` and authenticated account/security flows belong in `sites/auth-adb-software-solutions/`.

Permissions must support capability and scope. A permission such as viewing Tickets does not imply access to every Client or Ticket Queue. Credential metadata view and secret reveal/copy are separate capabilities. Permission-boundary tests are mandatory for restricted APIs.

Use Django Groups/Permissions for capabilities and the established access-control scope layer for object visibility. Never rely on a React component hiding an action as the security check.

## Public websites and CMS

The three public brands serve different commercial purposes and must not become recoloured copies of one template.

Main marketing pages are code-owned. CMS-managed content is intentionally limited to editorial content such as blog posts, testimonials, FAQs and optionally public Case Studies/Portfolio. CMS content must be Brand-aware and public APIs must not leak content between Brands.

Operational `Project` is not public `Portfolio`/CaseStudy. They may reference one another later, but remain separate concepts.

Public forms should call the shared Django backend and identify Brand/source. Website contact forms currently participate in the Lead + Ticket ingestion pipeline; preserve that unified communication model.

## Business platform domains

Before making public-site development the main focus, the internal platform roadmap prioritises:

- Client/Contact CRUD and complete Client workspaces;
- Lead detail/CRUD and Ticket/email relationships;
- Project detail/CRUD;
- Task CRUD/completion/list modes;
- Users & Access;
- IT Glue-style Knowledge Base, Credentials and Infrastructure;
- timer-based integrated Time Tracking;
- Calendar/work planning;
- configurable per-user Dashboard widgets/layouts;
- cross-domain Client context/search.

Future capabilities include client portals, quotes, contracts, invoicing and Stripe payments. These may influence clean extension points but must not be implemented speculatively during unrelated work.

Tasks do not require Projects. Standalone and recurring internal work is a valid first-class use case.

## Working rules

Read nearby code, tests and documentation before editing. Keep changes scoped to the requested task. Add/update tests for behavioural changes. Do not silently weaken lint, type or test rules. Do not commit secrets, credentials, local environment files or generated coverage output.

The lint runner discovers tracked files through Git. Stage intended new files before running `tools/lint`, review staged scope with `git status`, then run `tools/lint` and relevant tests before considering work complete. If a check cannot run, state exactly why.

For Python, use modern typing and existing Django conventions. For TypeScript, keep strict typing and avoid `any` unless unavoidable/documented. Prefer Server Components for public pages by default; use client components where browser-side state/APIs are genuinely required. Operational admin pages may use client components when interactive workflow state requires them.

Generated Python requirement lock files must never be hand-edited. Change `backend/requirements/*.in`, run `tools/update-locked-requirements`, and commit the source and generated lock files together. Likewise, regenerate pnpm lock state with pnpm rather than editing `pnpm-lock.yaml` by hand.

## Commit messages

Use `<type>: <Imperative summary>.`, keep the complete title at or below 76 characters, and follow repository conventional-commit rules. Use `tools/commit-message-lint` before handoff where available.

## Documentation

Update README/docs when adding or changing an application, environment variable, port, deployment requirement, data store, authentication behaviour, external integration or breaking API/configuration.

Architectural decisions must update canonical docs in the same change so future developers/agents do not need chat history to reconstruct intent.
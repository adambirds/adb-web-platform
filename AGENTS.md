# AGENTS.md

Guidance for AI coding agents working in this repository.

## Canonical platform documentation

Before making architectural, domain-model, permissions, CMS, CRM, ticketing, credential, infrastructure, authentication or admin-platform changes, read the relevant canonical documents:

- `docs/PLATFORM_MASTER_PLAN.md` — overall product and architecture plan;
- `docs/PERMISSIONS_AND_ACCESS_MODEL.md` — authorisation, roles, sensitive capabilities and object scoping;
- `docs/DOMAIN_MODEL_AUDIT.md` — current model review and keep/amend/defer decisions;
- `docs/CURRENT_STATE_AND_FOUNDATION_CHECKLIST.md` — implementation state and ordered foundation work.

These documents are the canonical product and architecture guidance for the ADB Business Platform. Older planning documents are historical context and must not override them when they conflict.

Do not invent a new architecture from partial code or stale documentation. If code conflicts with the canonical plan, determine whether the code is legacy/incomplete before copying its pattern into new work.

## Project

This repository is the shared application platform for the ADB businesses. It contains a shared Django backend, shared packages, three separate public websites, a dedicated authentication frontend, and an internal administration application.

All browser-facing applications belong under `sites/`. Public marketing functionality must remain separate from the admin and authentication applications.

## Repository layout

- `backend/` — Django backend, Django Ninja APIs, CRM, clients, infrastructure, credentials, knowledge base, tasks, ticketing/email integrations, Celery and shared business data.
- `sites/adb-software-solutions/` — public ADB Software Solutions website.
- `sites/adb-web-designs/` — public ADB Web Designs website.
- `sites/adb-technology/` — public ADB Technology website for DevOps, infrastructure, IT consultancy, and support services.
- `sites/auth-adb-software-solutions/` — dedicated authentication/account frontend, including login, 2FA, passkeys and session-management flows.
- `sites/admin-adb-software-solutions/` — internal Next.js administration application. This is not a public marketing site.
- `packages/ui/` — genuinely reusable UI primitives and brand-neutral types.
- `packages/api-client/` — shared API client helpers and contracts used by multiple frontends.
- `packages/eslint-config/` — shared lint configuration where it is actually useful.
- `packages/typescript-config/` — shared TypeScript configuration.
- `tools/` — repository linting, testing and development tooling.

## Architectural priorities

1. Keep the Django backend as the single business-data and operations backend for all ADB brands.
2. Keep authentication and the internal administration experience separate from public marketing websites.
3. Treat ADB Software Solutions, ADB Web Designs and ADB Technology as first-class Brands; do not scatter brand identity as hard-coded strings through business logic.
4. Keep Brand scope separate from operational ownership. Operational resources are client-owned or explicitly internal.
5. Treat Client as the main operational context linking contacts, tickets, projects, tasks, time, documentation, credentials and infrastructure.
6. Public-site enquiries should ultimately become tickets and sales/CRM records with an explicit originating brand/source rather than creating separate communication silos.
7. Microsoft 365/Graph email integration belongs in the shared backend/admin platform, not in individual marketing sites.
8. Fine-grained permissions and access scopes are foundational. Do not assume every staff user is a superuser.
9. Backend Django permission checks are authoritative. Frontend visibility is UX, not security.
10. Sensitive actions such as credential reveals and permission changes must be auditable.
11. Prefer straightforward, maintainable implementations over new infrastructure or abstractions added pre-emptively.
12. Shared packages must contain code that is genuinely shared. Do not force public brands to use identical layouts or visual identities merely because they live in one repository.
13. Preserve strict typing and explicit API contracts between Django and TypeScript applications.
14. Keep CI/CD and container images application-focused even though frontend applications share a pnpm workspace.

## Stack

- Backend: Python 3.12+, Django, Django Ninja, PostgreSQL, Redis and Celery.
- Authentication frontend: React/Vite/TypeScript.
- Internal admin frontend: Next.js, React and TypeScript using the App Router.
- Public websites: Next.js, React, TypeScript and Tailwind CSS using the App Router.
- Tooling: pnpm, repository `tools/` suite, Ruff, mypy, pytest, ESLint, Prettier and Stylelint.

Do not replace Django, Django Ninja, the existing authentication subsystem or the established deployment pipeline without an explicit architectural decision.

## Authentication and permissions

Authentication is a first-class subsystem. Preserve `sites/auth-adb-software-solutions/` and the backend authentication flows unless a task explicitly changes them. Passwords, 2FA, passkeys, sessions and account-security behaviour are security-sensitive. Use established libraries and never implement cryptographic primitives manually.

The public marketing sites must not gain privileged admin functionality. Internal administration routes belong in `sites/admin-adb-software-solutions/` and authenticated account/security flows belong in `sites/auth-adb-software-solutions/`.

Permissions must support meaningful capabilities and scope. A permission such as viewing tickets does not automatically imply access to every client or ticket queue. Credentials require particularly deliberate handling: viewing metadata and revealing a secret are separate capabilities, and secret reveals must be audit logged.

Use Django Groups/Permissions for capability grants and the access-control scope layer for object visibility. Do not introduce a generic content-type ACL system unless the canonical permissions plan is explicitly changed.

When implementing restricted APIs, add tests for both permitted and denied access paths. Never rely on a React component hiding an action as the permission check.

## Public websites and CMS

The three public websites serve different commercial purposes and must not become recoloured copies of one template.

- ADB Software Solutions focuses on bespoke software, integrations, automation, SaaS/product development, client software work and ADB software products.
- ADB Web Designs focuses on websites, WordPress/Next.js delivery, website rescue, hosting, maintenance, performance and ongoing support.
- ADB Technology focuses on DevOps, cloud/infrastructure engineering, IT consultancy and technical support.

Main marketing pages are code-owned. CMS-managed content is intentionally limited to editorial content such as blog posts, testimonials, FAQs and optionally public case studies/projects. CMS content must be brand-aware and public APIs must not leak content between brands.

Operational `Project` records are not public case studies. A public case study may reference an operational Project, but they must remain separate models/concepts.

Share low-level primitives when useful, but keep brand messaging, page composition, navigation, imagery and visual identity owned by each site.

## Business platform domains

The internal platform is intended to cover clients/contacts, CRM/leads, projects, standalone and project-linked tasks, time tracking, ticketing/communications, knowledge base, credentials, infrastructure inventory and content management.

Future capabilities include client portals, quotes, contracts, invoicing and Stripe payments. These future features may influence clean extension points but must not be implemented speculatively during unrelated work.

Tasks do not require projects. Standalone and recurring internal work, such as monthly invoice reminders, is a valid first-class use case.

Inbound communication should ultimately unify around Tickets. Microsoft Graph email, contact forms and future portal messages should not become unrelated communication stores.

## Working rules

Read nearby code, tests and documentation before editing. Keep changes scoped to the requested task. Add or update tests for behavioural changes. Do not silently weaken lint, type or test rules. Do not commit secrets, credentials, local environment files or generated coverage output.

The lint runner discovers tracked files through Git. Stage intended new files before running `tools/lint`, review the staged scope with `git status`, then run `tools/lint` and the relevant tests before considering work complete. If a check cannot run, state exactly why.

For Python, use modern typing and follow existing Django conventions. For TypeScript, keep strict typing and avoid `any` unless unavoidable and documented. Prefer Server Components by default in Next.js public sites and introduce client components only when browser-side state or APIs are required.

## Commit messages

When creating a commit, use `<type>: <Imperative summary>.`, keep the complete title at or below 76 characters, and follow the repository's existing conventional commit rules. Use `tools/commit-message-lint` before handing off a commit.

## Documentation

Update README/docs when adding a public application, environment variable, port, deployment requirement, data-store requirement, authentication change or breaking API/configuration change. Keep repository structure documentation accurate whenever an application is moved or renamed.

Architectural decisions that affect the platform plan must update the canonical docs in the same change so a future agent does not need chat history to reconstruct the intent.

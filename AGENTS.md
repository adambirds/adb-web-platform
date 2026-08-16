# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project

This repository is the shared application platform for the ADB businesses. It contains a shared Django backend, shared packages, three separate public websites, a dedicated authentication frontend, and an internal administration application.

All browser-facing applications belong under `sites/`. Public marketing functionality must remain separate from the admin and authentication applications.

## Repository layout

- `backend/` — Django backend, Django Ninja APIs, CRM, clients, infrastructure, credentials, knowledge base, tasks, email integrations, Celery and shared business data.
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
3. Public-site enquiries should ultimately enter the shared CRM with an explicit brand/source rather than creating separate backends.
4. Microsoft 365/Graph email integration belongs in the shared backend/admin platform, not in individual marketing sites.
5. Prefer straightforward, maintainable implementations over new infrastructure or abstractions added pre-emptively.
6. Shared packages must contain code that is genuinely shared. Do not force public brands to use identical layouts or visual identities merely because they live in one repository.
7. Preserve strict typing and explicit API contracts between Django and TypeScript applications.
8. Keep CI/CD and container images application-focused even though frontend applications share a pnpm workspace.

## Stack

- Backend: Python 3.12+, Django, Django Ninja, PostgreSQL, Redis and Celery.
- Authentication frontend: React/Vite/TypeScript.
- Internal admin frontend: Next.js, React and TypeScript using the App Router.
- Public websites: Next.js, React, TypeScript and Tailwind CSS using the App Router.
- Tooling: pnpm, repository `tools/` suite, Ruff, mypy, pytest, ESLint, Prettier and Stylelint.

Do not replace Django, Django Ninja, the existing authentication subsystem or the established deployment pipeline without an explicit architectural decision.

## Authentication

Authentication is a first-class subsystem. Preserve `sites/auth-adb-software-solutions/` and the backend authentication flows unless a task explicitly changes them. Passwords, 2FA, passkeys, sessions and account-security behaviour are security-sensitive. Use established libraries and never implement cryptographic primitives manually.

The public marketing sites must not gain privileged admin functionality. Internal administration routes belong in `sites/admin-adb-software-solutions/` and authenticated account/security flows belong in `sites/auth-adb-software-solutions/`.

## Public websites

The three public websites serve different commercial purposes and must not become recoloured copies of one template.

- ADB Software Solutions focuses on bespoke software, integrations, automation, SaaS/product development, client software work and ADB software products.
- ADB Web Designs focuses on websites, WordPress/Next.js delivery, website rescue, hosting, maintenance, performance and ongoing support.
- ADB Technology focuses on DevOps, cloud/infrastructure engineering, IT consultancy and technical support.

Share low-level primitives when useful, but keep brand messaging, page composition, navigation, imagery and visual identity owned by each site.

## Working rules

Read nearby code, tests and documentation before editing. Keep changes scoped to the requested task. Add or update tests for behavioural changes. Do not silently weaken lint, type or test rules. Do not commit secrets, credentials, local environment files or generated coverage output.

The lint runner discovers tracked files through Git. Stage intended new files before running `tools/lint`, review the staged scope with `git status`, then run `tools/lint` and the relevant tests before considering work complete. If a check cannot run, state exactly why.

For Python, use modern typing and follow existing Django conventions. For TypeScript, keep strict typing and avoid `any` unless unavoidable and documented. Prefer Server Components by default in Next.js public sites and introduce client components only when browser-side state or APIs are required.

## Commit messages

When creating a commit, use `<type>: <Imperative summary>.`, keep the complete title at or below 76 characters, and follow the repository's existing conventional commit rules. Use `tools/commit-message-lint` before handing off a commit.

## Documentation

Update README/docs when adding a public application, environment variable, port, deployment requirement, data-store requirement, authentication change or breaking API/configuration change. Keep repository structure documentation accurate whenever an application is moved or renamed.

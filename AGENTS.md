# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project

This repository is the shared application platform for the ADB businesses. It contains the Django backend and internal administration applications plus separate public Next.js sites for ADB Software Solutions and ADB Web Designs.

The public sites are intentionally separate from the internal administration UI. Do not add marketing pages back into `admin-website/`.

## Repository layout

- `backend/` — Django backend, Django Ninja APIs, CRM, clients, infrastructure, credentials, knowledge base, tasks, email integrations, Celery and shared business data.
- `auth-frontend/` — dedicated authentication/account frontend, including login, 2FA, passkeys and session-management flows.
- `admin-website/` — internal Next.js administration application. This is not a public marketing site.
- `sites/adb-software-solutions/` — public ADB Software Solutions website.
- `sites/adb-web-designs/` — public ADB Web Designs website.
- `packages/ui/` — genuinely reusable UI primitives and brand-neutral types.
- `packages/api-client/` — shared API client helpers and contracts used by multiple frontends.
- `packages/eslint-config/` — shared lint configuration where it is actually useful.
- `packages/typescript-config/` — shared TypeScript configuration.
- `tools/` — repository linting, testing and development tooling.

ADB Technology may become a third public site later. Do not create it speculatively unless explicitly requested.

## Architectural priorities

1. Keep the Django backend as the single business-data and operations backend for all ADB brands.
2. Keep authentication and the internal administration experience separate from public marketing websites.
3. Public-site enquiries should ultimately enter the shared CRM with an explicit brand/source rather than creating separate backends.
4. Microsoft 365/Graph email integration belongs in the shared backend/admin platform, not in individual marketing sites.
5. Prefer straightforward, maintainable implementations over new infrastructure or abstractions added pre-emptively.
6. Shared packages must contain code that is genuinely shared. Do not force the public brands to use identical layouts or visual identities merely because they live in one repository.
7. Preserve strict typing and explicit API contracts between Django and TypeScript applications.
8. Do not redesign the existing deployment model or CI/CD conventions unless the requested change requires it.

## Stack

- Backend: Python 3.12+, Django, Django Ninja, PostgreSQL, Redis and Celery.
- Authentication frontend: React/Vite/TypeScript.
- Internal admin frontend: Next.js, React and TypeScript using the App Router.
- Public websites: Next.js, React, TypeScript and Tailwind CSS using the App Router.
- Tooling: pnpm, repository `tools/` suite, Ruff, mypy, pytest, ESLint, Prettier and Stylelint.

Do not replace Django, Django Ninja, the existing authentication subsystem or the established deployment pipeline without an explicit architectural decision.

## Backend and database changes

Read the existing backend code, migrations and nearby tests before changing persistent models. Use Django migrations for schema changes and review generated migrations before committing them. Keep business logic out of migrations unless it is specifically data-migration logic.

The backend is shared across brands. Model brand-specific behaviour explicitly rather than duplicating applications or databases without a strong reason.

## Authentication

Authentication is a first-class subsystem. Preserve the existing `auth-frontend/` and backend authentication flows unless a task explicitly changes them. Passwords, 2FA, passkeys, sessions and account-security behaviour are security-sensitive. Use established libraries and never implement cryptographic primitives manually.

The public marketing sites must not gain privileged admin functionality. Internal administration routes belong in `admin-website/` and authenticated account/security flows belong in `auth-frontend/`.

## Public websites

The two public websites solve different commercial problems and must not become recoloured copies of one template.

- ADB Software Solutions focuses on bespoke software, integrations, automation, SaaS/product development, client software work and ADB software products.
- ADB Web Designs focuses on websites, WordPress/Next.js delivery, website rescue, hosting, maintenance, performance and ongoing support.

Share low-level primitives when useful, but keep brand messaging, page composition, navigation, imagery and visual identity owned by each site.

## Commit messages

When creating a commit, agents must use this exact title format:

```text
<type>: <Imperative summary>.
```

Use one of these lowercase types:

- `feat` — new user-visible functionality.
- `fix` — a bug fix.
- `refactor` — a code change that neither fixes a bug nor adds a feature.
- `test` — test-only changes.
- `docs` — documentation-only changes.
- `style` — formatting or other non-functional source changes.
- `build` — build system or dependency changes.
- `ci` — continuous-integration changes.
- `deployment` — containers, packaging or deployment changes.
- `chore` — repository maintenance not covered by another type.

The summary after the prefix must start with a capital letter, use imperative mood, end with a period and make the commit purpose specific. The complete title, including prefix and final period, must not exceed 76 characters.

Do not use past tense, a gerund or third-person wording such as `Fixed`, `Fixing` or `Fixes`.

A body is optional. Separate it from the title with a blank line, explain why the change is needed when the title is not sufficient and keep every body line at or below 76 characters.

Valid examples:

```text
fix: Fix issue with authentication.
refactor: Separate the internal admin site.
ci: Update frontend workflow paths.
deployment: Add public website image build.
```

Before handing off a commit, run `tools/commit-message-lint` and correct every reported violation. Do not bypass the commit-message rules.

## Working rules

Read nearby code, tests and documentation before editing. Keep changes scoped to the requested task. Add or update tests for behavioural changes. Do not silently weaken lint, type or test rules. Do not commit secrets, credentials, local environment files or generated coverage output.

The lint runner discovers tracked files through Git. Stage intended new files before running `tools/lint`, review the staged scope with `git status`, then run `tools/lint` and the relevant tests before considering work complete. If a check cannot run, state exactly why.

When a cohesive requested task is fully implemented and validated, commit it using the repository commit-message rules. For a large feature or multi-part refactor, use multiple coherent commits rather than a premature catch-all commit.

Branch-and-pull-request workflow is the default for all changes. Large features, multi-feature changes and work expected to need follow-up commits must always use a dedicated branch and pull request.

Keep Git history linear. Fetch and rebase onto the latest target branch rather than merging the target branch into the working branch. Never create merge commits for routine branch updates. If a published rebase requires a non-fast-forward update, use `git push --force-with-lease`, never plain `--force`.

For Python, use modern typing and follow existing Django conventions. For TypeScript, keep strict typing and avoid `any` unless unavoidable and documented. Prefer Server Components by default in Next.js public sites and introduce client components only when browser-side state or APIs are required.

## Documentation

Update README/docs when adding a public application, environment variable, port, deployment requirement, data-store requirement, authentication change or breaking API/configuration change. Keep repository structure documentation accurate whenever an application is moved or renamed.

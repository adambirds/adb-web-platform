# ADB Web Platform

Shared web and business-operations platform for the ADB brands.

The repository contains the three public ADB websites, a shared authentication/account application, the internal administration workspace, and the Django backend that powers both public content and internal operations.

## Applications

All browser-facing applications live under `sites/`:

- `sites/adb-software-solutions/` — combined ADB Software Solutions application. Public marketing routes live alongside the authenticated internal operations workspace under `/admin`.
- `sites/adb-web-designs/` — public ADB Web Designs website.
- `sites/adb-technology/` — public ADB Technology website for DevOps, IT consultancy, infrastructure, and support services.
- `sites/auth-adb-software-solutions/` — shared authentication, account-security, passkey, TOTP, and session-management frontend.

The shared Django backend lives at `backend/`, while reusable frontend/tooling packages live under `packages/`.

## Platform model

The platform is one shared operational system serving multiple ADB brands.

Public website pages such as home, service and marketing pages are owned in code. Dynamic public content such as blog posts, testimonials, FAQs and public case studies is managed through the CMS and explicitly assigned to one or more Brands.

Internal operational data follows a different scope model: resources are either client-owned or explicitly internal. Brand and Client are separate concepts. For example, a future support ticket can belong to ADB Web Designs while also belonging to a specific client.

The long-term internal platform combines concepts normally spread across CRM, ticketing, project-management and structured-documentation tools. Planned domains include:

- clients and contacts;
- CRM and leads;
- projects, tasks and time tracking;
- ticket queues and communications;
- Microsoft Graph-backed mailboxes;
- knowledge-base documentation;
- credential management;
- infrastructure inventory;
- background workflows and notifications;
- client-context search;
- later client portals, quotes, contracts, invoicing and payments.

Permissions are backend-authoritative. Django permissions describe capabilities, while explicit scope grants restrict which clients and, later, ticket queues a staff user can access. Sensitive operations such as credential reveal are designed as separate capabilities and will be audit logged.

## Architecture documentation

Before changing domain architecture, authentication, authorisation, CMS behaviour, ticketing, credentials, infrastructure, or client ownership, read:

- `docs/PLATFORM_MASTER_PLAN.md` — canonical product and architecture plan.
- `docs/PERMISSIONS_AND_ACCESS_MODEL.md` — permissions and object-scope architecture.
- `docs/DOMAIN_MODEL_AUDIT.md` — decisions from the existing Django model audit.
- `docs/CURRENT_STATE_AND_FOUNDATION_CHECKLIST.md` — current implementation status and ordered roadmap.

Older planning documents in the repository are historical context. Where they conflict with the documents above, the canonical `docs/` architecture takes precedence.

## Shared packages

- `packages/ui/` — brand-neutral shared UI primitives and types.
- `packages/api-client/` — shared API helpers/contracts.
- `packages/eslint-config/` — shared ESLint configuration.
- `packages/typescript-config/` — shared TypeScript configuration.

## Development

The recommended development environment is VS Code Dev Containers.

After opening the repository in the container, the primary development services are:

```text
Django backend             http://localhost:8000
ADB Software Solutions     http://localhost:3000
  Internal admin           http://localhost:3000/admin
ADB Web Designs            http://localhost:3002
ADB Technology             http://localhost:3003
Authentication frontend    http://localhost:3004
Flower                      http://localhost:5555
```

Useful root commands:

```bash
pnpm dev:auth
pnpm dev:software-solutions
pnpm dev:web-designs
pnpm dev:technology
tools/lint
tools/test-all
```

Read `AGENTS.md` and `CONTRIBUTING.md` before making changes. Scoped `AGENTS.md` files provide additional guidance inside major application areas.

## Monorepo approach

The repository intentionally does not use Turborepo or another monorepo orchestration framework. pnpm workspaces provide shared-package resolution while CI/CD and container images remain application-focused.

Each deployable application has its own Docker image. Published images in the shared DigitalOcean Container Registry are prefixed with `adb-web-platform-` so they cannot collide with unrelated ADB projects.

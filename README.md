# ADB Web Platform

Shared web and business-operations platform for the ADB brands.

The repository contains the three ADB public websites, a shared authentication/account application, the internal operations workspace, and the Django backend that powers public content and internal business workflows.

## Applications

All browser-facing applications live under `sites/`:

- `sites/adb-software-solutions/` — combined ADB Software Solutions Next.js application. Public marketing routes live alongside the authenticated internal operations workspace under `/admin`.
- `sites/adb-web-designs/` — public ADB Web Designs website.
- `sites/adb-technology/` — public ADB Technology website for DevOps, IT consultancy, infrastructure and support services.
- `sites/auth-adb-software-solutions/` — shared authentication/account-security application for login, password/account flows, passkeys, TOTP and session management.

The shared Django backend lives at `backend/`; reusable frontend/tooling packages live under `packages/`.

There is no separate admin frontend deployment. The internal operations workspace is part of `sites/adb-software-solutions/` and is served under `/admin`.

## Platform model

The platform is one shared operational system serving multiple ADB Brands.

Public marketing pages are owned in code. Dynamic public content such as blog posts, testimonials, FAQs and public case studies is managed through the CMS and explicitly Brand-scoped.

Operational data uses a separate ownership model: resources are Client-owned or explicitly Internal. Brand and Client are different concepts. For example, a Ticket may belong to ADB Web Designs while also belonging to a specific Client.

The internal platform covers or is being developed to cover:

- Clients and Contacts;
- CRM and Leads;
- Projects;
- Tasks and work planning;
- Time Tracking;
- Ticket Queues and communications;
- Microsoft Graph-backed Shared Mailboxes;
- Knowledge Base documentation;
- credential/secret management;
- Infrastructure inventory;
- configurable dashboards and Calendar/work planning;
- Client-context search and cross-domain workspaces;
- later client portals, quotes, contracts, invoicing and payments.

The ticketing/communications foundation is implemented, including Graph mailbox sync/replies, website contact-form ingestion, vendor routing and governed attachments. Several other operational modules currently have register/list foundations but still require full create/edit/detail/workflow UX before the internal platform is considered operationally complete.

Permissions are backend-authoritative. Django permissions describe capabilities while explicit scopes restrict which Clients and Ticket Queues a staff user can access. Sensitive operations such as credential reveal/copy are separate capabilities and must be audit logged.

## Architecture documentation

Before changing domain architecture, authentication, authorisation, CMS behaviour, ticketing, credentials, infrastructure or Client ownership, read:

- `docs/PLATFORM_MASTER_PLAN.md` — canonical product and architecture plan.
- `docs/CURRENT_STATE_AND_FOUNDATION_CHECKLIST.md` — current implementation state and ordered operational roadmap.
- `docs/PERMISSIONS_AND_ACCESS_MODEL.md` — permissions and object-scope architecture.
- `docs/DOMAIN_MODEL_AUDIT.md` — decisions from the Django model audit.
- `docs/TICKETING_ARCHITECTURE.md` — ticketing and communications architecture.
- `docs/MICROSOFT_GRAPH_TICKETING_SETUP.md` — complete Microsoft 365/Graph/Exchange RBAC setup runbook.

Older root-level planning documents are historical context only. Where they conflict with canonical `docs/` architecture, the canonical documents take precedence.

## Current development priorities

Before public-site development becomes the main focus, the internal platform roadmap prioritises:

1. Client/Contact CRUD and complete Client workspaces, plus Users & Access.
2. Lead, Project and Task detail/CRUD/workflow completion.
3. IT Glue-style Knowledge Base, Credentials and Infrastructure workspaces.
4. integrated timer-based Time Tracking and Calendar/work planning.
5. complete cross-domain Client context and configurable per-user Dashboard widgets/layouts.

See `docs/CURRENT_STATE_AND_FOUNDATION_CHECKLIST.md` for the detailed implementation checklist.

## Shared packages

- `packages/ui/` — brand-neutral shared UI primitives and types.
- `packages/api-client/` — shared API helpers/contracts.
- `packages/eslint-config/` — shared ESLint configuration.
- `packages/typescript-config/` — shared TypeScript configuration.

## Development

The recommended development environment is VS Code Dev Containers.

Primary local services:

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

Python dependency lock files are generated. Update `backend/requirements/*.in`, then run:

```bash
tools/update-locked-requirements
```

Do not hand-edit generated requirement lock files or `pnpm-lock.yaml`.

Read `AGENTS.md` and `CONTRIBUTING.md` before making changes. Scoped `AGENTS.md` files provide additional guidance inside major application areas.

## Monorepo approach

The repository intentionally does not use Turborepo or another monorepo orchestration framework. pnpm workspaces provide shared-package resolution while CI/CD and container images remain application-focused.

Each deployable application has its own Docker image. Published images in the shared DigitalOcean Container Registry are prefixed with `adb-web-platform-` so they cannot collide with unrelated ADB projects.

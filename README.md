# ADB Web Platform

Shared codebase for the ADB businesses.

## Applications

All browser-facing applications live under `sites/`:

- `sites/adb-software-solutions/` — public ADB Software Solutions website.
- `sites/adb-web-designs/` — public ADB Web Designs website.
- `sites/adb-technology/` — public ADB Technology website for DevOps, IT consultancy, infrastructure, and support services.
- `sites/auth-adb-software-solutions/` — authentication and account frontend.
- `sites/admin-adb-software-solutions/` — internal Next.js administration application.

The shared Django backend remains at `backend/`, while reusable frontend/tooling packages live under `packages/`.

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
Internal admin website     http://localhost:3000
ADB Software Solutions     http://localhost:3001
ADB Web Designs            http://localhost:3002
ADB Technology             http://localhost:3003
Authentication frontend    http://localhost:5173
Flower                      http://localhost:5555
```

Useful root commands:

```bash
pnpm dev:admin
pnpm dev:auth
pnpm dev:software-solutions
pnpm dev:web-designs
pnpm dev:technology
tools/lint
tools/test-all
```

Read `AGENTS.md` and `CONTRIBUTING.md` before making changes. Scoped `AGENTS.md` files provide additional guidance inside major application areas.

## Architecture

The Django backend is shared across all ADB brands and internal operations. Browser-facing applications are grouped under `sites/`, but remain independent applications so public brands, authentication, and administration can evolve independently.

The repository intentionally does not use Turborepo or another monorepo orchestration framework. pnpm workspaces provide shared-package resolution while CI/CD and container images remain application-focused.

# ADB Web Platform

Shared codebase for the ADB businesses.

## Applications

- `backend/` — Django backend and shared operations platform.
- `auth-frontend/` — authentication/account frontend.
- `admin-website/` — internal Next.js administration application.
- `sites/adb-software-solutions/` — public ADB Software Solutions website.
- `sites/adb-web-designs/` — public ADB Web Designs website.

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
Authentication frontend    http://localhost:5173
Flower                      http://localhost:5555
```

Useful root commands:

```bash
pnpm dev:admin
pnpm dev:auth
pnpm dev:software-solutions
pnpm dev:web-designs
tools/lint
tools/test-all
```

Read `AGENTS.md` and `CONTRIBUTING.md` before making changes. Scoped `AGENTS.md` files provide additional guidance inside major application areas.

## Architecture

The Django backend is shared across all public brands and the internal administration applications. Public websites remain independent Next.js applications so their branding, content and conversion journeys can evolve independently.

The repository intentionally does not use Turborepo or another monorepo orchestration framework. pnpm workspaces provide shared-package resolution while the existing deployment and CI/CD approach remains application-focused.

ADB Technology may be added as another public site in the future, but is intentionally not scaffolded until it is needed.

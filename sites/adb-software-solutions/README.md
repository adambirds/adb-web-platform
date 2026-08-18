# ADB Software Solutions

This Next.js application serves both the public ADB Software Solutions website and the authenticated internal ADB Business Platform.

## Route ownership

- `/` and other public routes: ADB Software Solutions marketing website.
- `/admin`: authenticated internal operations workspace.
- Authentication remains delegated to the separate `sites/auth-adb-software-solutions` application and the Django backend.

The public marketing site is intentionally minimal while it is rebuilt. Until those routes are implemented, `/` redirects to `/admin`.

## Development

From the repository root:

```bash
pnpm dev:software-solutions
```

The application runs on:

```text
http://localhost:3000
```

The Django API is expected on `http://localhost:8000` during local development, and the auth application runs separately on port `3004`.

## Admin UI conventions

The internal workspace is dark-only, full-width by default and built from the shared primitives in `src/components/ui`.

Data-heavy screens should support pagination, filtering and drill-down navigation rather than rendering unbounded tables. Reuse existing UI primitives before adding page-specific components.

See the repository root documentation and `AGENTS.md` for the broader platform architecture and contribution rules.

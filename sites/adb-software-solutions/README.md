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

## Public website editing

Run `pnpm --dir sites/adb-software-solutions dev` from the repository root (port 3000).
Edit `src/content/site.ts` for services, locations, About, policies and contact copy;
edit `src/content/home.ts` for homepage text. The homepage layout/artwork lives in
`src/components/public/HomePage.tsx` and brand styling in `src/styles/public.css`.

Blog, portfolio, testimonials and FAQs are published through `/admin/content` in
the Software operations app. Assign this Brand explicitly, save a draft, upload
images from its edit form and publish after review. Empty collections are hidden
from navigation and sitemaps. Public requests use the shared backend; configure
`API_INTERNAL_URL` at runtime if a private server-to-server origin is needed.

See the root README public setup guide and `docs/PUBLIC_WEBSITES_MORNING_REVIEW.md`
for launch assumptions, policy review and validation.

# AGENTS.md

Scoped guidance for `sites/adb-software-solutions/`.

- This Next.js application serves both the public ADB Software Solutions website and the authenticated internal operations platform under `/admin`.
- Public marketing routes and authenticated `/admin` routes must remain clearly separated through App Router route groups and shared layout boundaries.
- Preserve the authenticated `/admin` functionality and its integration with `sites/auth-adb-software-solutions/` and the Django backend.
- Internal workflows may cover CRM, leads, clients, projects, tickets, content, infrastructure, credentials and email.
- Prefer shared UI primitives and layouts over page-specific duplication, especially inside the admin operations workspace.
- Admin pages are dark-only, full-width by default and should use consistent page spacing. Narrow content widths should be reserved for forms or long-form reading where they materially improve usability.
- Data-heavy admin screens must be designed for server-side pagination, filtering and drill-down navigation rather than unbounded tables.
- Keep TypeScript strict, use the App Router and preserve existing application conventions.
- Treat authentication, credentials, attachments and email actions as security-sensitive.
- Follow the root `AGENTS.md` and `CONTRIBUTING.md` branch, commit and validation rules.

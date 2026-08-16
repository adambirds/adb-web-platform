# AGENTS.md

Scoped guidance for `admin-website/`.

- This is the internal Next.js administration application only.
- Do not add public marketing pages, public SEO content or anonymous lead-generation pages here.
- Preserve the existing authenticated `/admin` functionality and integration with `auth-frontend/` and the Django backend.
- Internal workflows may cover CRM, leads, clients, projects, content, infrastructure, credentials and email.
- Keep TypeScript strict, use the App Router and preserve existing application conventions.
- Treat authentication, credentials and email actions as security-sensitive.
- Follow the root `AGENTS.md` and `CONTRIBUTING.md` branch, commit and validation rules.

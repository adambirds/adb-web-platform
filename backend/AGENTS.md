# AGENTS.md

Scoped guidance for `backend/`.

- This is the shared Django backend for all ADB brands and internal operations.
- Preserve Django, Django Ninja, PostgreSQL, Redis and Celery conventions already present.
- Use Django migrations for persistent model changes and review migrations before committing.
- Keep brand/source attribution explicit for enquiries and other brand-owned records.
- Authentication, credentials and Microsoft Graph/email code are security-sensitive. Read nearby code and tests before editing and do not weaken existing controls.
- Keep API contracts typed and stable for `auth-frontend/`, `admin-website/` and public sites.
- Add tests for behavioural changes and run backend lint/type/test checks.
- Follow the root `AGENTS.md` and `CONTRIBUTING.md` commit/branch rules.

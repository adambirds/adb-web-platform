# AGENTS.md

Scoped guidance for `auth-frontend/`.

- This application owns authentication and account-security flows, including login, sessions, 2FA and passkeys.
- Do not move public marketing pages or internal CRM/admin functionality into this application.
- Authentication behaviour is security-sensitive. Preserve backend contracts and add/update tests for changes.
- Keep TypeScript strict and avoid `any` unless unavoidable and documented.
- Follow existing Vite/React patterns rather than introducing a second framework into this app.
- Follow the root `AGENTS.md` and `CONTRIBUTING.md` branch, commit and validation rules.

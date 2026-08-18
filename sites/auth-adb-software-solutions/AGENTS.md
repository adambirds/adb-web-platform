# AGENTS.md

Scoped guidance for `sites/auth-adb-software-solutions/`.

- This application owns authentication and account-security flows, including login, sessions, 2FA and passkeys.
- It is a Next.js 16 App Router application. Follow App Router conventions and do not reintroduce React Router or Vite.
- Django remains authoritative for sessions, CSRF, authentication, TOTP and WebAuthn. Do not add Auth.js/NextAuth, browser-stored JWTs or a second authentication authority.
- Do not move public marketing pages or internal CRM/admin functionality into this application.
- Authentication behaviour is security-sensitive. Preserve backend contracts and add or update tests for changes.
- Keep TypeScript strict and avoid `any` unless unavoidable and documented.
- Keep browser-only WebAuthn and interactive authentication code in Client Components while using Server Components where they materially simplify non-interactive structure.
- Follow `docs/AUTH_FRONTEND_NEXTJS_MIGRATION.md`, the root `AGENTS.md`, and `CONTRIBUTING.md`.

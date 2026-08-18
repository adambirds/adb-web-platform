# ADB Software Solutions Authentication

This application provides the shared authentication and account-security frontend for the ADB Web Platform. It is built with Next.js 16 using the App Router and talks to the Django backend for all authentication state and security operations.

## Responsibilities

- passkey-first authentication with discoverable WebAuthn credentials;
- email/password authentication as a fallback;
- TOTP two-factor authentication and recovery codes;
- registration and email verification;
- password reset and password changes;
- session/device management;
- passkey enrolment, rename and deletion;
- redirect-based sign-in for the ADB marketing and administration applications.

Django remains the authority for sessions, CSRF, authentication, TOTP and WebAuthn. Do not introduce Auth.js/NextAuth, browser-stored JWTs or another authentication authority into this application.

## Local development

The development port map is:

- Admin: `http://localhost:3000`
- ADB Software Solutions: `http://localhost:3001`
- ADB Web Designs: `http://localhost:3002`
- ADB Technology: `http://localhost:3003`
- Authentication: `http://localhost:3004`
- Django: `http://localhost:8000`

From the repository root:

```bash
pnpm install
pnpm --dir sites/auth-adb-software-solutions dev
```

Build and test with:

```bash
pnpm --dir sites/auth-adb-software-solutions test --passWithNoTests
pnpm --dir sites/auth-adb-software-solutions build
```

## Routes

Public authentication routes:

- `/login`
- `/signup`
- `/forgot-password`
- `/reset-password/[token]`
- `/verify-email/[token]`
- `/logout`

Authenticated account-security routes:

- `/setup-passkey`
- `/setup-2fa`
- `/account`
- `/account/security`

`/account` redirects to `/account/security`.

## Backend API

The frontend calls the Django authentication APIs beneath the configured backend URL, including `/api/auth-service/*` and the CSRF bootstrap endpoint `/api/auth/csrf`.

All authenticated browser requests use Django session cookies with `credentials: "include"`, and mutating requests continue to use Django CSRF protection.

## Environment variables

- `NEXT_PUBLIC_API_URL` - Django origin, default `http://localhost:8000`.
- `NEXT_PUBLIC_APP_URL` - ADB Software Solutions site, default `http://localhost:3001`.
- `NEXT_PUBLIC_ADMIN_URL` - administration application, default `http://localhost:3000`.
- `NEXT_PUBLIC_WEB_DESIGNS_URL` - ADB Web Designs site, default `http://localhost:3002`.
- `NEXT_PUBLIC_TECHNOLOGY_URL` - ADB Technology site, default `http://localhost:3003`.
- `NEXT_PUBLIC_AUTH_URL` - this authentication application, default `http://localhost:3004`.

Only the known ADB application origins and safe relative paths are accepted as redirect targets.

## Migration and security guidance

See `../../docs/AUTH_FRONTEND_NEXTJS_MIGRATION.md` for the migration contract and regression checklist. Authentication changes are security-sensitive: preserve backend contracts and add or update tests whenever behaviour changes.

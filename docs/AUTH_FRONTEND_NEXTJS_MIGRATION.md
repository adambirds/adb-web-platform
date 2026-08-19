# Authentication Frontend Next.js Migration

## Status

**Completed.** This document is retained as the completion record and architectural guardrails for the migration of `sites/auth-adb-software-solutions/` from React/Vite/React Router to Next.js App Router.

The historical migration plan is no longer an outstanding roadmap item. Current operational priorities live in `CURRENT_STATE_AND_FOUNDATION_CHECKLIST.md`.

## Current architecture

`sites/auth-adb-software-solutions/` is a dedicated Next.js authentication/account-security application.

Django remains the authentication and session authority. The frontend does not introduce Auth.js/NextAuth, browser-stored JWT authentication or a second identity/session system.

The application remains independently deployable from:

- the three public Brand sites; and
- the authenticated operations workspace under `sites/adb-software-solutions/.../admin`.

## Preserved authentication capabilities

The migration preserved the established Django-backed flows for:

- email/password login;
- logout;
- registration where enabled;
- email verification;
- forgotten/reset password;
- Django session-cookie authentication;
- CSRF protection;
- TOTP setup/challenge/disable;
- recovery codes;
- WebAuthn/passkey registration;
- discoverable passkey login;
- passkey rename/delete;
- account/session/device management.

Cryptographic verification remains in Django/Python services rather than being moved into Next.js.

## Route principles

The authentication application owns public authentication and protected account/security routes. Existing external URLs and `next`/return flows should remain stable unless a deliberate change is made.

Dynamic token routes use normal App Router dynamic segments for flows such as:

- email verification;
- password reset.

Protected account routes redirect unauthenticated users through the established login flow and preserve validated return destinations.

## Environment/configuration principles

Browser-visible configuration uses `NEXT_PUBLIC_*` values where genuinely required. Secrets never use `NEXT_PUBLIC_*`.

The application must continue to call the shared Django authentication APIs using the established session-cookie/CSRF contract.

Production configuration must keep:

- secure cookies;
- appropriate same-site/domain settings;
- explicit trusted origins/CORS configuration;
- validated return URLs;
- no authentication secrets embedded into the frontend bundle.

## Development/runtime

The authentication frontend uses local port `3004` in the devcontainer/development setup.

Normal commands are the package scripts under `sites/auth-adb-software-solutions/`, including:

```bash
pnpm --dir sites/auth-adb-software-solutions dev
pnpm --dir sites/auth-adb-software-solutions test
pnpm --dir sites/auth-adb-software-solutions build
```

Repository CI validates its tests, production build, filesystem security scan and Docker image.

## Testing expectations

Authentication is security-sensitive. Framework/tooling upgrades or changes to auth APIs must continue to regression-test the critical browser-facing flows, especially:

- password login/logout and redirects;
- email verification;
- password reset;
- CSRF/session persistence;
- TOTP setup and challenge;
- recovery codes;
- passkey registration;
- discoverable passkey login;
- passkey management;
- protected account-route redirects;
- cross-site return URLs.

Unit/component tests are useful, but significant auth changes should also be manually verified against the Django backend before production deployment.

## Guardrails

Do not:

- migrate authentication into the public websites merely for convenience;
- migrate authentication into `/admin`;
- introduce Auth.js/NextAuth as a parallel authority;
- store long-lived authentication tokens in localStorage;
- weaken CSRF/cookie/origin protections;
- move WebAuthn/TOTP verification out of Django without an explicit security architecture decision;
- casually change externally used auth URLs while working on unrelated UI changes.

## Related canonical documents

- `PLATFORM_MASTER_PLAN.md` — overall application architecture and roadmap;
- `PERMISSIONS_AND_ACCESS_MODEL.md` — staff authorisation and scope architecture;
- `CURRENT_STATE_AND_FOUNDATION_CHECKLIST.md` — current operational implementation status.

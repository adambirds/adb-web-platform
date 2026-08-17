# Authentication Frontend Next.js Migration Plan

## Purpose

This document defines the migration of `sites/auth-adb-software-solutions/` from its current React/Vite/React Router implementation to a Next.js 16 App Router application.

The migration is intentionally planned as a dedicated follow-up to the platform-foundation PR rather than being folded into the same change. Authentication is security-sensitive and already contains mature flows for password authentication, email verification, password reset, TOTP, recovery codes, passkeys/WebAuthn and session/device management. The framework migration must preserve those behaviours rather than redesign them casually.

The Django backend remains the authentication authority throughout this migration.

## Goals

The migration should:

- standardise the browser application stack around Next.js, React and TypeScript;
- use Next.js 16 and the App Router from the start;
- preserve the existing visual design and user journeys unless a change is explicitly approved;
- preserve Django session-cookie and CSRF authentication;
- preserve the current Django authentication API contracts;
- preserve passkey/WebAuthn, TOTP, recovery-code and session-management behaviour;
- remove React Router and Vite-specific infrastructure from the authentication application;
- align Docker, CI, linting, testing and environment configuration with the other Next.js applications in the monorepo;
- leave the authentication application independently deployable from the admin and public websites;
- improve typing and test coverage while migrating rather than carrying unnecessary weakly typed API responses forward.

## Non-goals

The migration must not:

- replace Django authentication with Auth.js, NextAuth or another parallel authentication authority;
- move authentication into the admin application;
- move authentication into any public marketing website;
- change password hashing, TOTP generation or WebAuthn cryptographic behaviour;
- introduce a second session implementation;
- redesign the full account/security experience merely because the frontend framework is changing;
- introduce client-portal functionality as part of the migration;
- weaken CSRF, cookie, redirect or origin validation.

## Target application structure

The exact internal file layout may evolve during implementation, but the target should follow normal Next.js 16 App Router conventions.

```text
sites/auth-adb-software-solutions/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── login/
│   │   └── page.tsx
│   ├── signup/
│   │   └── page.tsx
│   ├── forgot-password/
│   │   └── page.tsx
│   ├── reset-password/
│   │   └── [token]/
│   │       └── page.tsx
│   ├── verify-email/
│   │   └── [token]/
│   │       └── page.tsx
│   ├── setup-2fa/
│   │   └── page.tsx
│   ├── setup-passkey/
│   │   └── page.tsx
│   └── account/
│       ├── page.tsx
│       └── security/
│           └── page.tsx
├── components/
├── contexts/
├── lib/
│   ├── api/
│   ├── auth/
│   └── config/
├── public/
├── next.config.ts
├── package.json
└── tsconfig.json
```

Use `src/` only if it makes the application materially clearer and is consistent with the monorepo conventions at migration time. Do not introduce structural churn for its own sake.

## Route mapping

The current authentication routes must continue to exist with equivalent behaviour.

| Current route | Target Next.js route | Notes |
| --- | --- | --- |
| `/login` | `app/login/page.tsx` | Preserve `next` return URL behaviour. |
| `/signup` | `app/signup/page.tsx` | Preserve registration and verification flow. |
| `/verify-email/:token` | `app/verify-email/[token]/page.tsx` | Dynamic route token. |
| `/forgot-password` | `app/forgot-password/page.tsx` | Preserve non-enumerating UX/API behaviour. |
| `/reset-password/:token` | `app/reset-password/[token]/page.tsx` | Dynamic route token. |
| `/logout` | implementation decision | Prefer a deliberate page/action flow rather than hidden framework magic. |
| `/setup-passkey` | `app/setup-passkey/page.tsx` | Browser WebAuthn APIs require client-side interaction. |
| `/setup-2fa` | `app/setup-2fa/page.tsx` | Preserve setup/confirmation/recovery-code handling. |
| `/account` | `app/account/page.tsx` | Continue redirecting to the security dashboard unless product requirements change. |
| `/account/security` | `app/account/security/page.tsx` | Password, passkeys, TOTP and session/device management. |

Any historic aliases or externally used URLs discovered during migration must either be retained or receive explicit redirects.

## Authentication authority and request model

Django remains responsible for:

- creating and validating sessions;
- authentication state;
- staff/client identity rules;
- CSRF tokens;
- password validation and changes;
- verification and password-reset tokens;
- TOTP and recovery codes;
- passkey/WebAuthn challenge generation and verification;
- session/device tracking;
- rate limiting;
- security logging.

Next.js is the presentation/application framework only.

The browser should continue to communicate with the Django backend using the established cookie-based session and CSRF model. Do not add JWT storage in local storage or another token scheme simply to make the frontend migration easier.

## Server and Client Components

Prefer Server Components for static layout and non-interactive presentation, but do not force security workflows into Server Components when they fundamentally require browser APIs or immediate interaction.

Client Components are expected for functionality such as:

- WebAuthn/passkey registration and authentication;
- interactive login/signup forms where the existing Django API is called directly;
- TOTP setup/verification UI;
- recovery-code display/copy behaviour;
- session/device revocation controls;
- password-change controls;
- browser-only return URL handling where necessary.

Keep client boundaries narrow. Shared presentational components should remain server-compatible where practical.

## Route protection

Do not rely on Next.js route protection as the security boundary. Django remains authoritative for authenticated API access.

The account/security UI should provide a good redirect experience for unauthenticated users. If Next.js `proxy.ts` is used, use it only for lightweight routing/optimistic checks. It must not become the definitive authorisation layer or perform slow backend session lookups for every request without a deliberate architecture decision.

Next.js 16 renamed the old Middleware convention to Proxy, so new code must use current Next.js 16 conventions rather than introducing deprecated `middleware.ts` patterns.

## Return URL security

The existing `next`/return URL behaviour must be retained and tested.

Allowed return destinations should remain limited to:

- relative paths that cannot become protocol-relative redirects;
- explicitly configured ADB application origins.

The migration must include tests for:

- accepted relative paths;
- accepted configured ADB origins;
- rejected protocol-relative URLs such as `//example.com`;
- rejected external origins;
- malformed URL input;
- a safe default destination when `next` is absent or invalid.

## Environment configuration

Replace Vite-specific `VITE_*` variables with deliberately named Next.js configuration.

Browser-exposed values must use `NEXT_PUBLIC_*` only where they genuinely need to be available in client bundles. Server-only values must not be given a `NEXT_PUBLIC_` prefix.

Likely public configuration includes:

- Django API base URL;
- admin application URL;
- ADB Software Solutions public-site URL;
- ADB Web Designs URL;
- ADB Technology URL;
- authentication application canonical URL where required for redirect validation.

The migration PR must update:

- `.env.example`;
- Docker build arguments/environment;
- GitHub Actions workflow configuration;
- devcontainer documentation and port forwarding;
- README/environment documentation.

No secrets belong in these frontend URL values.

## Development port

The current Vite application has been temporarily standardised on port `5175` so local development is internally consistent before migration.

The Next.js migration should move the authentication application to the normal `300x` application range and update all dependent configuration atomically. The exact port should be selected after checking the existing admin/public-site assignments so there are no collisions.

Do not leave compatibility configuration pointing at both the old Vite port and the new Next.js port after the migration is complete.

## API client migration

The existing auth API utility should be migrated rather than rewritten blindly.

During the migration:

- preserve CSRF-aware fetch behaviour;
- preserve `credentials: "include"` semantics;
- retain the existing backend endpoint contracts;
- split the large API module into coherent areas if doing so improves maintainability;
- replace avoidable `unknown`/generic response shapes with explicit TypeScript contracts;
- do not log authentication response bodies, tokens, CSRF values or credential material;
- keep error handling safe and user-friendly without leaking sensitive server details.

Good candidate modules include:

```text
lib/api/
├── client.ts
├── auth.ts
├── passkeys.ts
├── two-factor.ts
└── sessions.ts
```

This is a suggested boundary, not a requirement to create abstraction for abstraction's sake.

## WebAuthn/passkeys

Passkey flows are a migration risk and require explicit regression testing.

Verify at minimum:

- discoverable/passkey login;
- registration ceremony;
- challenge parsing and encoding/decoding;
- authenticator response serialisation;
- passkey listing;
- passkey rename;
- passkey deletion;
- browser cancellation/error behaviour;
- secure-context assumptions in production;
- correct RP ID/origin configuration from Django.

Do not move WebAuthn verification logic into Next.js.

## TOTP and recovery codes

Verify at minimum:

- current 2FA status;
- initial setup;
- QR/secret presentation;
- confirmation with a valid code;
- invalid/expired code behaviour;
- login challenge flow;
- recovery-code login;
- recovery-code regeneration;
- disabling 2FA;
- password confirmation where currently required.

Recovery codes and TOTP secrets must never appear in logs.

## Session and device management

Verify:

- current authenticated user bootstrap;
- session/device listing;
- current-session identification;
- revoking another session;
- revoking all other sessions;
- expected behaviour if the current session expires while the page is open;
- redirect behaviour after logout.

## Testing strategy

The migration is not complete merely because `next build` succeeds.

### Unit/component tests

Retain and expand tests for:

- form validation;
- redirect validation;
- authentication provider/state handling where retained;
- API-client response transformations;
- passkey utility conversion logic where testable;
- reusable controls.

Tests must mock backend requests deliberately rather than attempting to call `localhost:8000` during isolated frontend CI.

### Route/flow tests

At minimum verify page rendering and transition behaviour for:

- login;
- signup;
- verification;
- password reset;
- 2FA challenge/setup;
- passkey setup;
- account security;
- unauthenticated account access;
- safe return URLs.

### Backend regression tests

Do not remove or weaken existing Django authentication tests. If the migration reveals ambiguities in frontend/backend contracts, add backend tests before changing contracts.

### Manual browser verification

Because WebAuthn and cookie/origin behaviour cannot be exhaustively represented by simple component tests, the PR handoff should include a manual verification checklist for local browser testing.

## CI and Docker

The migrated auth app must continue to have its own CI workflow and Docker image.

CI should validate:

- root frozen pnpm install;
- frontend tests;
- ESLint/Prettier/Stylelint through the repository lint suite;
- TypeScript via the Next.js build;
- production `next build`;
- Trivy filesystem/container checks currently used by the project;
- Docker image build on pull requests;
- DigitalOcean registry push only under the repository's established main/tag policy.

The Docker image should run the Next.js application using the same deployment principles as the other Next.js apps rather than retaining the Vite static-Nginx image after migration.

## Shared packages

Use shared workspace packages only where they are genuinely shared.

Potentially reusable items include:

- low-level UI primitives;
- API request helpers;
- strict shared TypeScript contracts;
- lint/TypeScript configuration.

Do not move authentication-specific screens or security logic into generic packages merely to reduce file count.

## Implementation order

Recommended migration sequence:

1. Confirm current auth routes, backend contracts and tests before changing framework code.
2. Introduce the Next.js 16 application shell/configuration.
3. Establish environment and API-client foundations.
4. Migrate shared layout/design primitives.
5. Migrate login/logout and authenticated-user bootstrap.
6. Migrate signup/email-verification/password-reset flows.
7. Migrate TOTP/recovery-code flows.
8. Migrate WebAuthn/passkey flows.
9. Migrate account/security and session/device management.
10. Remove React Router/Vite-specific files and dependencies.
11. Replace the Vite Docker runtime with the Next.js runtime.
12. Update CI, devcontainer ports, docs and environment examples.
13. Run complete frontend/backend CI.
14. Perform manual browser regression of password, TOTP and passkey flows.
15. Merge only after all existing auth capabilities are accounted for.

Prefer keeping the application usable throughout the branch where practical, but a clean framework migration is more important than preserving artificial intermediate commits that cannot run.

## Completion criteria

The migration is complete when:

- the auth application runs on Next.js 16 App Router;
- React Router and Vite are removed from that application;
- every existing user-facing authentication/account route has an equivalent working route;
- Django remains the single authentication/session authority;
- return URL validation remains safe;
- CSRF/session behaviour works locally and in the production-domain configuration;
- login/logout work;
- signup and email verification work;
- password reset/change work;
- TOTP and recovery-code workflows work;
- passkey/WebAuthn workflows work;
- session/device management works;
- unit/component tests do not make real backend requests;
- repository lint passes;
- auth CI passes;
- Docker build passes;
- dependent admin/public application redirects use the new canonical auth URL/port;
- Vite-specific files, environment names and documentation are removed;
- the canonical platform documentation reflects the new stack.

## Work after this migration

After the authentication frontend is successfully migrated, the next planned operational development phase is Clients + Contacts.

Separately, the existing Next.js applications should receive a deliberate framework-modernisation pass so that the repository converges on a consistent supported Next.js 16 stack. That broader dependency upgrade should remain separate from the auth migration unless combining them is demonstrably safer and easier to review.

# Contributing

This repository contains the shared ADB backend, authentication and administration applications, plus the public ADB Software Solutions and ADB Web Designs websites.

Prefer straightforward implementations and measurable benefits over infrastructure or abstractions added pre-emptively.

## Development environment

The recommended environment is VS Code with Dev Containers.

```bash
git clone git@github.com:adb-software-solutions/adbsoftwaresolutions.co.uk.git
cd adbsoftwaresolutions.co.uk
code .
```

Then choose **Dev Containers: Reopen in Container**.

## Repository layout

- `backend/` — Django backend and shared business platform.
- `auth-frontend/` — authentication/account frontend.
- `admin-website/` — internal Next.js administration frontend.
- `sites/adb-software-solutions/` — public ADB Software Solutions site.
- `sites/adb-web-designs/` — public ADB Web Designs site.
- `packages/` — shared TypeScript packages.
- `tools/` — development, linting and test scripts.

## Branches and commits

Create a focused branch from `main`, keep commits small and coherent, and submit the change through a pull request. This is the default workflow for all changes.

Large features, changes containing multiple features and work expected to need several follow-up commits must always use a dedicated branch and pull request; they must not be committed directly to `main`.

Keep repository history linear. Fetch and rebase your branch onto the latest target branch before opening or updating a pull request; do not merge `main` into your working branch and do not create merge commits. If a published rebase requires a non-fast-forward update, use `git push --force-with-lease`, never plain `--force`.

Commit messages are checked with gitlint and must use:

```text
<type>: <Imperative summary>.
```

Allowed lowercase types are:

- `feat`
- `fix`
- `refactor`
- `test`
- `docs`
- `style`
- `build`
- `ci`
- `deployment`
- `chore`

Start the summary with a capital letter, use imperative mood, end with a period and keep the complete title at or below 76 characters.

Examples:

```text
fix: Fix issue with authentication.
refactor: Separate the internal admin site.
ci: Update frontend workflow paths.
deployment: Add public website image build.
```

Run `tools/commit-message-lint` before pushing and correct every violation.

## Quality checks

Stage newly created files before linting, then run:

```bash
tools/lint
tools/test-all
```

Run application-specific tests and builds for the areas changed. Python should pass Ruff, mypy and pytest. Frontend code should pass ESLint, Prettier, Stylelint and its tests/build where applicable.

Do not weaken checks to make a change pass.

## Dependencies

Python dependencies remain managed by the existing backend requirements tooling. JavaScript dependencies are managed with pnpm. The repository uses a pnpm workspace to make shared packages available while retaining per-project lockfiles.

Avoid adding a dependency when the same functionality can be implemented clearly with the standard library or existing project dependencies.

## Pull requests

A pull request should describe what changed, why it changed, how it was tested and any operational or security implications. Update tests for behavioural changes and documentation for configuration, API, deployment or user-visible changes.

## Security

Never commit production secrets, credentials, private keys, access tokens or real local environment files. Authentication, passkeys, 2FA, credential storage and Microsoft Graph/email integration are security-sensitive areas and require deliberate review.

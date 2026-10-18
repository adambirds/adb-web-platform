# ADB Web Platform

Shared web and business-operations platform for the ADB brands.

The repository contains the three ADB public websites, a shared authentication/account application, the internal operations workspace, and the Django backend that powers public content and internal business workflows.

## Applications

All browser-facing applications live under `sites/`:

- `sites/adb-software-solutions/` — combined ADB Software Solutions Next.js application. Public marketing routes live alongside the authenticated internal operations workspace under `/admin`.
- `sites/adb-web-designs/` — public ADB Web Designs website.
- `sites/adb-technology/` — public ADB Technology website for cloud/DevOps, infrastructure, migrations, deployment pipelines and server work.
- `sites/auth-adb-software-solutions/` — shared authentication/account-security application for login, password/account flows, passkeys, TOTP and session management.

The shared Django backend lives at `backend/`; reusable frontend/tooling packages live under `packages/`.

There is no separate admin frontend deployment. The internal operations workspace is part of `sites/adb-software-solutions/` and is served under `/admin`.

## Platform model

The platform is one shared operational system serving multiple ADB Brands.

Public marketing pages are owned in code. Dynamic public content such as blog posts, testimonials, FAQs and public case studies is managed through the CMS and explicitly Brand-scoped.

Operational data uses a separate ownership model: resources are Client-owned or explicitly Internal. Brand and Client are different concepts. For example, a Ticket may belong to ADB Web Designs while also belonging to a specific Client.

The internal platform covers or is being developed to cover:

- Clients and Contacts;
- CRM and Leads;
- Projects;
- Tasks and work planning;
- Time Tracking;
- Ticket Queues and communications;
- Microsoft Graph-backed Shared Mailboxes;
- Knowledge Base documentation;
- credential/secret management;
- Infrastructure inventory;
- configurable dashboards and Calendar/work planning;
- Client-context search and cross-domain workspaces;
- later client portals, quotes, contracts, invoicing and payments.

The ticketing/communications foundation is implemented, including Graph mailbox sync/replies, website contact-form ingestion, vendor routing and governed attachments. The operations workspace includes create/edit/detail workflows across its major domains, plus monitoring and the GitHub dashboard. The canonical implementation checklist records completed work and remaining gaps.

Permissions are backend-authoritative. Django permissions describe capabilities while explicit scopes restrict which Clients and Ticket Queues a staff user can access. Sensitive operations such as credential reveal/copy are separate capabilities and must be audit logged.

## Architecture documentation

Before changing domain architecture, authentication, authorisation, CMS behaviour, ticketing, credentials, infrastructure or Client ownership, read:

- `docs/PLATFORM_MASTER_PLAN.md` — canonical product and architecture plan.
- `docs/CURRENT_STATE_AND_FOUNDATION_CHECKLIST.md` — current implementation state and ordered operational roadmap.
- `docs/PERMISSIONS_AND_ACCESS_MODEL.md` — permissions and object-scope architecture.
- `docs/DOMAIN_MODEL_AUDIT.md` — decisions from the Django model audit.
- `docs/TICKETING_ARCHITECTURE.md` — ticketing and communications architecture.
- `docs/MICROSOFT_GRAPH_TICKETING_SETUP.md` — complete Microsoft 365/Graph/Exchange RBAC setup runbook.

Older root-level planning documents are historical context only. Where they conflict with canonical `docs/` architecture, the canonical documents take precedence.

## Current development priorities

Before public-site development becomes the main focus, the internal platform roadmap prioritises:

1. Client/Contact CRUD and complete Client workspaces, plus Users & Access.
2. Lead, Project and Task detail/CRUD/workflow completion.
3. IT Glue-style Knowledge Base, Credentials and Infrastructure workspaces.
4. integrated timer-based Time Tracking and Calendar/work planning.
5. complete cross-domain Client context and configurable per-user Dashboard widgets/layouts.

See `docs/CURRENT_STATE_AND_FOUNDATION_CHECKLIST.md` for the detailed implementation checklist.

## Shared packages

- `packages/ui/` — brand-neutral shared UI primitives and types.
- `packages/api-client/` — shared API helpers/contracts.
- `packages/observability/` — `/healthz`, Prometheus `/metrics` and JSON console logs, shared by the four frontends.
- `packages/eslint-config/` — shared ESLint configuration.
- `packages/typescript-config/` — shared TypeScript configuration.

## Setup and configuration

This is the single starting point for development and production setup. The
[environment template](.devcontainer/.env.example) lists every application
runtime variable, including optional integrations. Detailed domain runbooks
remain linked below for troubleshooting and rotation.

### 1. Prepare the development environment

Install Docker with Compose and the VS Code Dev Containers extension. Before
opening the container, copy the template on your host:

```bash
cp .devcontainer/.env.example .devcontainer/.env
```

Generate two **different** secrets with host Python 3 (no packages required):

```bash
# Paste this output into SECRET_KEY.
python3 -c 'import secrets; print(secrets.token_urlsafe(64))'

# Paste this output into CREDENTIAL_ENCRYPTION_KEYS.
python3 -c 'import base64, secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())'
```

Keep these values outside Git. `SECRET_KEY` is required to start Django.
`CREDENTIAL_ENCRYPTION_KEYS` is required to create/read Vault secrets. GitHub and
Graph use Infisical-injected signing material directly. This encryption key is not the Django secret and must stay
stable across restarts. Existing encrypted credentials need the original keys;
back them up with the database. To rotate, configure `new-key,old-key` and keep
old keys until all affected secrets have been re-encrypted and verified.

Leave the local PostgreSQL and Redis URLs as supplied. Open the folder in VS Code
and choose **Dev Containers: Reopen in Container**. The post-create script installs
pnpm dependencies and runs migrations. Inside the container:

```bash
python backend/manage.py createsuperuser
```

Run the following in separate terminals:

```bash
# ASGI is required for the live events stream; this helper uses Uvicorn.
.devcontainer/scripts/start-backend
pnpm dev:software-solutions
pnpm dev:auth
.devcontainer/scripts/start-celery-general
.devcontainer/scripts/start-celery-beat
```

The worker and Beat are needed for monitoring, expiry/metadata refreshes,
GitHub webhook processing/recovery, mailbox sync and attachment scanning.
Monitor workers, queue depths, task history, per-task logs and scheduled jobs at
<http://localhost:3000/admin/celery>. Access requires an active staff superuser.
The dashboard is part of the existing backend and operations frontend; no extra
service, OAuth registration or forwarded port is required. See
[Celery operations](docs/CELERY_DASHBOARD.md).

Optional processes:

```bash
pnpm dev:web-designs
pnpm dev:technology
```

| Service                         | Local URL                                               |
| ------------------------------- | ------------------------------------------------------- |
| Backend/API                     | <http://localhost:8000>                                 |
| Django bootstrap admin          | <http://localhost:8000/admin/>                          |
| Software Solutions + operations | <http://localhost:3000> / <http://localhost:3000/admin> |
| Authentication/account frontend | <http://localhost:3004>                                 |
| Web Designs                     | <http://localhost:3002>                                 |
| Technology                      | <http://localhost:3003>                                 |

Compose injects `.devcontainer/.env` into the `app` container. Django does **not**
automatically read that file when run outside Compose. After changing it, use
**Dev Containers: Rebuild Container**, then restart backend, worker, Beat and
frontend processes. Merely restarting Python in the old container retains the
old injected environment. Frontend `.env.local` files can also configure local
Next.js apps; already-injected process variables take precedence.

### 2. Backend variable reference

Set these in the environment of the API, Celery worker and Beat.
Production values come from your deployment
secret manager rather than the development `.env` file.

| Variable                                | Development value / how to obtain it                               | Production requirement                                                                                    |
| --------------------------------------- | ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| `SECRET_KEY`                            | Generate with the command above                                    | Unique secret, stable across API/worker replicas                                                          |
| `CREDENTIAL_ENCRYPTION_KEYS`            | Generate a Fernet key above; comma-separated key ring for rotation | Same usable key ring wherever Vault secrets are decrypted                                                 |
| `DEBUG`                                 | `1`                                                                | `0`                                                                                                       |
| `DEBUG_TOOLBAR_ENABLED`                 | `0`; optionally `1` for local debugging                            | `0`                                                                                                       |
| `SITE_DOMAIN`                           | `localhost`                                                        | Parent domain, e.g. `adbsoftwaresolutions.co.uk`; no scheme/path/subdomain prefix                         |
| `ADMIN_FRONTEND_URL`                    | `http://localhost:3000`                                            | Combined Software Solutions origin; admin lives under `/admin`                                            |
| `AUTH_FRONTEND_URL`                     | `http://localhost:3004`                                            | Auth origin, e.g. `https://auth.adbsoftwaresolutions.co.uk`; used in account emails                       |
| `SOFTWARE_SOLUTIONS_FRONTEND_URL`       | `http://localhost:3000`                                            | Software Solutions public origin                                                                          |
| `WEB_DESIGNS_FRONTEND_URL`              | `http://localhost:3002`                                            | `https://adbwebdesigns.co.uk` or the configured brand origin                                              |
| `TECHNOLOGY_FRONTEND_URL`               | `http://localhost:3003`                                            | `https://adbtechnology.co.uk` or the configured brand origin                                              |
| `FRONTEND_URL`                          | `http://localhost:3000`; compatibility alias                       | Same Software Solutions origin                                                                            |
| `SQL_ENGINE`                            | `django.db.backends.postgresql`                                    | Keep PostgreSQL                                                                                           |
| `SQL_DATABASE`                          | `adbsoftwaresolutions_dev`                                         | Database name from your PostgreSQL provisioning output                                                    |
| `SQL_USER`                              | `adbsoftwaresolutions`                                             | Database user from your provider                                                                          |
| `SQL_PASSWORD`                          | Local Compose password in the template                             | Database password from your provider/secret manager                                                       |
| `SQL_HOST`                              | `db` inside Compose                                                | Private database hostname supplied by your provider                                                       |
| `SQL_PORT`                              | `5432`                                                             | Provider's PostgreSQL port                                                                                |
| `SQL_SSL`                               | `disable`                                                          | Provider-required libpq SSL mode, usually `require` or `verify-full` with its CA provisioned              |
| `CACHE_BACKEND_URL`                     | `redis://redis-cache:6379/0`                                       | Shared default cache, locks, rate limits, GitHub token cache and SSE Pub/Sub                              |
| `SESSION_BACKEND_URL`                   | `redis://redis-session:6379/0`                                     | Dedicated session cache; URL from your Redis provider                                                     |
| `CELERY_BROKER_URL`                     | `redis://redis-celery:6379/0`                                      | Task broker URL from your Redis provider                                                                  |
| `CELERY_RESULT_BACKEND`                 | `redis://redis-celery:6379/1`                                      | Result backend URL; separate from broker/cache/sessions                                                   |
| `CELERY_QUEUE`                          | `general`                                                          | Production worker entrypoint consumes this queue; keep `general` for current tasks                        |
| `CELERY_CONCURRENCY`                    | `2`                                                                | Worker process count, sized for available memory/CPU                                                      |
| `TICKETING_GRAPH_SYNC_INTERVAL_SECONDS` | `60`                                                               | Mailbox dispatch interval; integer >= 30; restart Beat after changing                                     |
| `TICKETING_GRAPH_SYNC_LOCK_SECONDS`     | `900`                                                              | Per-mailbox lock lifetime; integer >= 60; size above a normal sync run                                    |
| `TICKETING_MALWARE_SCANNING_ENABLED`    | `0`                                                                | `1` when a scanner is provisioned and attachments must pass scanning                                      |
| `TICKETING_CLAMAV_HOST`                 | `clamav`                                                           | Private clamd hostname reachable from scanning workers                                                    |
| `TICKETING_CLAMAV_PORT`                 | `3310`                                                             | clamd TCP port                                                                                            |
| `TICKETING_CLAMAV_TIMEOUT_SECONDS`      | `30`                                                               | Positive scanner timeout in seconds                                                                       |
| `LOG_FORMAT`                            | `text`                                                             | `json` (set in the images): one JSON object per line on stdout, for Loki                                  |
| `LOG_LEVEL`                             | `INFO`                                                             | `INFO` unless investigating                                                                               |
| `SERVICE_NAME`                          | Empty                                                              | Set in each image to its component, e.g. `adb-web-platform-backend`; the `service` field of each log line |

Redis credentials belong in the URL, for example
`rediss://username:password@private-host:port/0` for TLS; URL-encode special
characters in credentials. Redis Pub/Sub uses the default cache connection, so
**SSE requires no additional Redis service or logical database**. Development
already has three Redis services: cache, sessions and Celery, with Celery results
on database 1. All API replicas and workers must share the same default cache
endpoint/channel namespace. Do not flush the session or broker stores as a cache
maintenance operation.

### 3. Account verification and password-reset email

Django application mail (account verification, password resets and staff
invitations) uses Microsoft Graph with the same Infisical tenant/client/certificate
configuration as Ticketing. SMTP host, port, login, TLS and backend variables are
no longer needed. Set only the sending address:

```dotenv
DEFAULT_FROM_EMAIL=no-reply@adbsoftwaresolutions.co.uk
```

Create this address as a Microsoft 365 **Shared Mailbox**, and ensure it is covered
by the Entra application's existing scoped Exchange `Application Mail.Send`
assignment. With the documented dynamic SharedMailbox scope, it enters scope
automatically. It does **not** need adding to ADB's Ticketing mailbox list unless
its incoming messages should also become Tickets. Configure the Graph variables
in [the Microsoft 365 setup section](#5-microsoft-365--graph-shared-mailboxes).

Local development sends through Graph too. No certificate material or mail bodies
are copied into application mail settings, Tickets or the audit trail. Production
may set another authorised Shared Mailbox as `DEFAULT_FROM_EMAIL`; individual
application emails cannot select an arbitrary sending mailbox. Django's server
error sender uses the same address. Graph's 202 response means accepted for
processing, rather than proof of final delivery. See
[Microsoft's sendMail reference](https://learn.microsoft.com/en-us/graph/api/user-sendmail?view=graph-rest-1.0).

### 4. GitHub App: repositories, issues, PRs and Actions

Configure the Vault first (step 1), then register **one GitHub App** for all
organisations and your personal account:

1. Open [new organisation App](https://github.com/organizations/adb-software-solutions/settings/apps/new)
   or [new personal App](https://github.com/settings/apps/new). Choose a name,
   your platform homepage and installation on **any account**. An App private to
   its owning account cannot serve the other organisations.
2. Enable webhooks. Set the URL to
   `https://api.<SITE_DOMAIN>/api/integrations/github/webhook`. Local testing needs
   a public HTTPS tunnel forwarding to backend port 8000. Generate a separate
   random webhook secret (the `secrets.token_urlsafe(64)` command above works)
   and enter the same value in GitHub and `GITHUB_WEBHOOK_SECRET`.
3. Set repository permissions: **Metadata: Read**, **Contents: Read**,
   **Issues: Read**, **Pull requests: Read**, **Actions: Read and write**.
   Actions write permits dispatch/rerun; the platform separately controls who
   can use those actions.
4. Subscribe to `repository`, `issues`, `pull_request`, `push`, `workflow_run`
   and `workflow_job`. Installation lifecycle/access events are also delivered.
5. In the App's General settings, copy the numeric **App ID** and the slug from
   its public URL `https://github.com/apps/<slug>`. Generate/download a private
   key under **Private keys**. Store the complete unencrypted GitHub-generated
   RSA PEM in Infisical as `GITHUB_APP_PRIVATE_KEY`. Inject it into the API,
   worker and Beat environments; no application Vault credential is needed.
   Multiline PEM and literal `\n` escapes are supported. For rotation, update
   the key in Infisical and redeploy all backend processes before revoking the
   old key in GitHub. Keep the private key out of Git and frontend variables.
6. Set the following on the API and Celery processes, then recreate/restart:

    | Variable                 | Source                                                                       |
    | ------------------------ | ---------------------------------------------------------------------------- |
    | `GITHUB_APP_ID`          | Numeric App ID from General settings; not OAuth Client ID or installation ID |
    | `GITHUB_APP_SLUG`        | `<slug>` from the App's public GitHub URL                                    |
    | `GITHUB_APP_PRIVATE_KEY` | Complete signing RSA PEM from Private keys, injected directly by Infisical   |
    | `GITHUB_WEBHOOK_SECRET`  | Secret you generated and entered in the App webhook settings                 |

7. From **Install App**, install the same App on each required account. Select
   **All repositories** if newly created repositories should join automatically.
   Direct installation-management links:

    | Account                | Installed Apps / repository access                                                         |
    | ---------------------- | ------------------------------------------------------------------------------------------ |
    | adb-software-solutions | [Settings](https://github.com/organizations/adb-software-solutions/settings/installations) |
    | adb-web-designs        | [Settings](https://github.com/organizations/adb-web-designs/settings/installations)        |
    | VastDesk               | [Settings](https://github.com/organizations/VastDesk/settings/installations)               |
    | vanderheim-village     | [Settings](https://github.com/organizations/vanderheim-village/settings/installations)     |
    | adambirds              | [Personal settings](https://github.com/settings/installations)                             |
    | adb-technology         | [Settings](https://github.com/organizations/adb-technology/settings/installations)         |
    | switchonyourcode       | [Settings](https://github.com/organizations/switchonyourcode/settings/installations)       |

8. In `/admin/github` → **Connections**, choose ownership and approve each
   pending installation as Internal or the correct Client, then connect and
   synchronise. For manual connection, the installation settings **Configure**
   URL contains the installation ID. It is separate from the App ID.
9. Save your GitHub username in the dashboard for My work filters. Verify
   repository import, a signed webhook delivery, PR updates and an Actions run.
   Run the `general` worker and Beat; live UI updates also need the shared SSE
   deployment settings below.

Leave all four GitHub variables empty if you are not enabling this integration.
No personal access token, GitHub OAuth client secret or per-organisation
environment variable is required for the dashboard.
[GitHub registration documentation](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app)
and the [GitHub integration runbook](docs/GITHUB_APP_SETUP.md) cover changes,
permissions, rotation and troubleshooting.

### 5. Microsoft 365 / Graph Shared Mailboxes

Graph configuration is injected from **Infisical** into API and Celery worker
runtime environments. Tenant/client IDs, certificate and private key are not
copied into the database or application credential Vault. Settings manages
mailboxes and automatically recognises the configured environment connection.

| Variable                                 | Where to get it                                                    |
| ---------------------------------------- | ------------------------------------------------------------------ |
| `MICROSOFT_GRAPH_TENANT_ID`              | Entra App registration Overview: Directory (tenant) ID             |
| `MICROSOFT_GRAPH_CLIENT_ID`              | Same Overview: Application (client) ID                             |
| `MICROSOFT_GRAPH_PRIVATE_KEY`            | Entire RSA PEM private-key contents, stored as an Infisical secret |
| `MICROSOFT_GRAPH_CERTIFICATE`            | Entire matching public PEM certificate, also uploaded to Entra     |
| `MICROSOFT_GRAPH_PRIVATE_KEY_PASSPHRASE` | Private-key passphrase if encrypted; otherwise empty               |

Keep these in the backend runtime secret scope in Infisical and ensure its
runtime identities inject them into the API and workers. They must
not enter frontend `.ci.env` files or `NEXT_PUBLIC_*` variables. For local testing,
set them in the untracked `.devcontainer/.env`. PEM values accept actual newlines
or literal `\n` sequences inside a quoted dotenv value. Leave the four required
values empty when Graph is disabled.

Graph also needs database/Redis/Celery configuration. Optional scheduling settings
are `TICKETING_GRAPH_SYNC_INTERVAL_SECONDS` (60) and
`TICKETING_GRAPH_SYNC_LOCK_SECONDS` (900). This environment-backed connection does
**not** require `CREDENTIAL_ENCRYPTION_KEYS`; the application Vault and the GitHub
signing integration still do.

The platform uses one Entra application and certificate-backed connection per
tenant, reusable across enabled Shared Mailboxes:

1. Open [Microsoft Entra](https://entra.microsoft.com/) → **Entra ID → App
   registrations → New registration**. Choose a single-tenant application.
   No interactive redirect URL is required for background app-only mail access.
   Copy **Directory (tenant) ID** and **Application (client) ID** from Overview.
2. Provision an RSA signing certificate/private key. A local/test example,
   created **outside the repository**:

    ```bash
    mkdir -p "$HOME/.adb-secrets/graph"
    chmod 700 "$HOME/.adb-secrets/graph"
    openssl req -x509 -newkey rsa:3072 -sha256 -days 365 -nodes \
      -keyout "$HOME/.adb-secrets/graph/ticketing.key.pem" \
      -out "$HOME/.adb-secrets/graph/ticketing.cert.pem" \
      -subj "/CN=ADB Business Platform Ticketing"
    chmod 600 "$HOME/.adb-secrets/graph/ticketing.key.pem"
    ```

    Upload **only the public certificate** to the App's **Certificates & secrets
    → Certificates**. Use a managed certificate/rotation process in production.

3. In Entra **Enterprise applications**, find the App and copy its **Object ID**.
   Exchange needs this **service principal** Object ID, not the Object ID of the
   App registration. Set `$AppId` and `$ServicePrincipalObjectId` below from
   these screens.
4. On an administrator workstation, install/connect Exchange Online PowerShell
   and configure RBAC for Applications:

    ```powershell
    Install-Module -Name ExchangeOnlineManagement -Scope CurrentUser
    Import-Module ExchangeOnlineManagement
    Connect-ExchangeOnline
    $AppId = "<APPLICATION-CLIENT-ID>"
    $ServicePrincipalObjectId = "<ENTERPRISE-APPLICATION-OBJECT-ID>"
    New-ServicePrincipal -AppId $AppId -ObjectId $ServicePrincipalObjectId `
      -DisplayName "ADB Business Platform Ticketing"
    New-ManagementScope -Name "ADB Ticketing Shared Mailboxes" `
      -RecipientRestrictionFilter "RecipientTypeDetails -eq 'SharedMailbox'"
    New-ManagementRoleAssignment -Name "ADB Ticketing Mail ReadWrite" `
      -App $ServicePrincipalObjectId -Role "Application Mail.ReadWrite" `
      -CustomResourceScope "ADB Ticketing Shared Mailboxes"
    New-ManagementRoleAssignment -Name "ADB Ticketing Mail Send" `
      -App $ServicePrincipalObjectId -Role "Application Mail.Send" `
      -CustomResourceScope "ADB Ticketing Shared Mailboxes"
    Test-ServicePrincipalAuthorization -Identity $ServicePrincipalObjectId `
      -Resource "<intended-shared-mailbox-address>"
    Test-ServicePrincipalAuthorization -Identity $ServicePrincipalObjectId `
      -Resource "<licensed-user-mailbox-address>"
    ```

    Reuse existing service principals/scopes/assignments rather than recreating
    them. Both roles must be in scope for the intended Shared Mailbox and out of
    scope for the licensed UserMailbox. Do not also grant broad Entra Graph Mail
    application permissions: those grants are additive and can defeat the
    Exchange scope. See [Microsoft's RBAC documentation](https://learn.microsoft.com/en-us/exchange/permissions-exo/application-rbac).

5. Store the tenant ID, client ID, certificate PEM, private-key PEM and optional
   passphrase under the variables above in Infisical. Upload only the public
   certificate to Entra. Configure your deployment to inject those variables into
   backend/worker processes; for local testing use `.devcontainer/.env` and
   rebuild the container to load changes.
6. Apply migrations, inject the Graph variables and deploy the API and workers.
   The app reads them directly and automatically exposes the connection in
   `/admin/settings`. There is no bootstrap command or application credential to
   create. Only a stable connection routing/status record is stored, so mailbox
   associations survive redeployments while real IDs and signing material remain
   in Infisical. Add Shared Mailboxes with email, Brand, purpose and default Ticket
   Queue, then verify access before enabling them. Create Microsoft-side Shared
   Mailboxes in the [Microsoft 365 admin centre](https://admin.microsoft.com/).

7. Start the `general` worker and Beat; verify inbound sync and an outbound reply.
   Adding another Shared Mailbox normally needs only its Microsoft mailbox and
   an enabled platform Mailbox row, not another certificate or RBAC assignment.

Graph mailbox processing currently uses scheduled delta sync, not an inbound
Microsoft webhook. Do not configure a Graph webhook/tunnel for this feature.
Certificate updates are manual: upload the new public certificate to Entra,
update the matching certificate/key/passphrase secrets in Infisical, and redeploy
the API and Celery workers. New processes read the updated environment. No app
Vault update or setup command is needed for routine certificate
rotation; verify mailbox access before retiring the old Entra certificate.

The [full Graph runbook](docs/MICROSOFT_GRAPH_TICKETING_SETUP.md) covers alternative
scopes, propagation delays, verification and certificate rotation.

### 6. Optional malware scanning

To enable attachment scanning, set this value before recreating the
devcontainer, and start the scanner service:

```dotenv
TICKETING_MALWARE_SCANNING_ENABLED=1
```

For local development, start the scanner explicitly with
`docker compose -f .devcontainer/docker-compose.yml --profile malware-scanning up -d clamav`.

The template's `TICKETING_CLAMAV_*` values already target that service. Production
needs a clamd service reachable privately from workers, with maintained signature
databases. Enabling scanning without a working scanner keeps governed attachments
quarantined. Ticketing and Knowledge Base use the scanner; no extra Redis is
needed.

### 7. Frontend environment and image builds

`NEXT_PUBLIC_*` variables are public browser configuration. They must contain
URLs only, never database passwords, encryption keys or App private keys. Supply
them **before `next build`**; changing only the production container environment
does not change the compiled browser bundle.

| Variable                      | Application / local value                            | Production source                                                                        |
| ----------------------------- | ---------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `NEXT_PUBLIC_API_URL`         | Software Solutions and auth: `http://localhost:8000` | Public backend origin, e.g. `https://api.adbsoftwaresolutions.co.uk`; **without `/api`** |
| `NEXT_PUBLIC_AUTH_URL`        | Software Solutions and auth: `http://localhost:3004` | Public authentication origin                                                             |
| `NEXT_PUBLIC_SITE_URL`        | Software Solutions: `http://localhost:3000`          | Software Solutions canonical public origin                                               |
| `NEXT_PUBLIC_APP_URL`         | Auth default redirect: `http://localhost:3000`       | Combined Software Solutions public/admin origin                                          |
| `NEXT_PUBLIC_WEB_DESIGNS_URL` | Auth allowed redirect: `http://localhost:3002`       | Web Designs public origin                                                                |
| `NEXT_PUBLIC_TECHNOLOGY_URL`  | Auth allowed redirect: `http://localhost:3003`       | Technology public origin                                                                 |

Authentication uses `NEXT_PUBLIC_APP_URL` for the combined Software Solutions
origin, including `/admin` return targets; there is no separate admin origin.

For development outside Compose, create untracked `.env.local` files in the
relevant `sites/<app>/` directory with that app's values. The auth app has its own
[public-variable template](sites/auth-adb-software-solutions/.env.example).
The Web Designs and Technology applications currently do not read application
`NEXT_PUBLIC_*` settings; do not assume they require secrets from the backend.

The existing Docker build path copies `sites/<app>/.ci.env` to `.env.production`
before building. Supply **only that frontend's public variables** in `.ci.env`.
The Software Solutions and auth build workflows request these public values from
the application's Infisical project through the reusable image-build workflow.
Verify the generated file has the correct production origins before publishing
an image. Local `.env` / `.env.local` files are excluded from Docker contexts.

The three public websites share identical dependency/version declarations.
`tools/check-public-site-dependencies`, included in repository lint, rejects
missing packages or version differences in runtime, development, peer and optional
dependencies. Update all three manifests together and regenerate the pnpm lockfile.

Frontend Docker installs use a package-name selector with the dependency suffix,
for example `pnpm install --frozen-lockfile --filter "@adb/web-designs-site..."`.
This includes the shared UI/API packages and their own dependency links. A bare
`./sites/<app>...` directory selector does not expand dependencies in the pinned
pnpm version; a full-workspace install can hide that mistake. Validate container
changes with a fresh filtered install rather than existing local `node_modules`.
Keep content/navigation tests in their owning site; importing a sibling app
can make the production type check depend on that app’s uninstalled dependencies.

### 8. Production deployment

Production needs the existing deployable components, provisioned separately from
the development Compose stack:

| Component          | Requirement                                                                                                                                                          |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PostgreSQL         | Private access, provider-required TLS, backups and restore testing                                                                                                   |
| Cache Redis        | Shared by API/worker replicas for cache, distributed locks and SSE Pub/Sub                                                                                           |
| Session Redis      | Shared session store; avoid eviction/flushes that unexpectedly sign users out                                                                                        |
| Celery Redis       | Broker/results isolated from cache and sessions; appropriate persistence and `noeviction` policy for queued work                                                     |
| Backend image      | Existing `Dockerfile.backend` starts Gunicorn with an ASGI Uvicorn worker on 8000                                                                                    |
| Worker image       | Existing `Dockerfile.celery-worker`; `CELERY_QUEUE=general`; include encryption/integration variables                                                                |
| Beat image         | Existing `Dockerfile.celery-beat`; run exactly one scheduler; its schedule state is `/tmp/celerybeat-schedule` and does not need persisting                          |
| Frontend images    | Software Solutions (3000), auth (3004), Web Designs (3002), Technology (3003); build with production public URLs                                                     |
| Runtime users      | Backend, worker and Beat run as `www-data` (uid/gid 33); frontends as `nextjs` (uid 1001). Media and static mounts must belong to uid 33                             |
| Attachment storage | Persist `backend/media` (container path `/opt/adb-software-solutions/media`), shared between API/attachment workers; keep protected attachments behind governed APIs |
| Static assets      | Backend entrypoint runs `collectstatic`; arrange serving of its `staticfiles` output                                                                                 |
| Optional scanner   | Private ClamAV                                                                                                                                                       |

Obtain database/Redis URLs from the provisioned services and inject backend
secrets through the existing Infisical-backed deployment. Do not build runtime
secrets into images. Use stable key rings and back them up outside the database.
One Redis instance can technically host separate logical databases, but they
share persistence, memory policy and failure/flush boundaries; separate services
match the development topology. SSE adds no separate store or worker.

For the current settings, deploy the API at `api.<SITE_DOMAIN>` and auth at
`auth.<SITE_DOMAIN>`; serve Software Solutions and its `/admin` routes together
at `https://<SITE_DOMAIN>`. Production allowed API hosts and cookie domains derive
from `SITE_DOMAIN`. HTTPS, credentialed CORS and CSRF trust are required. The
current production CORS list includes the Software Solutions/auth origins and
`adbwebdesigns.co.uk` / `adbtechnology.co.uk` (including `www`); arbitrary alternate
brand domains need a reviewed backend configuration change. Frontend URL variables
alone do not alter that allow-list.

Before directing traffic to a new release:

```bash
# Run as a single deployment job with the backend runtime configuration.
python manage.py migrate --noinput
python manage.py check --deploy
```

Review every deployment-check finding against the trusted TLS proxy and current
security settings. Point DNS to the deployed services, terminate TLS and forward
`X-Forwarded-Proto: https` only from your trusted proxy. API access must retain
session cookies and the CSRF token header. Keep database, Redis and ClamAV private.
Allow outbound access needed by Microsoft Graph, GitHub, DNS/RDAP and the
configured monitoring checks. ICMP checks require OS permission for datagram/raw
ICMP sockets (e.g. the appropriate ping group range or `NET_RAW` capability), even
though the check does not invoke an external `ping` command.

For `/api/admin/events`, turn off reverse-proxy buffering/caching, keep an idle
read timeout above the 15-second heartbeat, and prefer HTTP/2. Example nginx
settings for the events location, alongside your normal backend routing:

```nginx
location = /api/admin/events {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 60s;
}
```

Responses also set `X-Accel-Buffering: no`. Validate that a signed GitHub webhook
or completed monitoring check results in an event and a frontend API refresh
without a page reload. See the [live updates guide](docs/LIVE_UPDATES_ARCHITECTURE.md)
for scopes and reconnect/fallback behaviour.

CI builds/publishes application images on `main`; production deployment is the
existing `.github/workflows/deploy.yml` workflow (the `deploy` branch or manual
image-tag dispatch). Its reusable deployment workflow/infrastructure lives in
`adb-software-solutions/github-actions-workflows`; production manifests are not
maintained in this repository. Supply the variables/services above there using
the current Infisical projects. This guide documents prerequisites; it does not
provision accounts, DNS, databases or deployments automatically.

#### Health, metrics and logs

Every image is ready for Prometheus, Grafana and Loki. Docker's `HEALTHCHECK`
calls `/healthz` every 30 seconds, and adb-deploy waits for it on deploy. nginx
(adb-deploy) answers 404 for `/healthz` and `/metrics` on the public domains,
so both are only reachable on the host.

- **Backend** (8000): `/healthz` answers **200** `ok`, or **200** `degraded` when PostgreSQL or the cache or session Redis does not answer (restarting the API would not fix them, and a deploy should not wait on them), with one entry per check: `database`, `cache:default`, `cache:session`. `/metrics` is django-prometheus: requests, responses and latency by view, method and status, summed over all Gunicorn workers (Prometheus multiprocess mode, set up by `entrypoint.sh` and `backend/gunicorn.conf.py`). Both are answered by `adbsoftwaresolutions.health`, first in `MIDDLEWARE`, so the host check, HTTPS redirect and login do not apply and neither is counted in the request metrics.
- **Frontends** (Software Solutions, Web Designs and Technology on 3000 in their images; auth on 3004): `/healthz` answers **200** `ok` whenever the server answers (it does not check the API). `/metrics` has `http_request_duration_seconds{method, status_code}` and the Node.js process metrics. Both come from `packages/observability`.
- **Celery worker and Beat**: JSON logs only; no HTTP endpoint.

A process that cannot answer at all fails the check, so none reports
`unhealthy` itself. Logs are one JSON object per line on stdout in every image
(`LOG_FORMAT=json`): `time`, `level`, `logger`, `message`, `service`, and
`exception` when there is one, from Django, Gunicorn, Uvicorn, Celery, pnpm and
Next.js alike. Celery runs with `--quiet` so it prints no banner.

### Verification and maintenance

```bash
tools/lint
tools/test-all
```

Check account email delivery, sign-in/CSRF, the credential Vault, background
monitoring, Graph inbound/outbound mail, GitHub webhook processing and SSE before
calling a production deployment ready. Leave optional integrations disabled until
their credentials/services exist.

Python requirement lock files are generated: change `backend/requirements/*.in`
and run `tools/update-locked-requirements`. Regenerate pnpm lock files using pnpm.
Read `AGENTS.md` and `CONTRIBUTING.md` before making changes.

## Monorepo approach

The repository intentionally does not use Turborepo or another monorepo orchestration framework. pnpm workspaces provide shared-package resolution while CI/CD and container images remain application-focused.

Each deployable application has its own Docker image. Published images in the shared DigitalOcean Container Registry are prefixed with `adb-web-platform-` so they cannot collide with unrelated ADB projects.

## Finding code and tests

Start with the [backend navigation guide](backend/README.md) and
[business-domain index](backend/apps/README.md). Every Django business app has a
README linking its models, services, API modules and tests. Backend tests live
in local `tests/` packages; authentication frontend tests live in
`sites/auth-adb-software-solutions/tests/`. See
[CONTRIBUTING.md](./CONTRIBUTING.md) for verification and repository conventions.

The internal GitHub dashboard lives at `/admin/github`. See
[GitHub App setup](docs/GITHUB_APP_SETUP.md) for multi-account installations,
Vault signing-key configuration, webhook subscriptions and workflow permissions.

Operational screens use shared server-sent events for live updates. See
[the live updates guide](docs/LIVE_UPDATES_ARCHITECTURE.md) for ASGI, Redis and proxy
requirements.

## Public websites: run, edit and publish

The three public websites are implemented as multi-page Next.js applications.
Their approved compositions are separate; common navigation, forms, editorial
rendering and SEO helpers live in `packages/ui/src/public/`. Marketing copy is
owned locally, while published editorial content comes from Django.

Run the shared backend and start any site from the repository root:

```bash
pnpm --dir sites/adb-software-solutions dev  # http://localhost:3000
pnpm --dir sites/adb-web-designs dev        # http://localhost:3002
pnpm --dir sites/adb-technology dev         # http://localhost:3003
```

Each site's `src/content/site.ts` contains its services, individual area pages,
About, working arrangements, policies and contact introduction.
`src/content/home.ts` contains homepage copy. Its `HomePage.tsx` owns the brand's
composition and artwork; `src/styles/public.css` owns brand-specific styling.
The shared public stylesheet is scoped under `.marketing` and does not change
admin styling. All sites default to dark; the visitor's theme choice is stored
locally, without a tracking cookie. The authentication app and `/admin` retain
Django-backed sessions and permissions.

Use `/admin/content` to create blog posts, public portfolio/case studies,
testimonials and FAQs. Select the correct Brand, save a draft, upload images from
its edit form, add descriptive alternative text and explicitly publish it.
Article and case-study bodies support Markdown; raw HTML and embedded scripts
are not rendered. Portfolio and FAQ service slugs connect editorial content to
matching service pages. Copy the slug from that site's service URL. FAQs also
need a category assigned to the same Brand. A future blog publication date keeps
an otherwise published post hidden until the date arrives. Empty editorial
collections are excluded from navigation and sitemaps and marked `noindex`.

For a populated Web Designs local preview, use the removable demo dataset below
with the backend Python environment active. It creates 12 projects, 12 articles,
3 testimonials and 10 FAQs with sample images, all explicitly labelled fictional
and published only to the Web Designs Brand. It requires debug mode and a local
DB host. Repeat runs skip existing entries; cleanup preserves real CMS content.

```bash
DEBUG=1 python backend/manage.py seed_web_designs_demo
# Remove the reserved demo entries and their media when finished:
DEBUG=1 python backend/manage.py seed_web_designs_demo --clear
```

Do not carry this published demo dataset into a production database. Web Designs
inner-page layouts live in `src/components/public/WebPages.tsx`, with editable
layout labels in `src/content/page-design.ts` alongside the main service copy.

Public SSR and the same-origin contact proxy read `API_INTERNAL_URL` at runtime;
if absent, they use `NEXT_PUBLIC_API_URL`, then the normal development/production
backend origin. In production, set `API_INTERNAL_URL` to an origin reachable
from each Next.js container, such as your private backend service URL. If using
a private hostname, add that exact name to the backend runtime `INTERNAL_API_HOSTS`
(comma separated, no scheme, port or wildcard). Set backend `PUBLIC_MEDIA_URL`
to a publicly reachable absolute media base such as
`https://api.adbsoftwaresolutions.co.uk/media/`, with its trailing slash, so CMS
images do not point browsers at the private service. The default `/media/` is
suitable for ordinary local/public-origin requests. `API_INTERNAL_URL` must
not include `/api`. It is not a browser variable. Continue setting the existing
`NEXT_PUBLIC_API_URL` at build time for the Software operations frontend. Brand
identity and canonical public URLs belong to the individual content files,
independently of the localhost preview URLs. Do not expose Graph, GitHub or
credential encryption secrets to frontend builds.

Contact forms submit through `/api/contact` to the shared Lead/Ticket ingestion
endpoint, with Brand fixed by the serving site. Ensure each Brand has an enabled
Ticket Queue (preferably Sales), and configure its sales Shared Mailbox if replies
should use Graph email. The existing ingestion preserves a Lead if ticket routing
is unavailable, so queue setup is a launch check. Forms validate email and length,
reject the honeypot, and limit submissions to five per IP per ten minutes using
existing cache Redis. Production ingress must overwrite `X-Forwarded-For` rather
than trusting a visitor-supplied value, as required by existing authentication
throttling. Backend failure shows a retry message; no successful submission is
claimed unless the backend acknowledges it. No new Redis service is needed.

Before production rollout, apply Django migrations, keep the shared packages in
the frontend builds, serve backend `/media/` publicly with persistent storage,
and verify HTTPS ingress routing for `/social`, `/api/contact`, icons, robots and
sitemaps. Social cards are rendered at 1200×630 using the supplied logo and brand
artwork, with a page-specific title; no third-party image service is required.
Set `NODE_ENV=production` for production builds/runs and `development` for dev;
arbitrary environment names are not valid Node modes.

For the full crawl, file decisions and production cutover, follow the
[Web Designs migration runbook](docs/WEB_DESIGNS_MIGRATION_RUNBOOK.md).

The old Web Designs URL decisions are recorded in
[the migration ledger](docs/WEB_DESIGNS_URL_MIGRATION.json). Static redirects live
in `sites/adb-web-designs/redirects.json`; all exported editorial aliases activate
only after the matching Web Designs CMS draft is published. Unpublished/retired
entries return a real 404.

Before switching off WordPress, create the version-controlled, self-contained
JSON export with original image bytes, then use the offline draft importer:

```bash
python backend/manage.py export_wordpress_content \
  --output backend/apps/website/fixtures/wordpress/adb-web-designs.json \
  --routes-directory sites/adb-web-designs/src/content
python backend/manage.py import_wordpress_content \
  --source backend/apps/website/fixtures/wordpress/adb-web-designs.json --dry-run
# Remove --dry-run and pass --media-base-url http://localhost:8000 locally,
# or the public production backend/media origin when importing production data.
```

Commit the archive and generated routing JSON files before deployment. The
importer creates all blog/project drafts, restores images without contacting
WordPress and preserves existing records. Review/publish individually in
`/admin/content`. Full instructions and limits are in
[the migration archive guide](docs/migrations/README.md).

The raw asset library and temporary mockup stay ignored. Only selected original
logos, the portrait and local font are shipped in the sites. No fabricated CMS
projects, ratings or testimonials are published. Review
[the morning notes](docs/PUBLIC_WEBSITES_MORNING_REVIEW.md) before launch,
especially policy/trading details, old article accuracy and case-study approval.

## Public website Google Analytics and privacy

Configure each public brand independently in its runtime environment (Infisical
in production), then redeploy:

| Site               | Runtime measurement ID                  |
| ------------------ | --------------------------------------- |
| Web Designs        | `GA4_WEB_DESIGNS_MEASUREMENT_ID`        |
| Software Solutions | `GA4_SOFTWARE_SOLUTIONS_MEASUREMENT_ID` |
| Technology         | `GA4_TECHNOLOGY_MEASUREMENT_ID`         |

These are public identifiers of the form `G-XXXXXXXXXX`. A blank or invalid ID
loads no Google script. In [Google Analytics](https://analytics.google.com/),
create a property and Web stream for each brand domain; copy its **Measurement
ID** from Admin → Data streams → the Web stream. Separate properties keep brand
reports independent. Apply the settings below to each property.

The public layouts read these values after Next.js's request boundary, so runtime
Infisical values do not have to be present when images are built. Analytics lives
inside the public route group; Software `/admin` and account/security routes do
not load it. No frontend build arguments or additional Redis services are needed.

Each public website loads normal GA4 analytics by default and offers an immediate opt-out
on `/privacy-policy/` and `/cookie-policy/`. Opt-out disables collection and clears
GA cookies; its choice cookie lasts 12 months. Theme persistence can also be
disabled. Code disables advertising consent, Google signals and advertising
personalisation, caps analytics cookies at 12 months and sends pathname-only page
locations and origin-only referrers. Do not put personal data in URL paths.

Before launch, configure the account/property for aggregate website statistics:

- Admin → Account settings → Data sharing settings: disable optional sharing,
  including Google products/services, benchmarking and support/specialist access.
- Admin → Data collection: keep Google signals and advertising features off.
  Do not link Google Ads, enable remarketing/User-ID, or use individual visitor
  profiling. Use aggregate site reports to improve these websites.
- Web stream → Enhanced measurement: disable automatic additional events,
  including form interactions, site search, outbound clicks and automatic page
  views; the application sends its own page views without query strings.
- Admin → Data retention: select 2 months for event/user data and disable resetting
  retention on new activity. Aggregate standard reports have separate retention.
- Review Google's processing terms and UK international-transfer arrangements.
  Verify page views in Realtime and verify opting out stops subsequent collection.

The [ICO statistical-purpose exception](https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guidance-on-the-use-of-storage-and-access-technologies/what-are-the-exceptions/)
requires aggregate service-improvement use, clear information and a simple free
objection mechanism. The account settings and actual use must meet these
conditions alongside the code; enabling unrelated tracking changes that assessment.
See [Google data-sharing settings](https://support.google.com/analytics/answer/1011397?hl=en)
and [data retention](https://support.google.com/analytics/answer/7667196?hl=en).

## Enquiry retention operations

Open `/admin/retention` in Software Solutions to review inactive Lost Leads after
36 months. Scans only queue records. Approve deletion explicitly, or keep with a
reason and a 3/6/12-month review date. The server rechecks recent contact and
protected relationships before approval. Apply CRM migration 0006 and grant the
review capabilities through Users & Access. Existing Celery workers/Beat run the
daily scan; no extra environment variables or Redis are needed. See
[Lead retention](docs/LEAD_RETENTION.md) for scope, permissions and mailbox/backups.

## Public brand design and editing

All three brands use the approved Web Designs visual language: dark by default,
a light/dark switch, large logos and typography, cyan sections and numbered inner
pages. Software introduces applications/integrations/automation; Technology uses
a source-to-server sequence. Their services, About and area copy remain separate.
Published projects, articles, testimonials and FAQs remain Brand-scoped CMS data.

Edit each site's `src/content/home.ts`, `site.ts`, `page-design.ts` and
`policies.ts`. Shared presentation styles are in
`packages/ui/src/public/family.css`; shared policy text is parameterised in
`packages/ui/src/public/policies.ts`. Brand facts and service terms are passed
from local content files. Do not put marketing styles or analytics in Software's
root or admin layout. Software's policies additionally describe signed-in
operations and necessary authentication storage. No contracting, core-hours
helpdesk or unconfirmed consultancy offer has been added.

### ADB Analytics

`sites/analytics-adb-software-solutions/` is the independent analytics product on
port 3005 (`analytics.adbsoftwaresolutions.co.uk`). It uses the shared Django
`/api/analytics` APIs, ADB sessions, encrypted credential Vault and existing Celery
workers. Run `pnpm --dir sites/analytics-adb-software-solutions dev` locally.
See [Analytics setup and architecture](docs/ANALYTICS_PLATFORM.md) for Google OAuth,
required runtime/build configuration, reporting semantics and live verification.

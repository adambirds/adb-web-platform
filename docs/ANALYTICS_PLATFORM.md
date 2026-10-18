# Analytics Platform

## Purpose

Provide an independent, authenticated analytics application at `analytics.adbsoftwaresolutions.co.uk`, using the existing Django identity, session, permissions, credential vault, and Celery infrastructure. GA4 reporting, GA4 administration and Google Search Console reporting are first-class MVP capabilities.

## Boundaries

- Next.js frontend: `sites/analytics-adb-software-solutions/`.
- Django Ninja API and domain services: `backend/apps/analytics/`.
- No second identity system, independent staff database, browser-held Google refresh tokens, or direct Google API calls from the browser.
- `Business` is an analytics workspace, distinct from `Brand` and operational `Client`. Optional Client linkage does not grant access.
- `BusinessMembership` connects existing users to businesses; `Website` belongs to exactly one business.
- Django capability checks and business membership scope must be enforced before accessing any website, provider connection, report, export or background job.
- Analytics users need not be staff users; membership is not access to ADB's operations console.

## Provider integration

A Google OAuth connection may authorize GA4 read, GA4 edit, and Search Console read separately. Tokens must be encrypted using the existing credential service and never exposed to frontend code or logs. State, PKCE, least-privilege scopes, token rotation and revocation are required.

Each Website may associate one GA4 property and one Search Console site property. Store external identifiers, provider permissions, sync cursors, quota/error state and freshness timestamps separately. Validate access to selected properties before saving.

GA4 Data API supplies aggregate and realtime reporting. GA4 Admin API supplies custom dimensions, metrics and key event management. Only registered, reportable custom dimensions are available for custom parameter breakdowns; registration is not retroactive. Search Console Search Analytics API supplies clicks, impressions, CTR, position and query/page/device/country dimensions, subject to privacy filtering and API row limits.

Search Console clicks and GA4 sessions must remain distinct metrics. Page-level comparisons may join normalized URLs and dates but must not imply person-level attribution.

## Reporting and operations

- Celery syncs aggregate historical data incrementally with bounded backfill and retries.
- Cache dashboards with freshness and last-sync indicators.
- Reserve a separate analytics worker queue when workload warrants it.
- Never place provider API calls on every page load.
- Provider quota exhaustion, missing dimensions, delayed Search Console data, incomplete days and disconnected integrations must be surfaced clearly.
- Google Admin API writes require an explicit confirmation, matching platform permission, Google edit scope and append-only audit event.
- Do not assume that the reporting APIs expose arbitrary raw events or unregistered event parameters.

## Initial implementation milestones

1. Django models, migrations and tenant-scoped tests for Business, BusinessMembership, Website and provider connections.
2. Shared-auth Next.js frontend with business/website selection and guarded dashboard routes.
3. Google OAuth connection lifecycle and property discovery.
4. GA4 historical/realtime reporting, scheduled sync and cached overview/pages/events.
5. Search Console sync, query/page performance and combined page reporting.
6. GA4 Admin API custom definition/key event management, write confirmation and audit coverage.
7. End-to-end tests, deployment wiring, operational runbook and user-facing onboarding.

## Cost policy

Use quota-limited Google APIs, existing hosting and local caching. No paid BigQuery export, paid AI API or metered third-party analytics service is required for the MVP.

## Implemented application contract

The analytics application is a separate Next.js deployment on port **3005**.
Django registers `/api/analytics` separately from `/api/admin`; analytics membership
does not set `is_staff`, add operational Groups, or grant access to Client records.
`business_has_perm` through the existing EmailBackend implements Django's object-permission interface for
Business objects. Owner, Admin and Viewer use the `Analytics / Owner`, `Analytics / Admin` and
`Analytics / Viewer` Django Group capability bundles without assigning global user
Group membership. Every resource lookup first requires business membership. Explicit Django capability grants
can extend a member's capabilities, but never bypass membership filtering.
BusinessMembership user deletion uses PROTECT; owner removal/demotion goes through
a serialized Business lock and retains an owner. Do not bypass the service with
bulk membership updates.

GoogleConnection references a shared StoredCredential. Token payloads use the
Vault service and `CREDENTIAL_ENCRYPTION_KEYS`; no alternate encryption key or
plaintext token field exists. OAuth states are session/actor/business bound,
expire after ten minutes, use PKCE S256 and are consumed before exchange. Callbacks
return only to the configured analytics origin. Each connection is business-owned,
so sharing a Google account across businesses requires separate consent connections.
An administrator can reconnect by authorizing again and relinking properties.

Reporting uses exact provider date-window snapshots in PostgreSQL, cached for five
minutes in Redis. This avoids adding daily unique-user counts or averaging daily
ratios incorrectly. Reports for an unsynchronized window explicitly return
`range_not_synchronized`; an administrator can request any past window up to 366
days, including its equal-length previous period. There are no fabricated zeros.
Each report request is bounded to four pages of 25,000 rows and reports truncation.
Successful empty responses are stored distinctly from missing responses.

Celery's `analytics.enqueue_syncs` refreshes the recent 28-day window every six
hours. Both providers end three days ago to align the initial reporting window; Search
Console requests final data. Both providers refresh their previous comparison window as well. This is a
bounded historical correction policy; arbitrary older ranges are fetched only on
explicit request. Initial property association queues this same initial window, followed by a
one-time 90-day historical window and its previous period. Existing historical
windows older than the 14-day correction horizon are reused on subsequent jobs.
Jobs have durable state, progress, bounded retry/backoff and a database unique
constraint preventing concurrent jobs for a property. Interrupted jobs expire
after two hours. Tasks run on the existing `general` queue, with a 30-minute hard
limit; no deployment or worker-queue infrastructure is changed.

URL joins preserve scheme, host, path slash and query distinctions and drop only
fragments. Canonical mismatches remain unmatched, rather than silently associating
unrelated content. GA4 property timezone must match the website timezone; unlink the GA4 property
before changing that timezone or replacing it with a property in another zone.
Unlinking removes only that website provider and its reports; Google account
revocation remains a separate action affecting all its associated websites. Search
Console remains Pacific Time. Combined views explicitly separate both systems.
The supported realtime view reports active users and event counts by event,
country and device; it does not invent realtime page paths.

GA4 configuration uses the Admin API with explicit `analytics.edit` consent,
business write permission, input validation, confirmation and audit intent plus
completion events. The wizard refreshes existing event dimensions, identifies
missing parameters and verifies created definitions. Property tier limits are
left to Google validation rather than guessed. Registration is non-retroactive;
allow 24–48 hours for new reportable data. The tracking example uses the existing
Google tag and requires the site's established consent configuration.

## Google Cloud setup

This connects Google data to an existing ADB account; it does not replace ADB
login. Configure the following in order. Select the same project in the console's
project selector for every link below; links are not pinned to a project ID.

### 1. Create the project and enable APIs

Use separate Google Cloud projects for development/testing and production, with
separate OAuth clients and secrets. Suggested names are `ADB Analytics Development`
and `ADB Analytics Production`; record each generated project ID in your deployment
configuration. Google's [OAuth policies](https://developers.google.com/identity/protocols/oauth2/policies)
explain environment separation.

1. [Create a project](https://console.cloud.google.com/projectcreate), or
   [select an existing project](https://console.cloud.google.com/cloud-resource-manager).
   Select the appropriate organization if your Google administrator provides one.
2. Open each API page and click **Enable**:
   [Google Analytics Data API](https://console.cloud.google.com/apis/library/analyticsdata.googleapis.com),
   [Google Analytics Admin API](https://console.cloud.google.com/apis/library/analyticsadmin.googleapis.com),
   and [Google Search Console API](https://console.cloud.google.com/apis/library/searchconsole.googleapis.com).
3. Confirm all three appear under
   [Enabled APIs & services](https://console.cloud.google.com/apis/dashboard).

This implementation uses user OAuth. You do not need a service-account JSON key,
an API key, BigQuery, or Google Cloud IAM access for each Analytics user.

### 2. Configure Branding

Open [Google Auth Platform → Branding](https://console.cloud.google.com/auth/branding).
If prompted, choose **Get started**. Enter these values for the production project;
use a clearly marked development name for the development project.

| Console field           | What to enter                                                                                                                                                 |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| App name                | `ADB Analytics`                                                                                                                                               |
| User support email      | A monitored address available in Google's selector; use a suitable Google-account address or eligible group you control.                                      |
| Audience                | **External** for the intended client-facing platform; see the decision below.                                                                                 |
| Developer/contact email | A monitored address for Google's verification and operational messages.                                                                                       |
| App home page           | `https://analytics.adbsoftwaresolutions.co.uk` once publicly accessible.                                                                                      |
| Privacy policy          | The actual public HTTPS URL of the policy covering this application's Google data use. Supply your published URL; this feature does not create a policy page. |
| Terms of service        | Your actual published terms URL, if provided.                                                                                                                 |
| Authorized domains      | `adbsoftwaresolutions.co.uk`, without a scheme, path or subdomain. Add another domain only if used by your app's URLs.                                        |
| Logo                    | Optional during initial setup; use an approved ADB asset if supplied.                                                                                         |

Save the configuration. Ensure verification reviewers can reach the home page and
policy links. Complete domain ownership verification through
[Google Search Console](https://search.google.com/search-console) when required;
use Google's [brand verification instructions](https://developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification)
for ownership and branding requirements. Do not enter placeholder policy URLs for
a production verification submission.

### 3. Choose Audience: External or Internal

Open [Google Auth Platform → Audience](https://console.cloud.google.com/auth/audience).

| Situation                                                                                                                                   | Choose                                                             |
| ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Clients connect their own Google accounts, including Gmail or another company's Workspace accounts.                                         | **External** — recommended for this platform.                      |
| ADB staff use personal Google accounts or Google accounts outside the project's owning organization.                                        | **External**, even if only ADB staff can log into the application. |
| Every Google account that will authorize connections belongs to the same Google Workspace/Cloud Identity organization as the Cloud project. | **Internal** may be appropriate for a staff-only deployment.       |
| Internal is unavailable in the console, or the project has no qualifying Google organization.                                               | **External**.                                                      |

An ADB email address or Microsoft 365 tenant alone does not establish membership
of a Google organization. Internal describes the **Google accounts authorizing
access**, not whether the ADB application is private. External does not bypass
ADB login, Business membership or website permissions, and Internal does not
prevent an eligible staff Google account from accessing client-owned properties
that have been shared with that account.

For initial External setup, keep **Publishing status: Testing**. Under **Test
users → Add users**, add the exact Google account addresses that will click
**Connect Google**, then save. Add the authorizing account, not just the ADB login
address. Testing supports up to 100 listed test users. Internal access is instead
restricted by the owning Google organization; its administrator may also need to
approve the app. See [Google's audience rules](https://support.google.com/cloud/answer/15549945?hl=en).

### 4. Register the requested scopes

Open [Google Auth Platform → Data Access](https://console.cloud.google.com/auth/scopes),
choose **Add or remove scopes**, and select or manually enter the following.
Save/update the scope selection.

| Scope                                                 | Why this application requests it                                                  |
| ----------------------------------------------------- | --------------------------------------------------------------------------------- |
| `openid`                                              | Identify the connected Google account.                                            |
| `https://www.googleapis.com/auth/userinfo.email`      | Email identity; the backend requests the equivalent OpenID Connect `email` scope. |
| `https://www.googleapis.com/auth/analytics.readonly`  | Discover GA4 properties and read reports.                                         |
| `https://www.googleapis.com/auth/webmasters.readonly` | Discover Search Console properties and read search performance.                   |
| `https://www.googleapis.com/auth/analytics.edit`      | Optional administration consent for custom dimensions, metrics and key events.    |

Register the edit scope if offering configuration management. Adding it to the
console does not grant it automatically: the backend requests it only when the
user chooses administration consent. Reporting consent requests only identity
and read scopes. No Gmail, Drive or Search Console write scope is needed.
For the console workflow, see Google's
[consent and scope guide](https://developers.google.com/workspace/guides/configure-oauth-consent).

### 5. Create the Web application OAuth client

Open [Google Auth Platform → Clients](https://console.cloud.google.com/auth/clients),
choose **Create client**, and use the following settings in each project's client.

| Field                         | Production project                                                                        | Development project                                  |
| ----------------------------- | ----------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| Application type              | **Web application**                                                                       | **Web application**                                  |
| Name                          | `ADB Analytics Production Web`                                                            | `ADB Analytics Local Web`                            |
| Authorized JavaScript origins | Leave empty: this integration redirects through Django and exchanges codes on the server. | Leave empty for the same reason.                     |
| Authorized redirect URIs      | `https://api.adbsoftwaresolutions.co.uk/api/analytics/oauth/callback`                     | `http://localhost:8000/api/analytics/oauth/callback` |

Click **Create** and securely capture the **Client ID** and **Client secret**.
The secret belongs in the backend runtime secret store, never in `NEXT_PUBLIC_*`,
Git or a frontend build. These credentials identify the app; user refresh tokens
are obtained later by connecting Google and encrypted by the existing Vault.

The callback belongs to the API, not port 3005 or the account application's login
page. Match scheme, hostname, port, path and trailing slash exactly between the
console and `ANALYTICS_GOOGLE_REDIRECT_URI`. Use `localhost` consistently for the
local app, API and account frontend. For another staging host, register its exact
callback in the corresponding nonproduction client. See Google's
[web-server OAuth instructions](https://developers.google.com/identity/protocols/oauth2/web-server).

### 6. Set application configuration and start services

Use the [environment variable table](#environment-variables) below. For local
work, add these values to `.devcontainer/.env` without overwriting existing secrets:

```dotenv
ANALYTICS_GOOGLE_CLIENT_ID=<development-client-id>
ANALYTICS_GOOGLE_CLIENT_SECRET=<development-client-secret>
ANALYTICS_GOOGLE_REDIRECT_URI=http://localhost:8000/api/analytics/oauth/callback
ANALYTICS_FRONTEND_URL=http://localhost:3005
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_AUTH_URL=http://localhost:3004
NEXT_PUBLIC_ANALYTICS_URL=http://localhost:3005
```

Keep the existing valid `CREDENTIAL_ENCRYPTION_KEYS` key ring; replacing it can
make stored secrets unreadable. Rebuild the devcontainer after environment changes
so Compose reloads the variables. Apply migrations, then use **Start Analytics
Stack**; see [development tasks](../.devcontainer/README.md). Django, the general
Celery worker and Beat must all be running for synchronization and refreshes.

Production uses the production client's values, the HTTPS callback above,
`ANALYTICS_FRONTEND_URL=https://analytics.adbsoftwaresolutions.co.uk`, and the
production API/auth/Analytics frontend origins. Inject secrets through the existing
runtime process, apply migrations, restart API/workers/Beat and rebuild the auth
frontend with its Analytics return origin. Deploy through the existing automation;
this feature does not provision infrastructure or DNS.

### 7. Grant Google property access and connect

The Cloud project and OAuth scopes do not grant access to GA4 or Search Console
properties. Use a Google account that already has the appropriate property access.

1. In [Google Analytics](https://analytics.google.com/), select the correct property
   and inspect **Admin → Property access management**. Reporting needs a role that
   can read its data; configuration writes require an appropriate role such as
   Editor or Administrator. Ask the property's administrator to grant access.
2. In [Search Console](https://search.google.com/search-console), select the property
   and inspect **Settings → Users and permissions**. Have its owner grant the
   connecting account suitable access. Domain (`sc-domain:`) and URL-prefix
   properties are supported; select the one covering the website being tracked.
3. Log into ADB Analytics with the existing ADB account. Create/select a Business
   and Website, then choose **Connect Google**. Select the Google account added
   as a test user and grant the requested reporting permissions.
4. Discover and link the GA4/Search Console properties. Match the Website timezone
   to GA4, start synchronization and follow job progress. Test administration
   consent separately on a test property before making configuration changes.

### 8. Move External production access out of Testing

External Testing refresh tokens expire after **seven days** for the scopes this
app uses. This can stop unattended synchronization; reconnecting is a temporary
testing measure. The identity-only exception does not apply to Analytics/Search
Console scopes. See Google's [refresh-token expiration rules](https://developers.google.com/identity/protocols/oauth2/#expiration).

For launch, finish the production project's branding, real public policy URLs,
domain ownership and scope configuration. In
[Audience](https://console.cloud.google.com/auth/audience), use **Publish app**
when ready, and follow
[Verification Center](https://console.cloud.google.com/auth/verification) for any
required brand/sensitive-scope verification. Prepare a description of each scope's
use and a demonstration of the consent and reporting/configuration flows. Use
Google's displayed requirements to determine the required submission material.
Publishing and verification are separate; publishing alone does not mean approved.
After changing status, reconnect accounts previously authorized in Testing and
verify background refresh. Production tokens can still be revoked or expire.

### Troubleshooting Google setup

| Symptom                                               | Check                                                                                                                                                    |
| ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `org_internal` or account rejected by an Internal app | The authorizing Google account must belong to the project's Google organization; use External for accounts outside it.                                   |
| External Testing access blocked                       | Add the exact Google account under Audience → Test users, save, then select that account during consent.                                                 |
| `redirect_uri_mismatch`                               | Compare the exact callback with the selected client's registered redirect URI and backend environment; check the project/client pair.                    |
| Property missing from discovery                       | Confirm the selected Google account has property access, all three APIs are enabled in the client's project, and the granted scopes match the operation. |
| Read reports work but configuration fails             | Reconnect with administration consent and confirm the account's GA4 property role allows writes.                                                         |
| Sync stops about a week after connection              | Check External Testing token expiry; complete production setup and reconnect. Revocation or organization policy can also require reconnection.           |
| Unverified-app warning or administrator block         | Check Verification Center and Google Workspace administrator policy; adding a test user does not override an organization block.                         |

### Environment variables

| Process         | Variable                         | Purpose                                                              |
| --------------- | -------------------------------- | -------------------------------------------------------------------- |
| API/worker      | `ANALYTICS_GOOGLE_CLIENT_ID`     | Google Web OAuth client identifier                                   |
| API/worker      | `ANALYTICS_GOOGLE_CLIENT_SECRET` | Runtime-only OAuth client secret                                     |
| API             | `ANALYTICS_GOOGLE_REDIRECT_URI`  | Exact registered callback; production default above                  |
| API             | `ANALYTICS_FRONTEND_URL`         | Fixed post-OAuth return origin; defaults to analytics subdomain      |
| API/worker      | `CREDENTIAL_ENCRYPTION_KEYS`     | Existing shared Vault key ring                                       |
| Analytics build | `NEXT_PUBLIC_API_URL`            | Shared API origin; local default `http://localhost:8000`             |
| Analytics build | `NEXT_PUBLIC_AUTH_URL`           | Existing auth origin; local default `http://localhost:3004`          |
| Auth build      | `NEXT_PUBLIC_ANALYTICS_URL`      | Exact analytics return origin; local default `http://localhost:3005` |

Existing SQL, cache, session and Celery variables remain required. Production
session/CSRF cookies remain secure and shared across the established parent domain.
CORS and CSRF origin allowlists add only the exact analytics origin and local port.
Rebuild the auth frontend with the analytics return URL configured before launch.
The new Dockerfile/workflow follow existing non-root, healthcheck, registry and
main-branch publishing conventions. The pnpm workspace already includes `sites/*`.

### Live verification checklist

Automated tests mock all Google responses. Before production use, verify consent
and any Google verification requirements; offline refresh; revocation; real GA4
and GSC property discovery; timezone selection; initial and custom-range sync;
provider quota/permission error displays; definition creation and key-event deletion
on a test property; account login/MFA return across the real subdomains; and the
image build/publish in the existing CI environment. Provider reports may exclude
privacy-filtered queries, have processing delays or expose only top rows; missing
or truncated data is not equivalent to zero.

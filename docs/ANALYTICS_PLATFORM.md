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
unrelated content. GA4 association reads and applies the provider timezone automatically. It rejects
a timezone change while a website synchronization is active.
Unlinking removes only that website provider and its reports; Google account
revocation remains a separate action affecting all its associated websites. Search
Console remains Pacific Time. Combined views explicitly separate both systems.
The realtime view shows overall active users and event counts, with event-count
breakdowns by event, country and device. Google's realtime API rejects
`activeUsers` combined with `eventName`, so active-user totals are queried
separately and never derived by summing event rows. It does not invent realtime
page paths. See the [Google realtime schema](https://developers.google.com/analytics/devguides/reporting/data/v1/realtime-api-schema).

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

| Console field           | What to enter                                                                                                            |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| App name                | `ADB Analytics`                                                                                                          |
| User support email      | A monitored address available in Google's selector; use a suitable Google-account address or eligible group you control. |
| Audience                | Choose for the connecting Google account, not ADB user count; see below.                                                 |
| Developer/contact email | A monitored address for Google's verification and operational messages.                                                  |
| App home page           | `https://analytics.adbsoftwaresolutions.co.uk` once publicly accessible.                                                 |
| Privacy policy          | `https://analytics.adbsoftwaresolutions.co.uk/privacy` after this version is deployed.                                   |
| Terms of service        | `https://analytics.adbsoftwaresolutions.co.uk/terms` after this version is deployed.                                     |
| Authorized domains      | `adbsoftwaresolutions.co.uk`, without a scheme, path or subdomain. Add another domain only if used by your app's URLs.   |
| Logo                    | Optional during initial setup; use an approved ADB asset if supplied.                                                    |

Save the configuration. Ensure verification reviewers can reach the home page and
policy links. Complete domain ownership verification through
[Google Search Console](https://search.google.com/search-console) when required;
use Google's [brand verification instructions](https://developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification)
for ownership and branding requirements. Do not enter placeholder policy URLs for
a production verification submission.

### 3. Choose Audience: External or Internal

The application is currently used only by its operator. Keep External in
**Testing** with only that operator's Google account listed while testing. One
user does not itself qualify for Internal: choose Internal only if that Google
account belongs to the Google organization owning the project. Public privacy and
terms pages do not open registration or change application permissions. Review
the policies and operating arrangements before inviting others.

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
| `https://www.googleapis.com/auth/analytics.edit`      | Supported, explicitly confirmed custom dimensions, metrics and key-event changes. |

Register all three API scopes. Initial connection and reauthorisation request
Analytics read, Analytics edit and Search Console read together, plus OpenID/email
identity, offline access and explicit consent. Adding scopes in the Console alone
does not grant them to an existing connection: use **Reauthorise account** in
Settings → Google accounts. No Gmail, Drive, Analytics user-management or Search
Console write scope is requested. Consent is separate from the Google property
role: supported GA4 configuration writes require Editor or Administrator access.
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

#### Infisical: production entries to create or confirm

Open [ADB Infisical](https://secrets.adbsoftwaresolutions.co.uk) and select the
existing **ADB Web Platform application project**, identified in the workflows by
project ID `51df9308-efb3-45b0-94ed-bf641f076acf`. Choose environment **prod**
and the root folder **/**. Both production frontend builds and the deployment
workflow read application values from this location. Use the exact uppercase
names below, without adding an application prefix or creating an `/analytics`
subfolder. The registry and deployment-bootstrap projects are separate; these
Google settings belong in the application project.

Create the following four Analytics backend entries if missing. Update an
existing entry rather than creating a duplicate:

| Infisical key                    | Production value                                                                                                             | Used by                                                   |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| `ANALYTICS_GOOGLE_CLIENT_ID`     | The **Client ID** from the production Google Web application OAuth client, normally ending in `.apps.googleusercontent.com`. | Django API and workers.                                   |
| `ANALYTICS_GOOGLE_CLIENT_SECRET` | The **Client secret** issued for that same production OAuth client. This is the confidential value.                          | Django API and workers; runtime only.                     |
| `ANALYTICS_GOOGLE_REDIRECT_URI`  | `https://api.adbsoftwaresolutions.co.uk/api/analytics/oauth/callback`                                                        | Django OAuth callback; must exactly match Google Clients. |
| `ANALYTICS_FRONTEND_URL`         | `https://analytics.adbsoftwaresolutions.co.uk`                                                                               | Django's fixed return destination after Google consent.   |

Create or confirm these public build settings in the same project/environment/root
folder. They are stored in Infisical for configuration management but their values
are public and will be included in the browser application:

| Infisical key               | Production value                               | Build that needs it                                                                 |
| --------------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------- |
| `NEXT_PUBLIC_API_URL`       | `https://api.adbsoftwaresolutions.co.uk`       | Analytics and shared authentication frontend.                                       |
| `NEXT_PUBLIC_AUTH_URL`      | `https://auth.adbsoftwaresolutions.co.uk`      | Analytics and shared authentication frontend.                                       |
| `NEXT_PUBLIC_ANALYTICS_URL` | `https://analytics.adbsoftwaresolutions.co.uk` | Analytics root login return target and shared authentication allowed return origin. |

`NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_AUTH_URL` may already exist; reuse them if
they match these origins. Keep the existing `NEXT_PUBLIC_APP_URL` pointing to the
Software Solutions application, not Analytics. Existing public brand URL settings
remain as configured. The Analytics frontend does not need the Google client
secret or a Google measurement ID to read connected properties.

**Keep the existing `CREDENTIAL_ENCRYPTION_KEYS` value unchanged.** Confirm that
Django and workers receive the same existing key ring; do not generate a new ring
for Analytics or overwrite the current one. Existing database, Redis, session,
Celery and Django `SECRET_KEY` settings are shared prerequisites, not new
Analytics secrets. Google access/refresh tokens and property IDs do not need
manual Infisical entries: the connection flow stores tokens encrypted in the
backend and property selection records the selected identifiers.

After saving the values:

1. Rebuild the **Analytics** and **authentication** images so their public build
   settings are incorporated. Restarting an old Next.js image alone does not
   update its compiled `NEXT_PUBLIC_*` values.
2. Ensure the existing deployment maps the four backend keys above and the shared
   credential key ring into the API and relevant Celery processes, then redeploy
   them and apply migrations. Deployment exports Infisical root values into
   Ansible variables; it does not prove every new variable is already mapped to
   container environments. Those runtime mappings live in the infrastructure
   repository, not this application repository. Check the mapping without
   printing secret values before attempting Google consent.
3. Connect Google through the application and verify discovery and background
   synchronisation. Merely creating an Infisical entry does not authorise Google
   property access.

These locations are confirmed by the application's
[Analytics build workflow](../.github/workflows/analytics-adb-software-solutions-ci.yml),
[authentication build workflow](../.github/workflows/auth-adb-software-solutions-ci.yml),
and [deployment workflow](../.github/workflows/deploy.yml), together with the
reusable [production image workflow](https://github.com/adb-software-solutions/github-actions-workflows/blob/v1/.github/workflows/docker-build-push.yml)
and [deployment workflow](https://github.com/adb-software-solutions/github-actions-workflows/blob/v1/.github/workflows/deploy-application.yml).

#### Infisical: pull-request CI and local development

Pull-request image builds use the separate CI application project
`cb12b399-589e-4d62-b8b8-7f4ffe4538e0`, environment **dev**, root path **/**.
Only the public build settings above are relevant there; do not copy production
Google secrets into this CI project. The current build workflows treat these
public settings as optional and use application defaults when absent. A Google
OAuth connection is not needed for mocked tests or the Docker build.

For local Google testing, use the development OAuth client from step 5 in the
untracked `.devcontainer/.env`; this does not require creating additional Infisical
entries. Use the [environment variable table](#environment-variables) below as a
reference. Add these values without overwriting existing secrets:

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
3. Open ADB Analytics: `/` sends you to the existing account application's login
   with `/dashboard` as the return URL. An existing ADB session proceeds to the
   dashboard. Choose **Connect Google**, select your test-user Google account
   and grant reporting and supported GA4 configuration permissions in the same consent. A first analytics workspace is created
   automatically; no Business, domain or timezone form is required.
4. After Google returns to `/dashboard`, accessible websites are discovered
   automatically. Tick the websites to add, then choose **Add websites**. GA4 and
   Search Console are matched by domain, and timezones come from GA4 (Search
   Console-only websites use `America/Los_Angeles`). If several GA4 properties
   cover a domain, choose which to use. Adding websites queues initial sync.
   Reports refresh automatically as background jobs complete.
   Use **+ Add websites** to import more later. Verify the property role and
   explicitly confirmed configuration on a test property; no scope-upgrade flow
   is needed after initial consent.

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

| Symptom                                               | Check                                                                                                                                                       |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `org_internal` or account rejected by an Internal app | The authorizing Google account must belong to the project's Google organization; use External for accounts outside it.                                      |
| External Testing access blocked                       | Add the exact Google account under Audience → Test users, save, then select that account during consent.                                                    |
| `redirect_uri_mismatch`                               | Compare the exact callback with the selected client's registered redirect URI and backend environment; check the project/client pair.                       |
| Property missing from discovery                       | Confirm the selected Google account has property access, all three APIs are enabled in the client's project, and the granted scopes match the operation.    |
| Read reports work but configuration fails             | Check the granted scopes in Settings → Google accounts; reauthorise legacy connections, and confirm the account’s property role is Editor or Administrator. |
| Sync stops about a week after connection              | Check External Testing token expiry; complete production setup and reconnect. Revocation or organization policy can also require reconnection.              |
| Unverified-app warning or administrator block         | Check Verification Center and Google Workspace administrator policy; adding a test user does not override an organization block.                            |

### Environment variables

| Process              | Variable                         | Purpose                                                              |
| -------------------- | -------------------------------- | -------------------------------------------------------------------- |
| API/worker           | `ANALYTICS_GOOGLE_CLIENT_ID`     | Google Web OAuth client identifier                                   |
| API/worker           | `ANALYTICS_GOOGLE_CLIENT_SECRET` | Runtime-only OAuth client secret                                     |
| API                  | `ANALYTICS_GOOGLE_REDIRECT_URI`  | Exact registered callback; production default above                  |
| API                  | `ANALYTICS_FRONTEND_URL`         | Fixed post-OAuth return origin; defaults to analytics subdomain      |
| API/worker           | `CREDENTIAL_ENCRYPTION_KEYS`     | Existing shared Vault key ring                                       |
| Analytics build      | `NEXT_PUBLIC_API_URL`            | Shared API origin; local default `http://localhost:8000`             |
| Analytics build      | `NEXT_PUBLIC_AUTH_URL`           | Existing auth origin; local default `http://localhost:3004`          |
| Analytics/auth build | `NEXT_PUBLIC_ANALYTICS_URL`      | Exact analytics return origin; local default `http://localhost:3005` |

Existing SQL, cache, session and Celery variables remain required. Production
session/CSRF cookies remain secure and shared across the established parent domain.
CORS and CSRF origin allowlists add only the exact analytics origin and local port.
Rebuild the auth frontend with the analytics return URL configured before launch.
The new Dockerfile/workflow follow existing non-root, healthcheck, registry and
main-branch publishing conventions. The pnpm workspace already includes `sites/*`.

### Dashboard and automatic website discovery

Analytics uses a full-width, portfolio-first interface with a horizontal header,
locally bundled Inter typography, interactive Recharts comparisons and light/dark
themes. Theme preference is stored locally; authentication remains Django-backed.
`/` redirects to the dedicated authentication frontend with `/dashboard` as its
return destination; `/dashboard` checks the existing Django session and redirects
unauthenticated visitors through the same login. OAuth callbacks return to
`/dashboard`, preserving the authorized Business and connection selection.
Privacy and terms remain public and independent of authentication.

The first **Connect Google** action creates `My websites` only if the user has no
Business membership. Existing Business scopes and capabilities are preserved;
viewers cannot create or use connections by invoking onboarding endpoints.
Discovery reads GA4 property timezones and web data stream `defaultUri` values,
then matches verified Search Console Domain or root URL-prefix properties.
It groups bare/`www` variants for onboarding only; other subdomains remain separate
and report URL joins retain their existing conservative behavior. A Domain
property can cover a subdomain; the most specific/exact match is preferred.
Multiple GA4 matches require a user choice. Path-only Search Console properties,
invalid timezones, missing web URLs and inaccessible streams are reported instead
of guessed. Discovery is capped at 100 GA4 properties with an explicit notice.

Selection imports are limited to 25 websites per request and are revalidated
against fresh Google inventory. Business/website locks serialize creation and
linking; initial sync tasks dispatch only after commit. Repeating an identical
selection reuses the website and links without deleting reports or starting
another sync. Existing different provider links require explicit unlinking first.
The original GSC association path now persists its own metadata and search type;
it never uses uninitialized GA4 metadata. Neither discovery nor import changes
Google property settings.

### Portfolio, website overview and progressive exploration

- `/dashboard`: totals, comparisons and daily trends across accessible websites,
  attention signals and searchable/sortable website cards. No sidebar report maze.
- `/dashboard/websites/{id}`: visitors, visits, search clicks and key events;
  engagement; channels/referrals; pages/landing pages; events; search queries;
  countries/devices/browsers and actionable evidence together.
- Click metrics to change the chart; hover or use chart arrow keys for values.
  Click a website chart point or report row for evidence in a focus-managed drawer.
  Page evidence places exact URL matches from GA4 and Search Console side by side.
  Event drawers include daily counts and registered event parameter breakdowns.
- `/dashboard/websites/{id}/explore`: detailed reports, report-local filters,
  previous-period comparisons, custom event investigation, realtime and CSV export.
- `/dashboard/insights`: all portfolio signals with links to supporting reports.
- `/dashboard/settings` and `/dashboard/websites/{id}/settings`: Google connections,
  website/access management and existing explicit-confirmation GA4 administration.

Dates and explorer filters are shareable URL state. Missing snapshots show gaps
and unavailable values, not simulated traffic. The default reporting period ends
three days ago to align GA4 with final Search Console data. Custom periods can be
synchronised explicitly; in-progress snapshots refresh automatically.

`GET /api/analytics/portfolio` and `GET /api/analytics/websites/{id}/dashboard`
read stored snapshots only. Both require `analytics.view_report` within Business
membership; an optional portfolio `business_id` is checked independently. Viewers
can inspect reports and cached event-definition metadata but retain no Google
write capability. Google parameter reports are requested only on investigation.

Portfolio period visitors use the **overview** metric, never the sum of daily
users. Totals count each provider/external-property ID once, including properties
linked to several websites. Website cards can therefore show the same property-wide
figures; both cards and dashboards flag shared properties. This is not domain-level
filtering or cross-property person deduplication. Coverage reports the number of
available reporting properties; incomplete overview snapshots are excluded. A
percentage comparison is withheld when prior coverage is incomplete or zero.
Daily comparison points align by date offset and preserve missing dates.

Rankings are sorted over all stored rows before selecting the top rows. Traffic
channels/referrals aggregate additive session metrics across campaign rows first;
engagement rates are derived from summed engaged sessions and sessions. Visitor
counts are not added across acquisition rows. Provider truncation is disclosed.

Insights are deterministic and deliberately cautious:

- Visitor changes require a previous baseline of at least 100 and a change of 20%;
  search clicks require 30 and 25%; key events require 10 and 25%. Absolute changes
  below five do not create a signal.
- Acquisition shifts require a source present in both periods, a baseline of 30
  sessions and an absolute change of 25 sessions. They suggest investigation,
  without claiming the source caused the overall change.
- Search opportunities require at least 100 impressions, CTR below 2% and average
  position between 4 and 20. They recommend reviewing the query/page/snippet,
  without promising additional clicks or attributing a ranking change.
- A daily decline signal requires eight consecutive available dates, a preceding
  seven-day mean of at least 30 and latest traffic below half that mean. It is
  explicitly not adjusted for seasonality.
- Incomplete or privacy-thresholded reports do not generate insights. Missing
  baselines never produce invented percentage changes or causal explanations.

The focused frontend modules live in `src/components/experience`,
`src/components/reports` and `src/components/settings`. Existing Google discovery,
OAuth, sync, permissions and advanced administration remain shared backend services.
No production demo data or additional paid analytics/AI service is introduced.
Browser-review fixtures intercept APIs only in isolated Playwright sessions.

### Repeatable visual review

Build the application, then start an isolated production preview:

```bash
NODE_ENV=production pnpm --dir sites/analytics-adb-software-solutions build
NODE_ENV=production pnpm --dir sites/analytics-adb-software-solutions exec next start -p 3105
```

In another terminal:

```bash
pnpm --dir sites/analytics-adb-software-solutions exec playwright install chromium
pnpm --dir sites/analytics-adb-software-solutions test:browser
```

`tools/visual-review.mjs` intercepts analytics API requests inside its own browser
session with explicitly isolated fixtures. It never inserts database rows, calls
Google or changes a real account. It checks portfolio-to-website navigation,
metric selection, chart tooltips/day inspection, page/source/event drawers,
registered parameter exploration, the advanced explorer, Escape dismissal,
light/dark modes and horizontal overflow at 390, 768, 1440, 1920 and 2560 pixels.
Screenshots are written to the system temporary directory under
`adb-analytics-review`; inspect them visually, including mobile and dark mode.
Override `ANALYTICS_REVIEW_URL` or `ANALYTICS_REVIEW_OUTPUT` when needed. Browser
checks supplement the unit/API tests and do not verify live Google reporting.

### Settings and unattended Google access

Settings has four areas: **Websites** (properties, detected timezones and sync),
**Google accounts** (account-wide consent, health and disconnection), **Events &
conversions** (observed events, key actions and progressively disclosed tracking
plans/custom definitions), and **Workspace** (business details, members and roles).
Workspace access never depends on having a website. Individual website settings
link back to the account-wide Workspace area; account disconnection clearly warns
that all linked websites will stop collecting. Viewers retain report-only access.

All new Google connections request the documented read/edit/search scopes upfront.
Legacy `reporting`/`administration` API mode values remain compatible but request
this same set. Reauthorisation sends an existing connection ID in session-bound
OAuth state, validates workspace capability again, and verifies the returned
Google subject matches the existing account **before** replacing credentials.
Linked properties and reports are preserved. Cancelled or failed consent leaves
the existing credentials intact. Partial consent is displayed as missing
permissions, not treated as proof of Google property-level edit authority.

Apply migration `analytics.0004_google_token_refresh_health`, then restart the
existing API, Celery workers and Beat as part of the normal application release.
No new environment variables, secrets, worker services or infrastructure are
required. Beat dispatches `analytics.enqueue_token_refreshes` every **five minutes**;
`analytics.refresh_google_token` refreshes connected accounts within **ten minutes**
of access-token expiry, independently of browser sessions. Existing six-hour
report scheduling continues for active websites while credentials remain valid.
Both token refresh and report sync use the same credential service and connection
row lock; duplicate workers recheck persisted expiry and do not repeat a successful
exchange. Token storage and expiry updates commit together. A missing replacement
refresh token preserves the current encrypted token; a returned replacement is
stored atomically. Reauthorisation of a known revoked offline grant requires a
new refresh token rather than pretending an access token repairs that grant. A provider 401 gets one coordinated access-token recovery
attempt before requiring reauthorisation; concurrent newer tokens are reused. Disconnection and reauthorisation take the same lock.

Transient failures retain the connection, persist a shared retry gate and use
exponential backoff (60 seconds up to one hour, plus jitter). Numeric Google
`Retry-After` hints are honoured up to one day. A token task makes at most five
Celery retries; Beat later resumes due transient failures. Valid access tokens may
still serve reports during a retry delay. Malformed responses do not overwrite
working encrypted credentials. Invalid/expired/revoked grants mark the connection
**Reconnect required**, stop automatic refresh/sync dispatch and do not enter an
endless retry loop. OAuth client-configuration failures require an operator to
check Google setup. Reauthorising the same account clears the refresh failure
state so scheduled collection can resume.

Connection health APIs expose status, last refresh/validation, expiry, failure
count and next retry only. They never return access tokens, refresh tokens or
credential records. Provider error messages are mapped to safe explanations;
Celery arguments contain a connection ID only. Application access/JSON logging
redacts the OAuth callback query (including codes/state) without changing server
handlers. Keep equivalent query redaction at any external access-log boundary. Application write capability,
explicit confirmation, Google scope/property permissions and audit logging remain
required for every supported Google configuration write.

**Refresh is not a refresh-token lifetime extension.** External Testing grants
using these scopes can expire after seven days, even if access tokens are refreshed
regularly. Production publishing does not guarantee indefinite refresh-token
validity: revocation, account policies, token limits and other Google expiry rules
still apply. The operator will manually publish the OAuth app when public policy
URLs are live; this implementation does not change Google publishing status.
See the [manual production checklist above](#8-move-external-production-access-out-of-testing)
and Google’s [OAuth expiration rules](https://developers.google.com/identity/protocols/oauth2#expiration).

The repeatable browser review also covers all Settings areas, account health,
legacy-scope reauthorisation, light/dark mobile layouts and confirmed key-event
configuration. Google requests/writes in that review are isolated fixtures; live
consent, refresh and property-role checks still require a real test account.

### Public policy routes

`/privacy` and `/terms` are public Server Component pages with no authentication
or provider API dependency. The root layout links them from every application
state. Their notices describe the current single-operator use, Google API data,
optional writes, essential cookies, retention and separate disconnection/deletion.
Confirm the published URLs are reachable without signing in before adding them
to Google Branding; creating these routes does not deploy them automatically.

### Live verification checklist

Automated tests mock all Google responses. Before production use, verify consent
and any Google verification requirements; offline refresh; revocation; real GA4
and GSC property discovery; timezone selection; initial and custom-range sync;
provider quota/permission error displays; definition creation and key-event deletion
on a test property; account login/MFA return across the real subdomains; and the
image build/publish in the existing CI environment. Provider reports may exclude
privacy-filtered queries, have processing delays or expose only top rows; missing
or truncated data is not equivalent to zero.

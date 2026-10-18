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

Select the same project in the console's project selector for every link below;
these links are not pinned to a particular project ID.

1. [Create a Google Cloud project](https://console.cloud.google.com/projectcreate)
   or [select an existing project](https://console.cloud.google.com/cloud-resource-manager).
   Open each API's library page and click **Enable**:
   [Google Analytics Data API](https://console.cloud.google.com/apis/library/analyticsdata.googleapis.com),
   [Google Analytics Admin API](https://console.cloud.google.com/apis/library/analyticsadmin.googleapis.com),
   and [Google Search Console API](https://console.cloud.google.com/apis/library/searchconsole.googleapis.com).
   Check [Enabled APIs & services](https://console.cloud.google.com/apis/dashboard)
   afterwards.
2. Open [Google Auth Platform → Branding](https://console.cloud.google.com/auth/branding)
   and click **Get started** if the platform has not been configured. Set the
   application name, verified `adbsoftwaresolutions.co.uk` domain, privacy policy
   and support contact. In [Audience](https://console.cloud.google.com/auth/audience),
   configure who can use the app and add test accounts while it is in Testing. External production access to
   sensitive scopes may require Google verification. Testing-mode refresh tokens
   may expire; complete the appropriate publishing/verification process.
3. Open [Google Auth Platform → Clients](https://console.cloud.google.com/auth/clients),
   choose **Create client**, and select **Web application**. Add this exact
   production URI under **Authorized redirect URIs**:
   `https://api.adbsoftwaresolutions.co.uk/api/analytics/oauth/callback`.
   For development register a separate exact callback such as
   `http://localhost:8000/api/analytics/oauth/callback` and set the variable below.
4. In [Google Auth Platform → Data Access](https://console.cloud.google.com/auth/scopes),
   use **Add or remove scopes** to configure the scopes below. Reporting consent
   requests `openid`, `email`,
   `https://www.googleapis.com/auth/analytics.readonly` and
   `https://www.googleapis.com/auth/webmasters.readonly`. Administration adds
   `https://www.googleapis.com/auth/analytics.edit`. Reporting consent never
   requests write scope. No BigQuery or paid API is required.
5. The Google account must have access to each GA4 and Search Console property.
   Editing custom definitions/key events additionally requires the corresponding
   Google property role (normally Editor or Administrator). OAuth edit scope does
   not override Google's property authorization. Domain and URL-prefix Search
   Console properties are supported, including encoded `sc-domain:` identifiers.
6. Supply backend secrets through the existing runtime secret-injection process.
   Do not put Google secrets into frontend build environments.
7. Apply Django migrations and restart API, existing workers and Beat. Deploy the
   analytics frontend image using the existing automation. No Ansible, Terraform,
   DNS, provisioning or other infrastructure changes are part of this feature.
8. Log in with an existing ADB account, create a Business and Website, connect
   Google, discover properties and link one or both integrations. Match the
   Website timezone to the selected GA4 property's timezone. Follow job progress,
   then synchronize the desired date range and refresh reports.

Google's [OAuth consent setup guide](https://developers.google.com/workspace/guides/configure-oauth-consent)
and [OAuth client creation guide](https://developers.google.com/workspace/guides/create-credentials#oauth-client-id)
provide the corresponding console navigation instructions.

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

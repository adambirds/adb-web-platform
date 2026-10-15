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

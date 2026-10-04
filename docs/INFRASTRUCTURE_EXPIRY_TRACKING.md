# Domain and TLS expiry tracking

## Existing and new behavior

Previously, Celery ran configured Monitoring checks, live TLS probes checked
served certificate expiry, and Domain expiry checks read manually maintained
`DomainProfile.expires_on`. Inventory metadata was not refreshed automatically.

The platform now discovers public registration/certificate metadata and creates
expiry checks for current structured Domain and TLS Certificate resources.
Renewals are detected as changed expiry dates or changed certificates. Provider
renewal transactions, ACME issuance and payments are outside this workflow.

## Operating the workflow

1. Create a Domain from **Infrastructure → Domains** or **Resources**. Both
   pages manage the same resource-backed Domain profile and show its expiry.
2. For TLS, create a structured TLS Certificate. Link a concrete HTTPS Website
   Endpoint to it, or supply a concrete certificate common name. Wildcards need
   an explicit linked endpoint; Domain-coverage links do not prove where a
   certificate is deployed.
3. Apply Django migrations and run Celery Beat and workers consuming `general`.
4. Open the resource details to see expiry metadata, **Metadata last checked**
   and **Metadata refresh error**. Open Monitoring or the resource's Monitoring
   section to see checks, history and incidents.

Beat dispatches `infrastructure.enqueue_metadata_refreshes` every five minutes.
It enqueues current Active/Maintenance/Deprecated profiles whose metadata is due.
`infrastructure.refresh_resource_metadata` uses a Redis resource lock and checks
freshness again inside the worker. Successful discovery runs daily; failures
retry after an hour. Retired/Archived resources are not refreshed or monitored.
Planned resources are not automatically enrolled in discovery.

The first refresh creates an expiry check if one of the corresponding type does
not already exist. Default checks run hourly, warn within 30 days, and open or
resolve incidents after one observation. Existing checks, custom thresholds and
paused checks are preserved. Edit these through the existing Monitoring form.
The usual 30-second Monitoring dispatcher executes due checks.

A stored certificate expiry check is distinct from a live TLS validity check:
the former evaluates inventory dates, while the latter validates the served
TLS endpoint and certificate. Both can be configured on the same resource.

Incidents use existing capability- and Client-scoped Monitoring APIs and
operational notifications. There is no new public endpoint or secret access.

## Discovery and authority

Domain discovery uses the [IANA RDAP bootstrap registry](https://www.iana.org/assignments/rdap-dns)
and registration/expiration events defined by
[RFC 9083](https://www.rfc-editor.org/rfc/rfc9083.html). The IANA bootstrap is
cached for 24 hours. Registry requests use HTTPS, ten-second timeouts and a 1 MB
response limit. Redirects and arbitrary response links are not followed.
The response must identify the exact requested Domain. Missing or conflicting
expiry dates fail discovery rather than inventing a value. Unsupported TLDs
and registries that omit expiry require manually maintained dates or a future
explicit registrar integration.

Discovered Domain expiry replaces the stored expiry so renewals are reflected.
Registration date and transfer-lock metadata fill missing values only. Registrar
accounts, account IDs, privacy and auto-renew policy are never inferred. Registry
expiry is the public registration expiry, not a registrar billing commitment.
RDAP contact/person data is not stored.

TLS discovery prefers an explicitly linked current HTTPS Endpoint, then a
concrete stored common name on port 443. The endpoint supplies its configured
port and SNI hostname. Certificate-chain and hostname validation remain enabled.
Public issuer, common name, serial, SHA-256 fingerprint and validity dates are
updated from the observed leaf certificate. The last successful endpoint origin
(host/port only) is retained for subsequent discovery if a served wildcard
replaces the initially configured common name; it is also visible in details. Provider accounts, certificate type,
coverage links, keys and auto-renew policy are preserved.

Expired, untrusted and self-signed endpoints cannot supply metadata through this
verified probe. Their previous dates remain available and the lookup error is
visible. A trusted replacement becomes discoverable on the next retry.

Failed discovery never clears existing metadata. A refresh error produces an
execution-error observation on the inventory expiry check, so stale discovery
is visible even when an old stored date is in the future. Successful refresh
clears the error; the normal check then evaluates expiry and can resolve the
incident. System audit events record only changed field names and source type,
with explicit resource/Client context.

## Deployment and verification

No new environment variables or dependencies are required. Workers need outbound
HTTPS to `data.iana.org`, IANA-listed RDAP registries and configured TLS endpoints.
The existing Redis cache and worker queue are reused.

```bash
cd backend
python manage.py migrate
```

From the repository root:

```bash
tools/test-backend apps.infrastructure.tests.test_metadata_refresh
tools/test-backend apps.monitoring.tests adbsoftwaresolutions.tests
tools/lint
```

This supplements the [Infrastructure architecture](INFRASTRUCTURE_ARCHITECTURE.md)
and preserves the [permissions model](PERMISSIONS_AND_ACCESS_MODEL.md).

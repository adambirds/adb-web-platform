# Credential Vault Architecture

## Purpose

The Credential Vault is the staff-only operational secret store for the ADB
Business Platform. It is designed to replace ad-hoc password, SSH key, API
token, certificate and recovery-code storage while remaining directly connected
to Clients and the structured Infrastructure resource graph.

The vault separates **credential metadata** from **secret material**. Normal
list/detail APIs return only safe metadata and the names of secret fields that
exist. Secret values require explicit reveal, copy or download actions and each
action is independently permission checked and audited.

This document is the authoritative credential-security architecture. It should
be read with:

- `PLATFORM_MASTER_PLAN.md` for platform direction and implementation order;
- `PERMISSIONS_AND_ACCESS_MODEL.md` for the wider capability/scope model;
- `DOMAIN_MODEL_AUDIT.md` for model boundaries and migration discipline;
- `INFRASTRUCTURE_ARCHITECTURE.md` for resource topology and specialist links;
- `MICROSOFT_GRAPH_TICKETING_SETUP.md` for a concrete Vault-backed certificate
  integration;
- `CURRENT_STATE_AND_FOUNDATION_CHECKLIST.md` for implementation status.

## Operational principles

- Active credentials are the default view.
- Inactive and archived credentials are history and must be explicitly selected.
- Credentials can be ADB Internal or Client-owned.
- Client-owned credentials may only link to infrastructure owned by that same
  Client.
- Internal credentials may link to Internal or Client infrastructure. This
  supports shared ADB operational credentials such as provider/API accounts that
  manage Client resources.
- A Client credential must never bridge Clients or link to ADB Internal
  infrastructure.
- Secret values never appear in normal credential list/detail responses.
- Encrypted notes are secret material. They are not stored in the legacy
  plaintext `notes` column.
- Reveal, clipboard copy and download are separate actions so the audit trail
  records what the user actually did.
- Resource visibility never implies secret visibility.
- Other domains reference Credentials rather than introducing duplicate
  plaintext password/token/private-key fields.

## Typed credential templates

The initial built-in templates are:

- Username and password
- SSH key
- Database login
- API key or token
- OAuth application
- Service account
- Certificate and private key
- Licence key
- Recovery codes
- Encryption key
- Custom secret

Each template defines dynamic fields with:

- a stable key;
- a display label;
- a field kind (`text`, `password`, `textarea` or `url`);
- a storage class (`username`, `url`, `metadata` or `secret`);
- required/optional behaviour.

Safe values such as usernames, URLs and identifiers can remain queryable
metadata. Passwords, tokens, key material, encrypted notes and other sensitive
values use the encrypted secret payload.

## Encryption model

`StoredCredential.encrypted_secret_payload` contains a versioned JSON payload
encrypted with Fernet. No plaintext secret is written to the new vault fields.

The runtime key ring is configured through `CREDENTIAL_ENCRYPTION_KEYS`. It is
an ordered list of Fernet keys:

1. The first key is the current primary encryption key.
2. Remaining keys are accepted for decryption during rotation.
3. New writes always use the primary key.
4. Existing records can be re-encrypted with the primary key without exposing
   plaintext to the UI.

### Generating a key

Generate Fernet keys using the `cryptography` package. Treat the resulting value
as a production secret and never commit it to Git.

```python
from cryptography.fernet import Fernet

print(Fernet.generate_key().decode("ascii"))
```

### Rotation procedure

A safe rotation sequence is:

1. Generate a new Fernet key.
2. Deploy `CREDENTIAL_ENCRYPTION_KEYS` with the new key first and the previous
   key(s) after it.
3. Re-encrypt stored credential payloads using the application rotation
   service/maintenance process.
4. Verify all credential payloads decrypt successfully using only the new key.
5. Remove retired keys from configuration.

Do not remove an old key before every payload encrypted with it has been rotated
or the affected credentials will fail closed.

## Legacy plaintext reconciliation

Older `StoredCredential` records pre-date the encrypted vault and may contain
values in:

- `password`
- `api_key`
- `secret_key`
- `private_key`
- `notes`

These columns remain temporarily for migration compatibility only. New vault
create/edit operations do not write sensitive values to them.

The credential detail API exposes only `has_legacy_plaintext`, never the legacy
values. An authorised staff member can run **Encrypt legacy values** from the
credential workspace. The operation runs atomically:

1. Read the legacy plaintext fields on the server.
2. Merge them into the encrypted secret payload.
3. Blank the legacy plaintext columns.
4. Record the actor and safe field-name-only audit metadata.

The transaction is intentionally all-or-nothing so a failed encryption operation
cannot blank the old values without successfully storing their encrypted
replacements.

Migrated encrypted fields remain usable even when an older CredentialType has no
modern template field schema. The workspace projects those existing encrypted
field keys safely rather than making migrated secrets disappear from the
operator experience.

Once production data has been reconciled and verified, a future migration can
remove the legacy plaintext columns entirely.

## Permissions and scope

Django permissions describe **what** a staff member can do. Client scope
describes **where** they can do it.

Core permissions are:

- `credentials.view_storedcredential`
- `credentials.add_storedcredential`
- `credentials.change_storedcredential`
- `credentials.delete_storedcredential` (archive lifecycle action)
- `credentials.reveal_storedcredential`
- `credentials.copy_storedcredential_secret`
- `credentials.download_storedcredential_secret`

Secret-action permissions are intentionally separate. A staff role can, for
example, be allowed to copy a password for operational use without being allowed
to reveal the entire encrypted payload.

Non-superuser staff are scoped to:

- ADB Internal credentials; plus
- Client credentials for Clients visible through the existing access-control
  policy.

Infrastructure link choices are also passed through the Infrastructure access
policy before ownership-boundary validation is applied.

Client-owned Credentials may only link to Resources owned by that Client.
Internal Credentials may link to Internal or Client Resources where that
represents legitimate shared ADB operational access.

## Auditing

The vault records safe audit events without secret values. Events include:

- credential created;
- credential updated;
- credential archived;
- secret revealed;
- secret copied;
- secret downloaded;
- legacy plaintext encrypted.

Secret events record field names only. Secret values must never be placed in
`AuditEvent.metadata`, logs, exception messages or URLs.

## API surface

Staff APIs are under `/api/admin`.

### Metadata and CRUD

- `GET /credential-options`
- `GET /credentials`
- `POST /credentials`
- `GET /credentials/{credential_id}`
- `PUT /credentials/{credential_id}`
- `POST /credentials/{credential_id}/archive`

The list supports status, ownership, Client, credential type, Infrastructure
resource, search and pagination filters.

### Secret actions

- `POST /credentials/{credential_id}/reveal`
- `POST /credentials/{credential_id}/secrets/{field_key}/copy`
- `POST /credentials/{credential_id}/secrets/{field_key}/download`
- `POST /credentials/{credential_id}/migrate-legacy-secrets`

Secret actions use POST so they remain CSRF protected and are not represented as
cacheable/navigation URLs.

The download response explicitly uses `private, no-store`, `no-cache` and
`nosniff` headers.

## Frontend behaviour

The main `/admin/credentials` workspace provides:

- Active credentials by default;
- explicit Inactive, Archived and All history views;
- search, ownership, Client and credential-type filters;
- paginated operational register;
- typed credential creation;
- drawer and full-page credential workspaces;
- inline editing without re-fetching existing secret values;
- explicit reveal/hide controls;
- audited clipboard copy controls;
- audited file downloads for key/certificate/JSON material;
- Infrastructure resource links;
- legacy plaintext warning/reconciliation action;
- archive lifecycle action.

Client pages embed the active Client-owned credential register. Infrastructure
Resource pages embed credentials linked to that resource. This keeps credentials
contextual rather than forcing staff to search a separate password database for
every operational task.

## Secret handling in the browser

Revealed values exist only in React component state for the open credential
workspace. Closing the drawer, changing credential, reloading the record or
selecting **Hide secrets** clears that state.

The frontend must not persist secret values in:

- localStorage;
- sessionStorage;
- cookies;
- route/query parameters;
- analytics events;
- normal application caches.

Clipboard copy asks the backend for only the requested field. The returned value
is handed directly to the Clipboard API and is not added to the visible
credential model.

## Service/integration secret access

Backend integrations such as Microsoft Graph may decrypt a Credential through a
server-side credential service path when they are authorised by application
logic to use it.

This is distinct from human secret actions:

- a worker using a Graph private key does not create a fake human reveal event;
- a user configuring Graph does not automatically gain permission to reveal the
  private key;
- every process performing service decryption must have the correct
  `CREDENTIAL_ENCRYPTION_KEYS` key ring;
- service code must never log the decrypted value.

This distinction is important for Monitoring, provider APIs, Kubernetes and
future commercial integrations as those domains are built.

## Failure behaviour

Secret storage is fail-closed:

- no configured key -> writes/reveals fail;
- wrong/retired key -> decryption fails;
- malformed or unsupported payload -> decryption fails;
- missing secret field -> explicit not-found response;
- missing permission -> forbidden;
- out-of-scope credential/resource -> unavailable/not found.

The platform must never fall back to plaintext storage because encryption
configuration is missing.

## Cross-domain contract

New domains that need authentication material must follow this pattern:

1. store safe technical metadata on the domain/resource model;
2. store the actual password/token/private key/recovery material in a Vault
   Credential;
3. link/reference the Credential through a typed/resource relationship;
4. use service-side decryption for automated integrations;
5. use explicit human reveal/copy/download actions for operator access;
6. never duplicate the secret into KB documents, Monitoring results, Ticket
   Notes, Infrastructure metadata, logs or search indexes.

`INFRASTRUCTURE_ARCHITECTURE.md` applies this pattern to the technical resource
graph. `MICROSOFT_GRAPH_TICKETING_SETUP.md` is the current concrete deployment
example.

## Future work

After the initial vault is stable:

- remove reconciled legacy plaintext columns;
- add scheduled expiry/rotation reminders;
- add bulk key-rotation management tooling and reporting;
- add credential health reporting (expired, expiring, legacy, unlinked, stale
  rotation);
- consider per-field reveal timeout behaviour;
- add richer custom credential-template administration if required;
- connect Credentials to KB/runbook procedures where an operational
  relationship exists;
- consider break-glass/step-up authentication for especially sensitive roles if
  the product threat model requires it.

## Resource-context creation and link selection

Creating a Credential from any Infrastructure resource workspace preselects that
resource and submits its link atomically with the Credential. The form preserves
initial and existing links while the scoped resource options are loading, then
validates their eligibility against the selected Credential ownership.

The create/edit form's infrastructure selector supports search by resource name,
type and Client/Internal label. Filtering the displayed list does not remove
selected links; the selection count remains visible and the results scroll within
the form. Backend scope and ownership validation remain authoritative.

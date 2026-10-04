# Development data

## Purpose

The ADB Business Platform includes deterministic fake-data tooling so the
operations UI can be developed against realistic cross-domain context rather
than empty tables.

Development data should exercise the product's current-first workspaces,
Client/Internal ownership, permission boundaries and relationships without ever
containing real Client secrets or private infrastructure data.

Credential-specific security rules are defined in
`CREDENTIAL_VAULT_ARCHITECTURE.md` and apply to development data as well as
production data.

---

## 1. Canonical development seed command

After applying migrations, run from `backend/`:

```bash
python manage.py seed_all_development --reset
```

For denser pagination/search/workspace testing:

```bash
python manage.py seed_all_development --reset --scale 3
```

The seeders refuse normal use when `DEBUG=False`. A `--force` escape hatch is
only for disposable non-production environments and must never be used against
real platform data.

`--reset` removes records created by the development seeders and rebuilds the
demo dataset. It does not intentionally flush unrelated development records.

Lower-level commands remain available for focused work:

- `seed_development`;
- `seed_task_workflows_development`;
- `seed_infrastructure_development`;
- `seed_ticketing_development`.

For normal local work, prefer `seed_all_development` because it handles the
required ordering/dependencies between seeders.

---

## 2. Data represented

At normal scale, the development dataset covers realistic examples across:

- the three ADB Brands;
- fake Clients and multiple Contacts;
- active/inactive/history lifecycle examples;
- Projects and project notes;
- CRM Leads and pipeline reference data;
- Tasks, Task Lists, Sections, Subtasks and Dependencies;
- recurring/current/completed work examples;
- Task/Project/Internal Time entries;
- Knowledge Base documents and version-history foundations;
- fake Credential metadata and encrypted demo secret values;
- active/inactive/archived Credential lifecycle examples where useful;
- native structured Provider Account, Server, Network, Subnet, network-interface and IP-address examples;
- native Database Instance, Logical Database, Application, Application Environment and Source Repository examples;
- typed Application/Repository role links;
- native Website/Endpoint, Domain, DNS Zone/Record and non-secret TLS Certificate/Domain-coverage examples;
- both Internal and Client-owned structured compute, data/application and web-infrastructure examples where an active demo Client exists;
- Mobile App/API/Bot/Email-system examples;
- Ticket Queues, configured demo Mailboxes, Tickets, Messages, Notes and
  attachment/scan-state examples;
- Brand-aware Blog/FAQ/Testimonial/Case Study content;
- Audit events/recent activity.

The exact counts are seed implementation detail and may grow as a domain
matures. Tests should not rely on specific production-like IDs/counts from the
development seed command.

### Resource-only Infrastructure

All infrastructure demo data uses `InfrastructureResource` and native typed
profiles. The seeders no longer create flat inventory or reconciliation examples.
Ownership is explicitly Internal or an existing demo Client.

`seed_infrastructure_development` now also creates deterministic native examples
for:

- a shared Internal DigitalOcean Provider Account;
- an Internal production VPC and subnet;
- an Internal modern Server profile with a network interface and reserved demo
  IPv4 addresses;
- a Client-owned Server using the shared Internal Provider Account when an active demo Client is available;
- an Internal PostgreSQL Database Instance and Logical Database;
- an Internal ADB Platform Application, production-like Application Environment, GitHub Provider Account and Source Repository;
- a typed primary Application/Repository link;
- an Internal Website connected to its Application Environment, reserved example Domain, DNS Zone/Records and non-secret TLS metadata;
- a shared Internal Cloudflare Provider Account used for DNS/CDN/WAF/registrar context without embedding any API token;
- matching Client-owned Database/Application/Environment/Repository and Website/Domain/DNS/TLS examples using the same ownership-boundary rules;
- deliberately nearer fake Client Domain/TLS expiry dates so the next Monitoring/expiry work has useful development context.

The IP addresses use documentation/reserved ranges and Web Infrastructure uses `.example.test` names. Database/application/repository/web metadata is fake operational context only; authentication material and private keys remain in fake encrypted Vault Credentials rather than specialist fields.
Structured development resources are validated through the same
model invariants as normal application records.

Where a seeder creates structured resources/relationships directly, it must obey
the same ownership and cross-Client validation as normal application code.

### Credential Vault data

The typed Vault is an implemented part of the platform. Development Credentials
should exercise the same services/contracts as normal Vault records:

- Client/Internal ownership;
- typed CredentialType/template schema;
- encrypted secret payloads;
- Active-first lifecycle;
- Infrastructure resource links where useful;

Fake credential secrets must be obvious placeholders such as
`demo-password-not-a-real-secret` and must use the encrypted credential service
rather than legacy plaintext fields.

Never copy real Microsoft Graph certificates/private keys, Client passwords,
API tokens, SSH keys or production recovery codes into seeders/fixtures.

Do not put fake secret values into AuditEvent metadata merely because the data
is non-production; the development dataset should exercise the real security
boundary.

---

## 3. Local workflow

For a fresh/newly migrated environment:

```bash
cd backend
python manage.py migrate
python manage.py seed_all_development --reset
```

Then start the normal backend/frontend/Celery development processes and sign in
through the authentication application.

Use a local superuser when reviewing the complete cross-domain dataset. Use
restricted staff users when reviewing capability/Client/Queue-scope behaviour;
a restricted account correctly sees only part of the seeded data.

For Vault permission review, include users with combinations such as:

- metadata view without reveal/copy/download;
- reveal permission;
- copy permission;
- download permission;
- selected Client scope that excludes some Client Credentials.

Create a local superuser when needed:

```bash
python manage.py createsuperuser
```

---

## 4. Reference fixture

`apps/core/fixtures/development_reference.json` remains the small baseline
fixture for reference/taxonomy data such as Lead sources, Task statuses,
Credential types and Knowledge Base sections.

It can be loaded with:

```bash
python manage.py loaddata apps/core/fixtures/development_reference.json
```

The comprehensive seed commands create/update the reference data they need, so
prefer `seed_all_development` for normal platform development.

Typed Vault templates may also ensure their built-in CredentialType definitions
through the Credential template service. Do not rely on fixture display names
alone for stable field schemas.

---

## 5. Seeder expectations for new work

When a domain gains meaningful UX, add representative development data where it
materially improves hands-on review.

Examples for upcoming phases:

- current + retired Infrastructure Resources and useful topology relationships;
- Vault Credential/resource links using only fake encrypted values;
- unhealthy/healthy Monitoring checks and incidents once Monitoring exists;
- authenticated Monitoring examples that reference fake Vault Credentials
  rather than owning plaintext passwords/tokens;
- nested Client/Internal KB folders/documents/resource/Credential links after
  the KB redesign;
- varied staff access/default Ticket Queue/Vault secret-action permissions for
  Users & Access and Dashboard work;
- commercial examples only once those models are explicitly designed.

Seed data should make current-first views meaningful: include enough history to
test history filters without making all demo records inactive/closed.

---

## 6. Rules

- Never use real Client/contact/credential/infrastructure data.
- Use reserved/example domains and clearly fake people/organisations.
- Keep generation deterministic unless randomness is itself under test.
- Use application/domain services where that is required to preserve invariants
  rather than bypassing them with unsafe direct inserts.
- Keep Client/Internal ownership internally consistent.
- Never use seeders to bypass permission/security design.
- Never write secret values to legacy plaintext Credential columns merely
  because the environment is development.
- Never expose seeded secrets through normal Credential metadata APIs/search.
- Seed data is for development/demos, not a substitute for focused unit/
  permission-boundary tests.

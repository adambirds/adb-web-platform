# Permissions and Access Model

## Purpose

This document defines the canonical authorisation model for the ADB Business
Platform. It should be read with `PLATFORM_MASTER_PLAN.md`,
`DOMAIN_MODEL_AUDIT.md`, `CURRENT_STATE_AND_FOUNDATION_CHECKLIST.md` and
`CREDENTIAL_VAULT_ARCHITECTURE.md`.

The platform contains sensitive Client, communication, infrastructure,
credential and future commercial data. Access therefore answers two separate
questions:

1. **Capability** — may this identity perform this type of action?
2. **Scope** — which Clients, Ticket Queues or owned resources may that
   capability act on?

Frontend visibility is usability only. Django remains the security boundary.

---

## 1. Core principles

1. **Django is authoritative.** Every protected query/mutation enforces access
   server-side.
2. **Capability and scope are separate.** `view_ticket` does not imply every
   Ticket is visible.
3. **Django Groups are role bundles.** Do not build a competing role engine.
4. **Least privilege is the normal staff model.** Routine operators should not
   require superuser.
5. **Superuser bypass is deliberate, not the normal workflow.** Sensitive
   operations should still audit where useful.
6. **Sensitive actions have narrow permissions.** Credential metadata access is
   distinct from reveal, copy and download.
7. **Denied objects do not enter normal API results.** Scope before
   serialisation.
8. **Indirect paths obey the same scope.** Drawers, selectors, search,
   dashboards, Calendar, Client workspaces, reports and exports do not widen
   access.
9. **Client context enriches navigation; it never grants access by itself.**
10. **Access changes are auditable.**
11. **Current-first views still scope normally.** A focused My/Active view is
    not a shortcut around domain policy.
12. **Server-backed preferences are not permissions.** Ticket Queue defaults
    change what the user sees first, never what the user is authorised to see.
13. **Secret storage and secret access are separate concerns.** A backend
    integration may decrypt through the Credential service without giving a
    human staff user reveal permission.

---

## 2. Identity model

The custom Django `User` remains the identity type.

Internal operations primarily use active staff users. Future Client portal
identities should continue through the same authentication system and link to
ClientContact rather than introduce another identity authority.

Django `is_active`, `is_staff`, `is_superuser`, Groups and Permissions remain
platform primitives.

The dedicated authentication/account frontend owns login and account-security
UX, while the `/admin` Users & Access workspace will own authorised staff
administration over the Django permission/scope model.

---

## 3. Capability permissions

Use Django model permissions where they accurately describe an action and
narrow custom permissions for domain-specific/sensitive operations.

Examples established by current domains include concepts such as:

```text
clients.view_client
clients.add_client
clients.change_client
clients.view_clientcontact

crm.view_lead
crm.change_lead

projects.view_project
projects.change_project

tasks.view_task
tasks.change_task

time_tracking.view_timeentry

ticketing.view_ticket
ticketing.reply_ticket
ticketing.assign_ticket
ticketing.close_ticket

infrastructure.view_infrastructureresource
infrastructure.change_infrastructureresource

credentials.view_storedcredential
credentials.add_storedcredential
credentials.change_storedcredential
credentials.delete_storedcredential
credentials.reveal_storedcredential
credentials.copy_storedcredential_secret
credentials.download_storedcredential_secret

access_control.manage_staff_access

core.view_auditevent
```

Credential secret-action permissions are deliberately independent. A role can
be allowed to view metadata without secrets, or be allowed to copy a single
secret field without receiving a broad unrestricted secret payload. The Vault
contract is defined in `CREDENTIAL_VAULT_ARCHITECTURE.md`.

Do not invent broad aliases such as `can_manage_everything` to bypass this
separation.

---

## 4. Groups / role bundles

Django Groups are the role mechanism. Human-friendly role templates may include
Administrator, Operations, Support, Accounts or Read Only, but those names are
convenience bundles only.

Effective access remains:

```text
Django permissions
+ object scope
+ operation-specific validation
```

A future Users & Access screen should make this understandable without hiding
the actual effective capabilities, including Credential reveal/copy/download
rights.

---

## 5. Staff object scope

Object scope lives in `apps.access_control`.

### 5.1 StaffAccessProfile

A scoped staff user may have a `StaffAccessProfile` containing at least:

- `all_clients`;
- `all_ticket_queues`;
- `default_ticket_queues` for the user's normal Ticket work focus.

A non-superuser without an appropriate profile does not silently receive broad
object access.

`default_ticket_queues` is a **preference**, not an authorisation grant:

- an empty stored default selection means **all accessible enabled queues**;
- an explicit subset means default Ticket focus views use that subset;
- choosing all currently accessible queues normalises back to the empty/all
  representation;
- inaccessible/disabled queues are never made visible by the preference.

### 5.2 ClientAccessGrant

When `all_clients` is false, grants identify selected Clients.

Client scope applies transitively to Client-owned operational resources through
domain policies/services, including Projects, Tasks, Time, Infrastructure,
Credentials, Knowledge and Client-matched Tickets where relevant.

### 5.3 TicketQueueAccessGrant

When `all_ticket_queues` is false, grants identify selected Ticket Queues.

Queue scope is independent from Client scope. Ticket operations may require
both.

### 5.4 Policy helpers

Reuse/extend central access-control policies rather than duplicating ad-hoc
checks in every view. Existing primitives include concepts such as:

```python
get_access_profile(user)
can_access_client(user, client)
scope_clients_for_user(user, queryset)
can_access_ticket_queue(user, queue)
scope_ticket_queues_for_user(user, queryset)
```

New resource domains should expose equivalent scoped services/querysets rather
than rely on frontend filtering.

---

## 6. Queryset, detail and selector scoping

Collection APIs scope before serialisation.

Detail endpoints should query an already-scoped queryset/service so an
inaccessible object normally behaves as unavailable/not found where that avoids
leaking existence.

The same rule applies to:

- list and focus endpoints;
- detail pages and record drawers;
- Client/Project/Ticket/Infrastructure contextual panels;
- autocomplete/relationship selectors;
- Credential resource-link choices;
- search;
- Dashboard widgets;
- Calendar feeds;
- Time reports;
- exports;
- user-triggered Celery operations;
- future portal endpoints.

A composite endpoint must not fetch globally and then assume its frontend will
remove denied records.

---

## 7. Client/Internal-owned resources

Projects, Tasks, Time, Knowledge, Credentials and Infrastructure support or are
designed around explicit Client/Internal ownership.

For a Client-owned record, a normal staff user needs:

```text
required domain capability
+ access to the owning Client
+ operation-specific validation
```

Internal records have their own staff-only policy and do not use a fake Client.

Knowledge Base folder/article collections require one selected Internal or
Client context. The server restricts folders and link options to that owner
after applying Client scope; selecting a context cannot widen access. The
context picker exposes accessible Client metadata only. Resource-context KB
requests require independent Infrastructure visibility and resolve the owning
Client/Internal context. Parent folders and document folders must share the
exact owner; normal edits cannot transfer ownership. Directory browsing and
subtree search apply those same boundaries, including section-ID validation
before querying descendants.

Cross-domain references must validate ownership consistency. For example, a
Client A Task cannot silently move into Client B Project context, and a Client A
Credential cannot link to Client B or Internal Infrastructure.

Internal Credentials may link to Internal or Client Infrastructure where that
represents shared ADB operational access. This does not make the Internal
Credential Client-visible.

---

## 8. Ticket access

A normal Ticket operation conceptually requires:

```text
active authenticated staff user
+ required Ticket capability
+ permitted Ticket Queue
+ permitted Client where a Client is attached
+ operation-specific checks
```

Unknown/prospect/vendor/global Tickets can rely on Queue scope even without a
Client.

Assignment must validate that the target assignee can access the relevant
Ticket context.

The main My/Unassigned/All Active/Queue focus API applies the same access policy
as generic Ticket collections. Waiting on Customer being visually quieter does
not alter permissions.

The per-user default Queue preference narrows normal focus only; it cannot
expand Queue scope.

---

## 9. Infrastructure access

`InfrastructureResource` follows capability + ownership scope.

Authorised staff can access Internal resources according to Infrastructure
capability. Client-owned resources additionally require access to the owning
Client.

This policy applies to:

- global and Client resource collections;
- detail/drawer workspaces;
- relationship target options;
- relationship create/delete;
- specialist projections;
- Monitoring/KB/Credential contextual panels.

Resource creation uses the common add capability and each typed specialist's
add capability. Provider Accounts additionally require vendor catalogue view;
creating Service Providers uses its separate model add permission. General
inventory create/update routes accept only types without typed profiles, so they
cannot bypass specialist capability checks. Tags are shared catalogue entries;
assignments require resource change/view, tag view and normal resource scope.
See `INFRASTRUCTURE_CREATION.md` for the creation map and API contracts.

Infrastructure has one resource identity; obsolete inventory-model and
reconciliation capabilities are removed alongside the old models.

Resource relationships must not bridge two different Client owners directly.
Internal ADB resources may legitimately relate to Client resources without
making the Internal resource Client-visible in a future portal.

Seeing a resource does not imply permission to reveal linked Credential
secrets. Resource workspaces ask the Credential domain for already-scoped
metadata and secret actions remain separately authorised.

---

## 10. Credential permissions and secret boundary

Credentials are a stronger security boundary than ordinary infrastructure
metadata. The full contract is defined in
`CREDENTIAL_VAULT_ARCHITECTURE.md`.

The implemented action separation is:

- view metadata;
- create;
- change metadata and explicitly supplied secret values;
- archive lifecycle action through the delete capability;
- reveal the credential secret payload;
- copy one requested secret field;
- download one requested secret field/file;
- reconcile legacy plaintext values into the encrypted payload.

Rules:

- ordinary list/detail/search responses never return secret values;
- Client-owned credential metadata requires Client scope;
- Client Credentials may link only to resources owned by that Client;
- Internal Credentials may link to Internal or Client resources;
- secret actions require their additional secret-action capability;
- Infrastructure link targets are themselves scoped before ownership
  validation;
- service/integration decryption is a separate backend service path and is not
  equivalent to giving a human reveal permission;
- reveal/copy/download use POST so normal CSRF protections apply;
- revealed frontend values are ephemeral component state and are not persisted
  to localStorage, sessionStorage, cookies, routes, analytics or normal caches;
- secret values never enter AuditEvent metadata, logs, URLs or analytics;
- missing/wrong encryption configuration fails closed rather than falling back
  to plaintext.

A role may intentionally be allowed to view credential metadata without being
allowed to reveal/copy/download secrets.

---

## 11. Time, work-management and Calendar access

### Tasks and Projects

My Tasks means **viewable Tasks assigned to the current user**, not all
assignments pulled globally and filtered in React.

Project List/Board/Timeline, Task List views, dependency selectors and quick
capture must preserve Client/Internal/Project ownership validation.

### Time

Recording Time is distinct from viewing/reporting Time where the permission
model requires it. A user-triggered timer may only attach to contexts the user
is authorised to use.

The server is authoritative for active timer state.

### Calendar

Calendar is a composite view over already-authorised work. It never receives a
special broad Calendar permission that bypasses Task/Project scope unless an
explicit future architecture deliberately introduces such a capability.

---

## 12. Users & Access administration

The backend access model exists; the custom Users & Access operational
experience remains to be completed.

Only identities with explicit access-administration capability may change
another staff user's permissions or scope.

The workspace must support:

- staff list/detail;
- create/invite/activate/deactivate according to identity policy;
- Group membership;
- capability permissions;
- Client scope;
- Ticket Queue scope;
- Credential metadata/reveal/copy/download capability visibility;
- clear effective-access display;
- audit events for access changes;
- allowed and denied path tests.

Routine administration must not require granting the operator superuser.

---

## 13. Dashboard, Search and Client Command Centre

Composite operational surfaces independently scope each domain.

Examples:

- a Ticket Queue widget uses Ticket/Queue/Client policy;
- My Tasks uses Task policy;
- Monitoring incidents use Infrastructure/Monitoring policy;
- Client Command Centre sections independently scope Projects, Tasks, Tickets,
  Time, Infrastructure, Credentials and Knowledge;
- global search asks each participating domain for already-authorised results;
- credential search indexes/returns metadata only;
- Client/Infrastructure credential embeds default to Active and do not reveal
  secrets automatically.

A Client page referencing a record does not make that record visible to a user
who lacks its domain capability.

Dashboard/search/activity must never surface decrypted Credential values.

---

## 14. Audit requirements

Audit materially privileged/security-sensitive operations, including:

- credential reveal;
- credential field copy;
- credential field download;
- credential legacy-secret reconciliation;
- staff Group/capability changes;
- Client/Ticket Queue scope changes;
- account/security changes where appropriate;
- future privileged portal/commercial actions where justified.

Credential secret events record safe field names/context only. Audit metadata
must never copy the secret itself.

Audit metadata should answer who/what/when/context without copying sensitive
payload content.

---

## 15. API failure behaviour

Use normal Django Ninja/API contracts consistently:

- unauthenticated -> established authentication failure;
- missing capability -> established forbidden response;
- inaccessible scoped object -> normally unavailable/not found where useful to
  avoid existence leakage;
- invalid cross-owner relationship -> explicit validation failure;
- missing secret-action capability -> forbidden;
- missing/invalid credential encryption key ring -> fail closed;
- missing secret field -> explicit not-found response;
- never return denied/secret data and rely on UI masking.

---

## 16. Required permission-boundary testing

For restricted domains, cover the relevant combinations of:

- superuser;
- staff with capability + global scope;
- staff with capability + selected correct scope;
- staff with capability + wrong Client/Queue;
- staff with scope but missing capability;
- staff with no required access profile;
- non-staff identity where Internal staff-only data is involved;
- unauthenticated identity;
- Credential metadata versus reveal/copy/download separation;
- Credential/resource cross-Client link rejection;
- selectors/related-object/drawer/search/composite endpoints;
- access administration allowed/denied paths.

Do not weaken lint/type/tests to make access work pass.

---

## 17. Future Client portal

Portal identities should use the existing authentication subsystem and link to
ClientContact.

Portal visibility must be explicit and narrower than staff access. Client
ownership alone must never automatically expose:

- Internal Infrastructure;
- Credential metadata unless explicitly designed;
- credential secret values or secret actions;
- private Knowledge documents;
- Ticket internal Notes;
- staff-only Activity/Audit/Security data.

Portal visibility rules belong to the later portal phase rather than being
implied now.

---

## 18. Prohibited shortcuts

Do not:

- authorise only in React;
- give all staff superuser because ADB is currently small;
- create a competing generic role/ACL engine without a concrete need;
- treat Brand as Client scope;
- treat Client or Infrastructure access as Credential reveal permission;
- let Ticket default Queue preferences grant Queue access;
- load all records then remove denied ones client-side;
- allow Dashboard/Search/Calendar/drawers to bypass normal policies;
- expose Internal data through an Internal-to-Client Infrastructure relation;
- put secrets into audit metadata;
- return secrets in normal Credential detail/list endpoints;
- persist revealed secrets in browser storage/routes/caches;
- make future portal visibility implicit.

### Infrastructure catalogue and nested edits

Service Provider updates require `view_serviceprovider` and
`change_serviceprovider`; tag metadata updates require `view_infrastructuretag`
and `change_infrastructuretag`. Both catalogues are shared across resource
ownership contexts. A shared tag edit affects all resources using that tag.
Resource-scoped assignment is independently permissioned.

Repository-link and TLS Domain coverage updates require resource view, the
parent/linked-profile view capabilities, link view and the link's `change_*`
capability. Existing and replacement linked resources must be visible and model
ownership validation still applies. Outgoing relationship editing requires
resource view and `change_resourcerelationship`, visible source/old target/new
target, and normal relationship validation. These updates append scoped audit
events. Deactivating a Service Provider never deletes its Provider Accounts.

### Lead catalogue configuration

Lead sources and sales stages are shared platform configuration. Staff need
`crm.add_leadsource` or `crm.add_leadstatus` respectively to add dropdown options
from the lead create/edit form. `crm.add_lead` and `crm.change_lead` do not imply
these catalogue capabilities. Both write APIs enforce the corresponding Django
permission. Sales-stage outcomes are explicitly Open/Won/Lost.

Direct Lead sales-stage updates require `crm.change_lead`. Lead conversion keeps
its existing `crm.convert_lead`, Client creation and Contact creation capability
checks; setting the Won outcome is an intrinsic part of that atomic operation
and does not require a separate general Lead edit permission.

## GitHub capabilities and scope

GitHub dashboard reads require `github_integration.view_repository` and
`infrastructure.view_infrastructureresource`, with native repository resource
Client/Internal scopes. Installation management uses `manage_github` and Client
scope; approval also requires native resource/repository creation capabilities.
`trigger_workflow` and `view_workflow_logs` are independent sensitive capabilities.
Workflow inputs and log bodies never enter audit metadata. Log retrieval checks
job membership of a visible run. GitHub App private keys are injected by
Infisical as `GITHUB_APP_PRIVATE_KEY` into backend process environments, never
stored in application records or exposed through APIs. Dashboard access grants
no access to signing material. A personal GitHub username preference only filters data.
See `GITHUB_APP_SETUP.md`.

## Live update hints

The `/api/admin/events` SSE endpoint requires an active staff session and an
approved origin. Each event is checked against fresh user capabilities and
Client/Ticket Queue scopes before delivery. Personal notifications and access
hints target the owning user; group permission changes send only an instruction
to refresh the recipient’s own access. Events contain topics only. Session
revocation and password changes terminate streams. Read APIs still enforce their
full permissions; stream subscription grants no extra access. See
[the live updates architecture](LIVE_UPDATES_ARCHITECTURE.md).

## Microsoft Graph configuration authority

The platform Graph connection now uses Infisical-injected environment values for
tenant/client IDs, certificate, private key and optional passphrase. None of
those values are copied into application records or the credential Vault.
An `environment_certificate` connection stores only routing identity/status;
it is discovered automatically from runtime configuration, without a bootstrap
command. Runtime token acquisition
reads environment values directly. Existing certificate/client-secret Vault
connections remain supported, but new platform setup uses Infisical. Graph secrets
must be scoped to backend/worker runtime identities, never frontend build contexts.

## Celery platform administration

The native `/admin/celery` dashboard and every API/control endpoint require an
active staff Django superuser. Ordinary staff, Administrator group membership,
and direct model permissions do not grant this platform-wide operational access.
Celery SSE hints are also restricted to current superusers. Task payloads/results
and exception messages are excluded. Dispatch/revoke controls are audited and
never expose arbitrary task invocation or worker termination. See
[Celery operations](CELERY_DASHBOARD.md).

## Per-task Celery diagnostics

The full-administrator Celery dashboard now includes a per-task log viewer.
`CeleryTaskLog` stores redacted messages/severity/logger/attempt/timestamp linked
to an execution. Workers capture task-context Python logging, redirected stdout/
stderr, lifecycle and failure tracebacks without local-variable dumps. Known
secrets and credential-shaped fields are scrubbed before persistence; task
argument/result dumps and SQL logs are excluded. Capture is bounded (2,000 rows
per execution, 8,000 characters per message) and retained for 14 days. The API
rechecks active staff superuser access; SSE transports only refresh hints. Existing
execution summary fields remain metadata-only. See
[Celery operations](CELERY_DASHBOARD.md) for scope and capture limits.

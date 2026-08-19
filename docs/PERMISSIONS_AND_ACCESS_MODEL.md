# Permissions and Access Model

## Purpose

This document defines the current authorisation architecture for the ADB Business Platform. It is canonical and should be read with `PLATFORM_MASTER_PLAN.md` and `CURRENT_STATE_AND_FOUNDATION_CHECKLIST.md`.

The platform contains sensitive Client, operational, infrastructure, communication and credential data. Access is therefore enforced by Django and consists of two separate questions:

1. **Capability** — may this user perform this type of action?
2. **Scope** — which Clients, Ticket Queues or owned resources may that capability act on?

Frontend visibility improves usability but is never an authorisation boundary.

## 1. Core principles

1. **Django is authoritative.** Every protected API query and mutation enforces permission server-side.
2. **Capability and object scope are separate.** `tickets.view_ticket` does not mean every Ticket is visible.
3. **Django Groups are role bundles, not a replacement for permissions.**
4. **Least privilege is the default.** A normal staff user should not need superuser access.
5. **Superusers bypass ordinary scope checks deliberately.** Sensitive actions should still be audited where applicable.
6. **Sensitive operations have dedicated permissions.** Credential metadata access is distinct from secret reveal/copy.
7. **Denied objects must not enter API responses.** Scope at queryset/service level rather than filtering only in React.
8. **Indirect access paths obey the same scope.** Search, selectors, related-object panels, exports and contextual workspaces must not widen access.
9. **Permission/scope changes are auditable.**
10. **Client context enriches navigation; it never widens access.**

## 2. Identity model

The custom Django `User` model remains the platform identity type.

Current internal operations primarily use staff users. Future Client portal identities should continue through the same authentication system and link to ClientContact rather than introducing a second authentication authority.

Django `is_active`, `is_staff`, `is_superuser`, Groups and Permissions remain the platform primitives. The custom operations UI should provide a usable Users & Access workspace over these concepts rather than making normal administration depend on Django admin.

## 3. Capability permissions

Use Django's permission framework as the capability layer.

Standard model permissions (`view`, `add`, `change`, `delete`) are preferred when they express the operation correctly. Domain-specific/sensitive operations use explicit custom permissions.

Examples currently used or established by the architecture include:

```text
clients.view_client
clients.add_client
clients.change_client
clients.view_clientcontact

crm.view_lead
crm.change_lead

ticketing.view_ticket
ticketing.reply_ticket
ticketing.assign_ticket
ticketing.close_ticket
ticketing.change_ticketqueue

credentials.view_storedcredential
credentials.add_storedcredential
credentials.change_storedcredential
credentials.reveal_storedcredential
credentials.copy_secret

access_control.manage_staff_access

core.view_auditevent
```

Exact model-generated codenames should follow Django's app/model naming. New custom operations must use narrow descriptive permissions rather than broad flags such as `can_manage_everything`.

## 4. Roles / Groups

Django Groups are the role mechanism. `CustomGroup`, where used by the authentication/admin layer, remains a proxy/convenience over Django Group rather than a separate role database.

Role templates may include concepts such as:

- Administrator;
- Operations;
- Support;
- Accounts;
- Read Only.

These are convenience bundles only. Effective access is still the resulting Django permissions plus object scope.

The future Users & Access UI should allow authorised administrators to manage Groups and effective capabilities without requiring direct Django-admin use for routine changes.

## 5. Implemented staff scope model

Object scope is implemented in `apps.access_control`.

### 5.1 StaffAccessProfile

Each scoped staff user can have a `StaffAccessProfile` containing:

- `all_clients` — the user may operate across every Client, provided the required capability permission also exists;
- `all_ticket_queues` — the user may operate across every Ticket Queue, again only with the required capability.

A non-superuser without an access profile does not implicitly receive broad object access.

### 5.2 ClientAccessGrant

When `all_clients` is false, `ClientAccessGrant` rows grant access to selected Clients.

This scope applies transitively to Client-owned operational resources according to each domain's policy. An endpoint must not expose another Client's resource merely because the user has the model-level `view_*` permission.

### 5.3 TicketQueueAccessGrant

When `all_ticket_queues` is false, `TicketQueueAccessGrant` rows grant access to selected Ticket Queues.

Queue scope is independent of Client scope. Ticket visibility/action policy intersects the relevant capability, queue scope and Client scope rather than assuming any one of them grants total access.

### 5.4 Reusable policy helpers

`apps.access_control.policies` provides the established primitives:

```python
get_access_profile(user)
can_access_client(user, client)
scope_clients_for_user(user, queryset)
can_access_ticket_queue(user, queue)
scope_ticket_queues_for_user(user, queryset)
```

New domains should reuse/extend the policy layer rather than implementing ad-hoc scope checks inside every view.

## 6. Queryset and object scoping

Collection endpoints should restrict their queryset before serialisation.

Preferred pattern:

```python
queryset = scope_clients_for_user(request.user, Client.objects.all())
```

Object detail endpoints should query from an already-scoped queryset or use an equivalent domain policy so inaccessible IDs do not leak existence through different response behaviour.

The same policy applies to:

- list endpoints;
- detail endpoints;
- relationship tabs/panels;
- search;
- autocomplete/selectors;
- dashboard widgets;
- Calendar feeds;
- reports/exports;
- Celery-triggered actions initiated by a user;
- future Client portal endpoints.

## 7. Ticket access

Ticketing is implemented and has its own detailed access policy/tests.

Conceptually, a non-superuser Ticket operation requires:

```text
active authenticated staff user
    + required ticket capability
    + permitted Ticket Queue
    + permitted Client when Ticket is client-owned/matched
    + any operation-specific checks
```

Unknown/prospect/vendor/global Tickets can require queue permission even when no Client is attached.

Ticket assignment also validates that the target assignee can access the relevant Ticket context rather than merely allowing assignment to any staff account.

Resolve/close/reopen operations use the explicit close capability where required; ordinary status/priority/queue changes use their established operation policy.

See `TICKETING_ARCHITECTURE.md` for the full Ticket domain.

## 8. Internal versus Client-owned resources

Knowledge Base documents, Credentials and Infrastructure records can be Client-owned or Internal.

A capability to view one of these resource types does not imply access to all Client-owned records. Domain services must combine:

- capability permission;
- ownership type;
- Client scope when client-owned;
- any additional sensitive-operation permission.

Internal resources must have an explicit policy. Do not represent Internal ADB data through a fake Client record.

## 9. Credential permissions

Credentials are a separate security boundary.

The model/service architecture distinguishes at least:

- view credential metadata;
- create credential;
- change metadata/secret;
- delete/archive according to lifecycle policy;
- reveal secret;
- copy secret.

List/search APIs must never include secret material.

`StoredCredential.encrypted_secret_payload` is the encrypted-at-rest secret store. New production secret values must not be placed in the legacy plaintext credential fields.

User-triggered secret reveal/copy goes through the credential secret service, validates the corresponding permission and records an audit event containing field names/context but never secret values.

Integration workers may decrypt service credentials through the explicit service-level path when required for their configured operation; that is not equivalent to granting a human user reveal permission.

## 10. Audit requirements

Audit events should cover security-sensitive or materially privileged operations, including:

- credential reveal/copy;
- staff permission/Group changes;
- Client/Ticket Queue scope changes;
- account/security changes where appropriate;
- other sensitive operational actions introduced by future domains.

Audit metadata must be curated. Do not record passwords, tokens, private keys, API keys, message attachment bodies or other secrets merely because they were part of an operation.

## 11. Frontend effective access

The operations frontend should use backend-provided effective permission/scope data to drive navigation, actions and selectors.

This is an optimisation and UX contract only. A stale/tampered frontend cannot grant access because every API operation must independently enforce capability and scope.

As the Users & Access workspace is completed, it should expose effective access in human-readable form, including:

- Groups/role bundles;
- direct/effective permissions;
- all/selected Client scope;
- all/selected Ticket Queue scope;
- active/staff/superuser state where authorised to view it.

## 12. Users & Access administration

The operations navigation already reserves a Users & Access area, but its custom route/workspace still needs completion.

Only users with explicit staff-access/permission administration capabilities may change another user's permissions or scope.

The implementation must support:

- staff list/detail;
- activate/deactivate/invite/create according to the identity workflow;
- Group membership;
- capability permissions;
- `StaffAccessProfile` flags;
- `ClientAccessGrant` management;
- `TicketQueueAccessGrant` management;
- clear effective-access display;
- audit events for changes;
- tests for allowed and denied administration paths.

Routine administration should not require giving the operator Django superuser access.

## 13. Dashboard, Calendar and cross-domain views

A composite surface never receives broader access merely because it combines multiple domains.

For example:

- a Ticket Queue dashboard widget uses the same Ticket/Queue scope as the Ticket list;
- My Tasks only contains Tasks the user can view;
- Calendar entries are derived from already-authorised Task/Project/Event data;
- Client workspace sections independently scope Tickets, Projects, Tasks, Time, KB, Credentials and Infrastructure;
- search results independently enforce the relevant domain permission and Client/Internal scope.

Prefer shared scoped query/services over duplicating filters in each composite endpoint.

## 14. API failure behaviour

Use normal Django Ninja/API error contracts consistently.

Guidelines:

- unauthenticated requests should fail according to the established authentication contract;
- authenticated users lacking a capability should receive the established forbidden response;
- inaccessible object IDs should generally behave like unavailable/not-found records where that avoids leaking existence;
- never return a secret and then rely on frontend masking;
- never include a denied object in a list and rely on the client to remove it.

## 15. Tests required for restricted domains

Every protected domain should include tests for both positive and negative paths.

At minimum cover:

- superuser access;
- staff with capability + global scope;
- staff with capability + selected scope;
- staff with capability but wrong Client/Queue;
- staff with scope but missing capability;
- staff with no access profile where scope is required;
- unauthenticated users;
- sensitive credential reveal/copy separation;
- related-object/context/search endpoints;
- permission administration where implemented.

Repository lint/type/test rules must not be weakened to make authorisation work pass.

## 16. Future Client portal

Future Client portal users should use the existing identity subsystem and be linked to ClientContact.

Portal access must be explicit and narrower than internal staff access. Client ownership alone must never make internal KB, Credentials, Infrastructure, Ticket notes or other sensitive records portal-visible.

Portal visibility should be a deliberate per-domain state/policy added when the portal phase is designed.

## 17. Non-goals / prohibited shortcuts

Do not:

- authorise only in React;
- grant all staff superuser because the team is currently small;
- create a parallel custom role engine when Django permissions/Groups suffice;
- treat Brand as an access scope substitute for Client ownership;
- treat Client access as automatically granting credential reveal;
- load all records and filter denied ones only after serialisation;
- allow search/dashboard/calendar endpoints to bypass normal policies;
- include secrets in audit metadata;
- make future portal visibility implicit.

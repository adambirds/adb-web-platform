# Permissions and Access Model

## Purpose

This document defines the authorisation model for the ADB Business Platform. It is part of the canonical platform architecture and must be read with `PLATFORM_MASTER_PLAN.md`.

The platform will contain sensitive client, operational, infrastructure, financial and credential data. Access must therefore be enforced by the Django backend and must support both broad roles and fine-grained scope restrictions.

The frontend may hide or disable unavailable functionality for usability, but frontend visibility is never an authorisation boundary.

## 1. Core principles

1. **Django is authoritative.** Every protected API query and mutation must enforce permissions server-side.
2. **Roles are convenience bundles, not the whole model.** Staff may need exceptions from a role.
3. **Capability and scope are separate questions.** A user may be allowed to view tickets but only for selected queues or clients.
4. **Superusers bypass normal restrictions.** This should remain explicit and auditable.
5. **Least privilege is the default.** New staff should receive only the access needed for their work.
6. **Sensitive actions are distinct permissions.** Seeing that a credential exists is different from revealing its secret.
7. **Denied data must not enter a response.** Filtering only in the frontend is prohibited.
8. **Permission changes and sensitive actions are auditable.**

## 2. Identity categories

The existing custom Django `User` model remains the single identity type.

Initially the platform primarily serves internal staff. Later, client contacts may be granted portal access using the same identity/authentication subsystem rather than a second authentication system.

A future user classification/profile may distinguish:

- internal staff;
- client portal users;
- service/system identities where genuinely required.

This classification does not replace Django permissions.

## 3. Capability permissions

Use Django's built-in permission framework as the primitive capability layer. Standard model permissions (`view`, `add`, `change`, `delete`) should be used where they express the action correctly. Add explicit custom permissions for sensitive or domain-specific actions.

Examples include:

```text
clients.view_client
clients.add_client
clients.change_client
clients.view_clientcontact

crm.view_lead
crm.change_lead
crm.convert_lead

tasks.view_task
tasks.change_task
tasks.assign_task

tickets.view_ticket
tickets.reply_ticket
tickets.assign_ticket
tickets.merge_ticket

credentials.view_storedcredential
credentials.reveal_storedcredential
credentials.copy_secret
credentials.change_storedcredential

core.view_auditevent
core.view_sensitive_audit_metadata

authentication.manage_staff_permissions
```

Exact codenames should be defined alongside each domain implementation. Avoid generic permissions such as `can_manage_everything`.

## 4. Roles

Django Groups should be used as role bundles. `CustomGroup` is currently a proxy around Django Group and should not become a second independent role database.

Suggested initial role templates are:

- Administrator;
- Operations;
- Support;
- Accounts;
- Read Only.

These are defaults, not hard-coded behavioural roles. A staff member may receive direct permission grants/revocations where required.

The admin UI should eventually present roles as convenient starting points while exposing advanced capability customisation.

## 5. Scope restrictions

Possessing a capability does not necessarily grant access to every object.

### Client scope

Staff access must support:

- all clients;
- selected clients;
- internal-only resources where applicable.

A future `ClientAccessGrant` (or equivalent domain model) should record explicit selected-client access when a user does not have global client scope.

The exact implementation should optimise for clear query scoping rather than an overly generic content-type ACL system.

### Ticket queue scope

When ticketing is implemented, access must support:

- all queues;
- selected queues;
- assignment restrictions where useful.

Queue access is independent of client access. A user may be permitted to work in a Support queue while only being allowed to see certain clients, or may be given an Accounts queue without Support access.

### Internal versus client resources

Operational resources such as credentials, knowledge-base documents and infrastructure records are either client-owned or internal. Permission policy must consider both capability and ownership scope.

A user with client-limited access must not obtain other clients' data through related-object APIs, search, exports, autocomplete endpoints or indirect URLs.

## 6. Credential permissions

Credentials are treated as a special security boundary.

At minimum distinguish:

- view credential metadata;
- create credential;
- change credential metadata/secret;
- delete credential;
- reveal secret;
- copy/export secret where separately useful.

List/search endpoints must never return secret material.

A user may have permission to see that a credential exists without having permission to reveal its password, API key, private key or other secret.

Every secret reveal must create an audit event recording, at minimum:

- actor;
- credential target identifier/label;
- action;
- timestamp;
- source IP where available;
- session/user-agent context where available.

The audit event itself must never contain the revealed secret.

## 7. Effective access calculation

For any protected object, access should conceptually evaluate:

```text
Is active authenticated user?
    ↓
Is superuser?
    ├── yes → allow (still audit sensitive actions)
    └── no
         ↓
Has required capability permission?
    ├── no → deny
    └── yes
         ↓
Is object within user's permitted scope?
    ├── no → deny / exclude from queryset
    └── yes → allow
```

The implementation should provide reusable backend policy/query helpers so each API endpoint does not reinvent this logic.

## 8. Queryset scoping

Collection APIs must scope at queryset level wherever possible.

Preferred pattern:

```python
queryset = scope_clients_for_user(request.user, Client.objects.all())
```

rather than loading all rows and removing unauthorised ones after serialisation.

The same rule applies to related selectors, search endpoints, ticket context panels, global search and exports.

Object detail endpoints should query from an already scoped queryset so inaccessible object IDs normally behave like unavailable records instead of leaking existence through differing response details.

## 9. Admin bootstrap/effective-permission payload

The internal admin frontend should eventually obtain an effective-access payload as part of its current-user/bootstrap request.

Conceptually:

```json
{
  "user": {},
  "permissions": [
    "clients.view_client",
    "tickets.view_ticket"
  ],
  "scope": {
    "clients": {
      "all": false,
      "ids": [1, 5]
    },
    "ticket_queues": {
      "all": false,
      "ids": [2]
    }
  }
}
```

The exact contract may change. The frontend uses this information for navigation and interaction affordances, while the backend independently enforces every request.

## 10. Permission administration

Only explicitly authorised users may modify staff roles, permissions and scope grants.

Permission changes must be audited, including:

- actor;
- target staff user;
- old and new role/permission/scope state where practical and safe;
- timestamp;
- request context.

The permission editor should support both approachable role-based setup and advanced customisation.

## 11. Audit events

`apps.core.AuditEvent` is the initial append-only audit foundation.

Audit events should be emitted for security-sensitive actions first, then expanded to important business operations.

High-priority audited actions include:

- credential reveal;
- credential creation/change/deletion;
- staff permission changes;
- authentication security changes;
- ticket assignment/merge where useful;
- destructive client/infrastructure changes;
- future invoice/payment/contract changes.

Audit metadata must be intentionally curated. Never dump request bodies or model dictionaries into audit metadata because they may contain secrets or personal data.

## 12. Future client portal permissions

Client portal users will require a separate policy context from staff users.

A client user should be linked to a `ClientContact` and inherit access only to explicitly portal-visible resources for that client. Portal visibility must be opt-in at the resource/domain level; internal knowledge-base documents, credentials, staff notes and infrastructure detail must remain private by default.

Do not implement portal permissions by simply giving client users normal staff model permissions.

## 13. Implementation sequence

1. Keep existing Django User/Group permission primitives.
2. Add custom permissions as each domain is hardened.
3. Introduce reusable permission/policy helpers.
4. Implement Client access grants alongside the Clients API.
5. Implement TicketQueue access grants alongside ticketing.
6. Add credential reveal permissions before a secret-reveal API exists.
7. Expose effective permissions/scopes to the admin frontend.
8. Build staff permission management UI.
9. Extend the same policy system to future portal access without weakening internal boundaries.

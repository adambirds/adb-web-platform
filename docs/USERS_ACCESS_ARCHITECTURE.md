# Users & Access Architecture

## Purpose

Users & Access is the ADB Business Platform's custom staff-administration workspace over the existing Django identity, permission and object-scope model.

It does **not** introduce another RBAC engine. Django remains authoritative for identity, Groups, Permissions and superuser semantics, while `apps.access_control` remains authoritative for Client scope, Ticket Queue scope and staff operational preferences.

The workspace exists so routine access administration does not require Django superuser access or direct use of Django Admin.

This document should be read with `PLATFORM_MASTER_PLAN.md`, `PERMISSIONS_AND_ACCESS_MODEL.md`, `CREDENTIAL_VAULT_ARCHITECTURE.md` and the authentication architecture/documentation.

## Authorisation model

Effective staff access is deliberately composed from separate concerns:

```text
Django Group permissions
+ direct Django permissions
+ Client scope
+ Ticket Queue scope
+ operation-specific domain validation
```

Frontend visibility is presentation only. The Django API/service boundary validates every Users & Access read and mutation.

### Groups are capability bundles

Django Groups are the platform's reusable role/capability bundles. Examples may eventually include human-friendly names such as Operations, Support, Accounts or Read Only, but Group names are convenience rather than a second authorisation abstraction.

Assigning a Group grants the Group's Django permissions in the normal Django way.

The Users & Access workspace only treats a Group as assignable when **every** permission in that Group belongs to the platform's assignable business-capability catalogue. A Group containing even one excluded framework/identity permission is hidden from the options API and rejected if its ID is submitted directly.

This rule prevents a legacy or externally-created Group from bypassing the workspace's capability boundary.

### Direct capabilities are additive exceptions

Direct permissions are supported for deliberate exceptions that should not require a new Group. They are additive to permissions inherited from Groups.

Removing a direct permission does not remove the same effective permission if it still comes from a Group. The detail API therefore returns effective capabilities with their source, for example:

```text
Direct
Group: Operations
Superuser
```

### Assignable business-capability catalogue

The custom workspace intentionally excludes low-level Django identity/framework permission families from assignment.

Excluded application labels include:

- `admin`;
- `auth`;
- `authentication`;
- `contenttypes`;
- `sessions`.

Raw CRUD permissions for `access_control` are also excluded. The intentional staff-administration capability is:

```text
access_control.manage_staff_access
```

This keeps the custom access-management boundary understandable and avoids exposing alternate routes such as raw `auth.change_permission` or `authentication.change_user` through the normal staff workspace.

## Sensitive capabilities

Sensitive business capabilities remain individually grantable, but the workspace marks them clearly in both the capability selector and effective-access view.

Current sensitive examples include:

```text
access_control.manage_staff_access
core.view_sensitive_audit_metadata
credentials.reveal_storedcredential
credentials.copy_storedcredential_secret
credentials.download_storedcredential_secret
credentials.reconcile_legacy_credentials
ticketing.configure_graph_connections
ticketing.configure_mailboxes
```

Credential metadata access remains independent from reveal/copy/download. Users & Access never receives Credential secret payloads simply because it can administer the corresponding capabilities.

## Staff object scope

Capability answers **what** a staff member may do. Scope answers **where** they may do it.

### Client scope

`StaffAccessProfile.all_clients` grants access to every Client subject to normal domain capabilities.

When it is false, `ClientAccessGrant` rows identify the permitted Clients. Client scope then flows through the established domain policies to Client-owned Projects, Tasks, Time, Infrastructure, Credentials, Knowledge Base and other scoped resources.

Users & Access changes the central scope records; it does not duplicate downstream domain filtering.

### Ticket Queue scope

`StaffAccessProfile.all_ticket_queues` grants access to every Ticket Queue subject to Ticket capabilities.

When it is false, `TicketQueueAccessGrant` rows identify the permitted queues.

Ticket Queue scope remains independent from Client scope. A user may need both boundaries to see or act on a Client-associated Ticket.

### Default Ticket Queues are preferences

`default_ticket_queues` is a server-backed work-focus preference, not an authorisation grant.

Rules are:

- only enabled queues inside the resulting Queue access scope can be defaults;
- an explicit subset narrows normal Ticket focus views;
- selecting every enabled accessible queue normalises to an empty stored selection;
- an empty stored selection means all accessible enabled queues;
- changing defaults never widens Queue authorisation.

## Management capability

The custom workspace and its API require:

```text
access_control.manage_staff_access
```

A staff user without this capability cannot list the workspace's staff data, retrieve access-management options, invite staff, change access, change account activation state or resend invitations.

The admin navigation uses the same capability as its visibility gate.

## Self and superuser safeguards

Routine access administrators are intentionally prevented from turning the workspace into a self-escalation mechanism.

For a non-superuser actor:

- changing their own access is rejected;
- changing their own activation state is rejected through the same target validation boundary;
- changing a superuser account is rejected.

Django superusers remain the bootstrap/break-glass authority and retain Django's normal permission bypass semantics. The custom workspace is not intended to replace superuser/bootstrap controls.

A superuser may inspect/manage staff through the workspace, but Groups/direct permissions do not constrain Django's superuser permission bypass.

## Staff invitation lifecycle

The platform reuses the existing authentication password-reset token flow rather than creating temporary passwords or a second invitation identity mechanism.

### Invite

An authorised administrator supplies:

- email;
- first and last name;
- Groups;
- direct capabilities;
- Client scope;
- Ticket Queue scope;
- Queue defaults.

The backend then, atomically:

1. validates the requested access configuration;
2. creates an active staff identity with an unusable password;
3. creates a one-hour password-reset/setup token;
4. applies Groups, permissions and object scope;
5. commits the account only if the access write succeeds.

After the transaction, the platform sends the existing auth frontend password-setup URL by email.

No temporary password is generated, stored or displayed. Reset/setup token values are never returned by the Users & Access API and are never written to AuditEvent metadata.

If mail delivery fails, the account remains valid and the API reports `invitation_email_sent=false` so the administrator can recover operationally rather than losing the configured account.

### Setup pending

The admin API exposes only:

```text
setup_pending = not user.has_usable_password()
```

This is sufficient to drive the invitation-resend UX without exposing token material.

### Resend invitation

Resend is allowed only while the target still has an unusable password.

The backend rotates the setup token under a row lock, resets its one-hour lifetime and sends a fresh setup link. Once the user has a usable password, the invitation-resend endpoint refuses the action and normal password-reset/account-security flows must be used instead.

### Email verification

Password setup does not silently redefine the platform's existing `email_verified` semantics. The invitation workflow leaves the field under the existing authentication/email-verification lifecycle rather than changing generic password-reset behaviour as a side effect of Stage 7.

## Account activation lifecycle

Users & Access supports explicit activation and deactivation through Django's `is_active` flag.

Deactivation preserves Groups, direct permissions, scope and history. It prevents authentication without destroying the access configuration, allowing an account to be safely reactivated later.

Activation/deactivation uses the same protected target rules as other access mutations.

## API contract

The Stage 7 API is mounted beneath `/api/admin/access`.

### Staff register

```text
GET /api/admin/access/users
```

Supports server-side:

- search;
- `active`, `inactive` or `all` status views;
- pagination;
- active/inactive counts.

The default UI is active-first in line with the platform's current/actionable-first doctrine.

### Assignment options

```text
GET /api/admin/access/options
```

Returns only the assignable:

- Groups;
- business capabilities;
- Clients;
- Ticket Queues.

Unsafe Groups containing excluded permissions are not returned.

### Staff detail and writes

```text
POST /api/admin/access/users/invite
GET  /api/admin/access/users/{user_id}
PUT  /api/admin/access/users/{user_id}/access
POST /api/admin/access/users/{user_id}/activate
POST /api/admin/access/users/{user_id}/deactivate
POST /api/admin/access/users/{user_id}/resend-invitation
```

The detail projection includes effective permission sources and safe scope metadata. It never includes passwords, reset/setup tokens, Credential secrets or other secret payloads.

## Atomicity and concurrency

Access writes and lifecycle mutations use database transactions. Existing users are locked for access/status changes where concurrent administration could otherwise race.

Invitation account creation and access assignment share one transaction, so an invalid scope, Group or capability selection does not leave a partially configured staff account behind.

Invitation resend rotates the token under a row lock.

## Auditing

Stage 7 records meaningful access-management events through the platform's append-only `AuditEvent` foundation.

Current actions include:

```text
staff_access.invited
staff_access.invitation_resent
staff_access.updated
staff_access.activated
staff_access.deactivated
```

Access-update metadata records safe before/after configuration including Group names, direct permission codes and scope identifiers.

Audit metadata deliberately excludes:

- passwords;
- reset/setup tokens;
- Credential secret values;
- authentication secret material.

## Frontend workspace

The implemented `/admin/access` workspace includes:

- active-first staff register;
- Active/Inactive/All focus views;
- search and server-side pagination;
- invitation flow;
- staff detail/access editor;
- Group/capability-bundle selection;
- direct capability selection;
- sensitive-capability warnings;
- effective capability/source display;
- Client scope administration;
- Ticket Queue scope administration;
- default Queue preferences;
- activation/deactivation;
- setup-pending state and safe invitation resend;
- read-only presentation when the actor is not allowed to manage the target.

The UI mirrors backend rules for usability but does not replace them.

## Deliberate boundaries and deferrals

Stage 7 deliberately does not add:

- a competing role/RBAC engine;
- browser-managed JWT authorisation;
- temporary passwords;
- raw framework identity/permission CRUD in the custom workspace;
- automatic broad access for staff lacking a scope profile;
- Credential secret values in access-administration responses;
- Client portal user administration;
- a generic organisation/multi-tenant abstraction for a hypothetical future SaaS product.

Human-friendly seeded role templates can be refined later using normal Django Groups without changing this architecture.

## Security invariants

The following are mandatory:

1. Django remains the authorisation authority.
2. `manage_staff_access` is required server-side for custom staff administration.
3. Non-superuser administrators cannot modify themselves or superusers.
4. Direct assignment accepts only the explicit business-capability catalogue.
5. Group assignment accepts only Groups composed entirely of assignable capabilities.
6. Client and Queue defaults never widen object authorisation.
7. Passwords and setup/reset tokens never appear in Users & Access API responses or audit metadata.
8. Credential secret payloads never enter Users & Access responses or audit metadata.
9. Frontend hiding is never treated as the security boundary.
10. Access changes remain auditable.

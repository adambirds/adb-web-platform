# Microsoft Graph Ticketing Setup

## Purpose

This is the deployment/runbook for connecting the ADB Business Platform to
Microsoft 365 Shared Mailboxes through Microsoft Graph.

It documents the agreed ADB operating model:

```text
one Microsoft 365 tenant
+ one Microsoft Entra application
+ one certificate/private key managed in Infisical
+ one MicrosoftGraphConnection
+ many Shared Mailboxes configured in ADB
```

Adding a new Shared Mailbox to Ticketing should **not** require a new Entra
application, another certificate, another tenant/client ID entry or a new
Exchange RBAC assignment every time.

Application/message architecture lives in `TICKETING_ARCHITECTURE.md`.
Graph signing configuration is supplied by Infisical to backend/worker runtime
environments. The application Vault remains a separate credential feature.

---

## 1. Intended production architecture

```text
Microsoft 365 tenant
    |
    +-- Entra application: ADB Business Platform Ticketing
    |       |
    |       +-- RSA certificate public key registered in Entra
    |       +-- Exchange Online RBAC for Applications
    |               |
    |               +-- Application Mail.ReadWrite
    |               +-- Application Mail.Send
    |               +-- SharedMailbox dynamic resource scope
    |
    +-- Shared Mailboxes
            |
            +-- support@...
            +-- enquiries/sales@...
            +-- accounts@...
            +-- other operational addresses

ADB Business Platform
    |
    +-- Infisical runtime environment
    |       |
    |       +-- tenant/client IDs and certificate/private key
    |
    +-- one MicrosoftGraphConnection
    |       |
    |       +-- reads signing configuration from environment
    |
    +-- one Mailbox row per Shared Mailbox actually used by Ticketing
            |
            +-- Brand
            +-- purpose
            +-- default Ticket Queue
            +-- enabled state
            +-- Graph sync/delta state
```

There are two different boundaries:

1. **Exchange Online RBAC** controls which mailboxes the application is
   technically authorised to access at Microsoft.
2. **ADB Mailbox records** are the narrower operational allow-list. Celery only
   synchronises enabled Mailbox rows.

The database allow-list does not replace the Microsoft-side security boundary.
Infisical manages the application signing configuration and does not replace
either mailbox authorisation boundary.

---

## 2. Required Graph/Exchange capabilities

Ticketing needs to:

- read messages/headers;
- retrieve attachments;
- maintain delta synchronisation state;
- update mailbox state where required by the sync implementation;
- send replies/new messages from configured Shared Mailboxes.

The Exchange application roles used by this design are:

- `Application Mail.ReadWrite`;
- `Application Mail.Send`.

`Mail.ReadWrite` does not include send capability, so both are required.

Background mailbox processing is app-only. It does not depend on an
interactive/licensed staff user's delegated OAuth session.

---

## 3. Least-privilege rule: do not undo the Exchange scope

The recommended deployment uses **Exchange Online RBAC for Applications** rather
than equivalent organisation-wide Microsoft Graph Mail application permissions
on the Entra app.

Exchange RBAC assignments and Entra application grants are additive. If the
same app also receives broad Entra `Mail.ReadWrite`/`Mail.Send` application
permissions, those grants can restore access outside the Exchange resource
scope.

Therefore:

- use the scoped Exchange application roles below;
- do not add equivalent broad Entra Mail application permissions merely to make
  the app work;
- remove/audit broad Mail grants left from experiments before calling the
  deployment least-privilege.

A future non-mail Graph capability should be granted separately and narrowly.

---

## 4. Prerequisites

You need:

- Microsoft 365 with Exchange Online;
- operational addresses created as **Shared Mailboxes**;
- rights to manage the Entra app registration;
- rights to configure Exchange Online RBAC for Applications;
- ExchangeOnlineManagement PowerShell module;
- an RSA certificate/private key;
- the ADB backend migrated/running;
- Infisical runtime identities authorised to inject the Graph environment
  variables into the backend, workers;
- access to update certificate/key secrets in Infisical;
- Celery worker and Beat in production.

---

## 5. Connect to Exchange Online PowerShell

Install/import the module as appropriate for the administrator workstation:

```powershell
Install-Module -Name ExchangeOnlineManagement -Scope CurrentUser
Import-Module ExchangeOnlineManagement
Connect-ExchangeOnline
```

Inspect the installed version if troubleshooting:

```powershell
Get-InstalledModule ExchangeOnlineManagement |
    Format-List Name,Version,InstalledLocation
```

---

## 6. Create the Microsoft Entra application

In Microsoft Entra admin center:

1. Open **Entra ID -> App registrations -> New registration**.
2. Use a clear name, e.g. `ADB Business Platform Ticketing`.
3. Use **Accounts in this organizational directory only** for the normal ADB
   single-tenant deployment.
4. No interactive redirect URI is required for app-only background sync.
5. Record:
    - **Application (client) ID**;
    - **Directory (tenant) ID**.

Exchange also needs the **service principal Object ID** from Enterprise
Applications, not the App Registration application-object ID.

---

## 7. Create and register the certificate

Production should use a securely managed/rotated RSA certificate. Only the
public certificate is uploaded to Entra. The private key remains an Infisical secret.

A disposable local/test self-signed example:

```bash
mkdir -p "$HOME/.adb-secrets/graph"
chmod 700 "$HOME/.adb-secrets/graph"

openssl req \
  -x509 \
  -newkey rsa:3072 \
  -sha256 \
  -days 365 \
  -nodes \
  -keyout "$HOME/.adb-secrets/graph/adb-ticketing-graph.key.pem" \
  -out "$HOME/.adb-secrets/graph/adb-ticketing-graph.cert.pem" \
  -subj "/CN=ADB Business Platform Ticketing"

chmod 600 "$HOME/.adb-secrets/graph/adb-ticketing-graph.key.pem"
chmod 644 "$HOME/.adb-secrets/graph/adb-ticketing-graph.cert.pem"
```

Upload the public certificate under **Certificates & secrets -> Certificates**
in the Entra app registration.

Never commit/upload the private-key file to Git.

After the Vault Credential has been created and verified, remove disposable
private-key copies from ordinary working directories according to the local
secret-handling policy.

---

## 8. Get the service principal Object ID

Open **Enterprise applications**, locate the Ticketing application and copy its
**Object ID**.

Set convenient PowerShell variables:

```powershell
$AppId = "<APPLICATION-CLIENT-ID>"
$ServicePrincipalObjectId = "<ENTERPRISE-APPLICATION-OBJECT-ID>"
$DisplayName = "ADB Business Platform Ticketing"
```

Do not confuse this Object ID with the application-object ID shown elsewhere in
App registrations.

---

## 9. Register the service principal with Exchange

```powershell
New-ServicePrincipal `
  -AppId $AppId `
  -ObjectId $ServicePrincipalObjectId `
  -DisplayName $DisplayName
```

If it already exists, inspect/reuse it instead of creating a duplicate:

```powershell
Get-ServicePrincipal -Identity $ServicePrincipalObjectId |
  Format-List DisplayName,ObjectId,AppId
```

---

## 10. Create the Exchange mailbox resource scope

### ADB default — all Shared Mailboxes

The agreed normal ADB tenant design scopes the application dynamically to
Exchange recipients whose type is `SharedMailbox`:

```powershell
New-ManagementScope `
  -Name "ADB Ticketing Shared Mailboxes" `
  -RecipientRestrictionFilter "RecipientTypeDetails -eq 'SharedMailbox'"
```

Why this is the default:

- the operational addresses ADB wants to ingest are Shared Mailboxes;
- licensed `UserMailbox` identities remain outside the resource scope;
- a newly created Shared Mailbox automatically matches without changing RBAC;
- the ADB database still decides which matching Shared Mailboxes are actually
  synchronised.

This directly supports the operational requirement that adding a new Shared
Mailbox to Ticketing is an ADB configuration step, not a Microsoft RBAC project.

Verify the scope population:

```powershell
Get-Recipient `
  -Filter "RecipientTypeDetails -eq 'SharedMailbox'" |
  Format-Table DisplayName,PrimarySmtpAddress,RecipientTypeDetails
```

### Optional tighter alternative — tagged Shared Mailboxes

If the tenant later contains Shared Mailboxes that the Ticketing application
must **not even technically access**, use a dedicated Exchange custom attribute
and a narrower dynamic scope.

Example only:

```powershell
Set-Mailbox "support@example.com" `
  -CustomAttribute15 "ADBTicketing"

New-ManagementScope `
  -Name "ADB Ticketing Shared Mailboxes" `
  -RecipientRestrictionFilter "(RecipientTypeDetails -eq 'SharedMailbox') -and (CustomAttribute15 -eq 'ADBTicketing')"
```

This is stricter but reintroduces one Microsoft-side tagging action whenever a
new Ticket mailbox is added. Use it only if that tighter boundary is actually
needed.

Do not create one management scope/role assignment per mailbox.

---

## 11. Assign the Exchange application roles once

```powershell
New-ManagementRoleAssignment `
  -Name "ADB Ticketing Mail ReadWrite" `
  -App $ServicePrincipalObjectId `
  -Role "Application Mail.ReadWrite" `
  -CustomResourceScope "ADB Ticketing Shared Mailboxes"

New-ManagementRoleAssignment `
  -Name "ADB Ticketing Mail Send" `
  -App $ServicePrincipalObjectId `
  -Role "Application Mail.Send" `
  -CustomResourceScope "ADB Ticketing Shared Mailboxes"
```

Inspect the role assignments:

```powershell
Get-ManagementRoleAssignment `
  -RoleAssignee $ServicePrincipalObjectId |
  Format-Table Name,Role,RoleAssigneeName,CustomResourceScope
```

These assignments are connection/application setup. Do **not** repeat them for
every Mailbox row.

---

## 12. Test Exchange authorisation before ADB configuration

Test an intended Shared Mailbox:

```powershell
Test-ServicePrincipalAuthorization `
  -Identity $ServicePrincipalObjectId `
  -Resource "support@your-shared-mailbox.example" |
  Format-Table RoleName,GrantedPermissions,AllowedResourceScope,ScopeType,InScope
```

The required roles should report the mailbox in scope.

Also test a licensed user mailbox that should be outside the ADB Ticketing
resource boundary:

```powershell
Test-ServicePrincipalAuthorization `
  -Identity $ServicePrincipalObjectId `
  -Resource "licensed.user@yourtenant.example" |
  Format-Table RoleName,GrantedPermissions,AllowedResourceScope,ScopeType,InScope
```

The Ticketing application roles should not be in scope for that UserMailbox.

Remember that `Test-ServicePrincipalAuthorization` evaluates Exchange RBAC;
broad Entra grants are separate and must be audited independently.

Microsoft-side permission propagation can take time even after configuration is
correct.

---

## 13. Audit Entra API permissions

Open the Entra app's **API permissions** page.

For this design:

- do not add broad Graph `Mail.ReadWrite` / `Mail.Send` Application permissions;
- remove equivalent broad grants left from previous experiments after the
  Exchange RBAC configuration is verified;
- grant any unrelated Graph capabilities independently/least-privilege.

---

## 14. Infisical-managed runtime configuration

Tenant ID, application ID and certificate authentication material are managed in
Infisical and injected into the API and worker environments:

```dotenv
MICROSOFT_GRAPH_TENANT_ID=<Directory tenant UUID>
MICROSOFT_GRAPH_CLIENT_ID=<Application client UUID>
MICROSOFT_GRAPH_PRIVATE_KEY=<entire RSA PEM private key>
MICROSOFT_GRAPH_CERTIFICATE=<matching public PEM certificate>
MICROSOFT_GRAPH_PRIVATE_KEY_PASSPHRASE=<optional passphrase>
```

Actual PEM newlines and escaped `\n` are accepted. Never place these variables in
frontend build environments. Graph environment authentication does not depend on
application Vault encryption. Existing Vault-backed connections remain supported
for compatibility; the preferred platform deployment uses Infisical.

Apply migrations and deploy the backend/workers with those environment values.
The app reads them directly; no bootstrap command is required. It automatically
creates/discovers only the stable routing record, without persisting real IDs,
certificate or private key. Existing disabled state and mailbox associations are
preserved. Settings displays the connection and manages Shared Mailboxes; reload
it, add intended mailboxes with Brand/purpose/queue, verify access and enable them.
Run the general worker and one Beat scheduler. Graph uses scheduled delta sync,
not an inbound Microsoft webhook.

## 15. Rotation and verification

Upload the new public certificate to the same Entra application, update the
matching certificate/key/passphrase manually in Infisical, then redeploy API/worker processes.
Verify inbound sync and outbound send before removing the previous Entra
certificate. No application Vault copy is needed. Preserve connection routing
records and mailbox associations across deploys. Tenant/application identity
changes retain those associations, so re-verify every mailbox's authorisation
before resuming processing in the new tenant/application.

Use Exchange's tests above to confirm a SharedMailbox is in scope and a licensed
UserMailbox is out of scope. If API verification succeeds but worker sync fails,
check that both received the same Infisical variables. Confirm certificate
validity, key/certificate matching, Exchange permission propagation, and enabled
mailbox rows. Logs and audit output must not contain PEM contents or tokens.

See the [root setup guide](../README.md#setup-and-configuration) for all runtime
variables, development setup and production injection requirements.

## Application email sender

Account verification, password resets and staff invitations now use the same
Infisical-configured Graph connection through Django's
`apps.ticketing.email_backend.MicrosoftGraphEmailBackend`. Remove obsolete
`EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`,
`EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL` and `EMAIL_TIMEOUT`
secrets. The backend transport is selected in code; configure only
`DEFAULT_FROM_EMAIL=no-reply@adbsoftwaresolutions.co.uk` alongside the existing
Graph variables.

Create the sender as a Microsoft 365 Shared Mailbox. The dynamic SharedMailbox
scope above automatically includes it for the existing `Application Mail.Send`
assignment. For a custom/tagged scope, include the sender and verify the scoped
role assignment explicitly. The sender does not require a Ticketing `Mailbox`
row; add one only if you intend to ingest its incoming correspondence.

Application mail uses Graph's MIME `POST /users/{sender}/sendMail` endpoint and
retains plain/HTML alternatives, recipient types, Reply-To and attachments.
Acceptance is a 202 response, not a final delivery receipt. No automatic send
retry is attempted after an ambiguous network failure, avoiding duplicate account
messages. Account mail bodies and tokens are not copied into Tickets or audits.
Local development uses Graph too; no console/SMTP fallback is selected silently.
See [Microsoft's sendMail reference](https://learn.microsoft.com/en-us/graph/api/user-sendmail?view=graph-rest-1.0).

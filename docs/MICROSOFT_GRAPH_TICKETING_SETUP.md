# Microsoft Graph Ticketing Setup

## Purpose

This is the deployment/setup runbook for connecting the ADB Business Platform ticketing system to Microsoft 365 Shared Mailboxes through Microsoft Graph.

It covers:

- the Microsoft Entra application;
- certificate-based app-only authentication;
- Exchange Online RBAC for Applications;
- restricting the application to ADB ticketing Shared Mailboxes;
- storing the certificate/private key in the platform credential vault;
- creating the database Graph connection;
- adding Shared Mailboxes in `/admin/settings`;
- Celery sync requirements;
- testing, troubleshooting and certificate rotation.

The detailed application-side message/threading design lives in `docs/TICKETING_ARCHITECTURE.md`.

## 1. Intended production architecture

The normal ADB configuration is:

```text
Microsoft 365 tenant
    |
    +-- one Microsoft Entra application
    |       |
    |       +-- certificate credential
    |       +-- Exchange Online RBAC for Applications
    |               |
    |               +-- Application Mail.ReadWrite
    |               +-- Application Mail.Send
    |               +-- scoped only to intended Shared Mailboxes
    |
    +-- Shared Mailboxes
            |
            +-- support@...
            +-- sales/contact@...
            +-- accounts@...
            +-- other operational addresses

ADB Business Platform
    |
    +-- one MicrosoftGraphConnection for that tenant/app
    |       |
    |       +-- one encrypted internal StoredCredential
    |
    +-- one Mailbox row per Shared Mailbox actually used by ticketing
            |
            +-- Brand
            +-- purpose
            +-- default Ticket Queue
            +-- Graph delta cursor/sync state
```

There are therefore **two allow-lists**:

1. **Exchange Online RBAC** is the external Microsoft-side security boundary that determines which mailboxes the application is technically authorised to access.
2. **ADB `Mailbox` rows** are the application-level operational allow-list. Celery only synchronises enabled Mailbox records configured in the database.

The database allow-list does not replace Exchange security scoping.

## 2. Required ADB Graph capabilities

The ticketing implementation needs to:

- read/create/update email state required by mailbox synchronisation;
- retrieve messages and file attachments;
- maintain delta sync state;
- send replies/new ticketing messages from configured Shared Mailboxes.

The Exchange application roles used by this design are:

- `Application Mail.ReadWrite` — Graph `Mail.ReadWrite` capability;
- `Application Mail.Send` — Graph `Mail.Send` capability.

`Mail.ReadWrite` does **not** include sending mail, which is why both roles are required.

The application does not use delegated user OAuth for background mailbox sync. The backend explicitly supports app-only certificate/client-secret methods and rejects delegated authentication for background sync.

## 3. Important least-privilege rule

The recommended design uses **Exchange Online RBAC for Applications** instead of granting equivalent organisation-wide Microsoft Graph Mail application permissions in the Entra app registration.

Exchange RBAC assignments and Microsoft Entra application permissions are independent/additive. If you grant an unscoped Entra `Mail.ReadWrite`/`Mail.Send` application permission as well as a scoped Exchange RBAC assignment, the broad Entra grant can restore access outside the Exchange scope.

Therefore:

- use the scoped Exchange application roles described below;
- do **not** also add equivalent unscoped Microsoft Graph Mail application permissions unless you intentionally want broader organisation-wide access;
- audit/remove old broad mail application grants if this app registration was previously configured another way.

## 4. Prerequisites

You need:

- a Microsoft 365 tenant with Exchange Online;
- the operational addresses created as **Shared Mailboxes**;
- permission to create/manage an Entra app registration;
- Exchange Online permissions sufficient to configure RBAC for Applications. Microsoft documents Organization Management / Exchange Administrator-level administration for this setup;
- PowerShell with the Exchange Online Management module;
- a production certificate, or a self-signed certificate for local/test bootstrap;
- the ADB backend migrated and running;
- `CREDENTIAL_ENCRYPTION_KEYS` configured before storing Graph secret material;
- Celery worker and Celery Beat running for production mailbox sync.

## 5. Install/connect Exchange Online PowerShell

Install the current public Exchange Online Management module for your user:

```powershell
Install-Module -Name ExchangeOnlineManagement -Scope CurrentUser
```

Then import/connect:

```powershell
Import-Module ExchangeOnlineManagement
Connect-ExchangeOnline
```

Use an account with sufficient Exchange administration permissions.

You can inspect the installed version with:

```powershell
Get-InstalledModule ExchangeOnlineManagement |
    Format-List Name,Version,InstalledLocation
```

## 6. Create the Microsoft Entra application

In the Microsoft Entra admin center:

1. Go to **Entra ID -> App registrations -> New registration**.
2. Give it a clear name, for example:

    ```text
    ADB Business Platform Ticketing
    ```

3. Choose **Accounts in this organizational directory only** for the normal single-tenant ADB deployment.
4. No interactive redirect URI is required for this app-only background integration.
5. Create the registration.
6. From **Overview**, record:
    - **Application (client) ID** — this becomes `MicrosoftGraphConnection.client_id`;
    - **Directory (tenant) ID** — this becomes `MicrosoftGraphConnection.tenant_id`.

The app registration creates/relates to a service principal in the tenant. Exchange RBAC needs the **service principal Object ID**, not the App Registration object's Object ID.

## 7. Create/register the certificate

### 7.1 Production recommendation

Use a certificate whose private key can be securely managed/rotated. Microsoft recommends certificate credentials over client secrets for production confidential applications.

The ADB implementation requires an **RSA** private key and PEM certificate because it builds a PS256 client assertion internally.

Only the public certificate is uploaded to Microsoft Entra. The private key stays with ADB and must never be committed to Git.

### 7.2 Local/test self-signed example

For development/bootstrap only, OpenSSL can create a self-signed RSA certificate:

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

If you need DER `.cer` format for tooling:

```bash
openssl x509 \
  -in "$HOME/.adb-secrets/graph/adb-ticketing-graph.cert.pem" \
  -outform der \
  -out "$HOME/.adb-secrets/graph/adb-ticketing-graph.cert.cer"
```

### 7.3 Upload the public certificate

In the Entra app registration:

1. Open **Certificates & secrets**.
2. Open **Certificates**.
3. Choose **Upload certificate**.
4. Upload the public `.pem`, `.cer` or `.crt` certificate.
5. Record/check the displayed certificate thumbprint and expiry.

Do **not** upload or otherwise expose the private-key file.

The backend calculates the SHA-256 certificate thumbprint (`x5t#S256`) and signs a short-lived JWT client assertion with PS256 when requesting a token.

## 8. Get the correct service principal Object ID

Exchange `New-ServicePrincipal` needs:

- the Entra **Application (client) ID**; and
- the **service principal Object ID** from **Enterprise applications**.

In the Entra admin center:

1. Go to **Enterprise applications**.
2. Find `ADB Business Platform Ticketing`.
3. Copy its **Object ID**.

Do not accidentally use the Object ID shown for the App Registration application object. Microsoft explicitly distinguishes the service principal Object ID for this Exchange command.

For the commands below, set variables:

```powershell
$AppId = "<APPLICATION-CLIENT-ID>"
$ServicePrincipalObjectId = "<ENTERPRISE-APPLICATION-SERVICE-PRINCIPAL-OBJECT-ID>"
$DisplayName = "ADB Business Platform Ticketing"
```

## 9. Create the Exchange service-principal pointer

Connect to Exchange Online, then register the Entra service principal in Exchange:

```powershell
New-ServicePrincipal `
  -AppId $AppId `
  -ObjectId $ServicePrincipalObjectId `
  -DisplayName $DisplayName
```

Confirm it exists:

```powershell
Get-ServicePrincipal -Identity $ServicePrincipalObjectId |
  Format-List DisplayName,ObjectId,AppId
```

If it already exists, do not create a duplicate; inspect the existing pointer instead.

## 10. Choose the Exchange mailbox scope

### Option A — recommended: explicitly tag ticketing Shared Mailboxes

This is the tighter production option if the tenant may contain Shared Mailboxes that ADB ticketing should **not** access.

Reserve one Exchange custom attribute for this purpose. The examples below use `CustomAttribute15 = ADBTicketing`; use a different custom attribute if 15 is already used in the tenant.

Tag each ticketing mailbox:

```powershell
Set-Mailbox "support@adbsoftwaresolutions.co.uk" `
  -CustomAttribute15 "ADBTicketing"

Set-Mailbox "support@adbwebdesigns.co.uk" `
  -CustomAttribute15 "ADBTicketing"

Set-Mailbox "support@adbtechnology.co.uk" `
  -CustomAttribute15 "ADBTicketing"
```

Add sales/accounts/general Shared Mailboxes in the same way when they should participate.

Verify the filter before creating the scope:

```powershell
Get-Recipient `
  -Filter "(RecipientTypeDetails -eq 'SharedMailbox') -and (CustomAttribute15 -eq 'ADBTicketing')" |
  Format-Table DisplayName,PrimarySmtpAddress,RecipientTypeDetails,CustomAttribute15
```

Create the dynamic management scope:

```powershell
New-ManagementScope `
  -Name "ADB Ticketing Shared Mailboxes" `
  -RecipientRestrictionFilter "(RecipientTypeDetails -eq 'SharedMailbox') -and (CustomAttribute15 -eq 'ADBTicketing')"
```

New Shared Mailboxes enter the Exchange scope only after you explicitly apply the chosen custom attribute.

### Option B — simpler: all Shared Mailboxes in the tenant

If every Shared Mailbox in the tenant is intentionally a valid technical target for this application, you can scope by recipient type only:

```powershell
New-ManagementScope `
  -Name "ADB Ticketing Shared Mailboxes" `
  -RecipientRestrictionFilter "RecipientTypeDetails -eq 'SharedMailbox'"
```

This still excludes normal licensed `UserMailbox` recipients, but it is broader than Option A because every current/future Shared Mailbox matches automatically.

The ADB database Mailbox allow-list still controls what the application actually synchronises, but Option A provides a stronger Microsoft-side least-privilege boundary.

## 11. Assign Exchange application roles

Create the two scoped role assignments:

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

Inspect assignments:

```powershell
Get-ManagementRoleAssignment `
  -RoleAssignee $ServicePrincipalObjectId |
  Format-Table Name,Role,RoleAssigneeName,CustomResourceScope
```

If your installed Exchange cmdlets do not accept the exact filtering parameter used in the inspection command, query the role assignment names directly; the creation syntax above is the important part.

## 12. Test Exchange authorisation before touching ADB

Test an intended mailbox:

```powershell
Test-ServicePrincipalAuthorization `
  -Identity $ServicePrincipalObjectId `
  -Resource "support@adbsoftwaresolutions.co.uk" |
  Format-Table RoleName,GrantedPermissions,AllowedResourceScope,ScopeType,InScope
```

For both required roles you want the target mailbox to report `InScope = True`.

Also test a mailbox that should **not** be accessible, ideally a licensed user mailbox:

```powershell
Test-ServicePrincipalAuthorization `
  -Identity $ServicePrincipalObjectId `
  -Resource "someone@yourtenant.example" |
  Format-Table RoleName,GrantedPermissions,AllowedResourceScope,ScopeType,InScope
```

The scoped mail roles should not be in scope for that recipient.

`Test-ServicePrincipalAuthorization` evaluates Exchange RBAC assignments, but Microsoft notes that it does not include permissions granted separately in Microsoft Entra. That is another reason to audit/remove equivalent broad Entra Mail application grants.

Exchange permissions can take time to propagate to live API calls. Microsoft documents caching delays that can be roughly 30 minutes to 2 hours even when the test cmdlet already reports the intended RBAC result.

## 13. Audit Entra API permissions

In the Entra app registration, open **API permissions**.

For the Exchange-RBAC design in this document:

- do not add broad Microsoft Graph `Mail.ReadWrite` / `Mail.Send` Application permissions just to make the app work;
- if these broad grants were added during experimentation, remove them after the scoped Exchange RBAC configuration is in place and tested;
- remember that broad Entra grants and Exchange RBAC are additive rather than one overriding the other.

If the app later needs a non-mail Microsoft Graph capability, grant only that separate least-privilege capability intentionally.

## 14. Configure ADB credential encryption

Graph certificate/private-key material is stored through `StoredCredential.encrypted_secret_payload`. The legacy plaintext credential fields must not receive new production secrets.

Generate a Fernet key:

```bash
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

Set it in the backend/worker environment:

```env
CREDENTIAL_ENCRYPTION_KEYS=<FERNET-KEY>
```

For key rotation, the setting accepts comma-separated keys. `MultiFernet` encrypts new/rotated payloads with the **first** key, so put the newest primary key first while retaining older keys until stored records have been re-encrypted.

Every process that needs to use Graph credentials — especially Celery workers — must receive the same valid encryption-key configuration.

Do not commit the Fernet key to the repository.

## 15. Store the Graph certificate in ADB

The custom Credentials workspace does not yet provide the final secure credential-create/rotation UX, so the current bootstrap method is the Django shell plus the credential secret service.

The devcontainer mounts the host home at `/host-home`; in production, use a secure mounted secret path appropriate to the deployment.

Start a shell:

```bash
cd backend
python manage.py shell
```

Then create an **Internal** credential and store the PEM material through the encryption service:

```python
from pathlib import Path

from apps.core.ownership import OwnershipType
from apps.credentials.models import CredentialType, StoredCredential
from apps.credentials.secrets import store_credential_secrets

credential_type, _ = CredentialType.objects.get_or_create(
    name="Microsoft Graph Certificate"
)

credential = StoredCredential.objects.create(
    ownership_type=OwnershipType.INTERNAL,
    name="Microsoft Graph - ADB Ticketing",
    credential_type=credential_type,
    notes="App-only certificate for ADB ticket Shared Mailboxes.",
)

private_key = Path(
    "/host-home/.adb-secrets/graph/adb-ticketing-graph.key.pem"
).read_text()
certificate = Path(
    "/host-home/.adb-secrets/graph/adb-ticketing-graph.cert.pem"
).read_text()

store_credential_secrets(
    credential,
    {
        "private_key": private_key,
        "certificate": certificate,
    },
)

print(f"StoredCredential ID: {credential.id}")
```

If the private key is encrypted, include:

```python
{
    "private_key": private_key,
    "certificate": certificate,
    "passphrase": "<PRIVATE-KEY-PASSPHRASE>",
}
```

The secret-key names are significant. Certificate authentication requires:

- `private_key`;
- `certificate`;
- optional `passphrase`.

Do not populate the model's legacy plaintext `private_key`, `password`, `api_key` or `secret_key` fields.

## 16. Create the ADB MicrosoftGraphConnection

Until the operations UI gains a full Graph-connection create form, bootstrap the connection in the Django shell:

```python
from apps.ticketing.models import MicrosoftGraphConnection

connection = MicrosoftGraphConnection.objects.create(
    name="ADB Microsoft 365",
    tenant_id="<DIRECTORY-TENANT-ID>",
    client_id="<APPLICATION-CLIENT-ID>",
    authentication_method=MicrosoftGraphConnection.AuthenticationMethod.CERTIFICATE,
    credential=credential,
    enabled=True,
)

print(f"MicrosoftGraphConnection ID: {connection.id}")
```

The Graph connection must reference an **Internal** StoredCredential.

### Verify token acquisition without printing the token

Still in the shell:

```python
from apps.ticketing.services.graph_auth import MicrosoftGraphTokenProvider

provider = MicrosoftGraphTokenProvider(connection)
assert provider.get_access_token()
print("Graph application authentication succeeded")
```

Do not print/log the token itself.

A successful acquisition updates `last_verified_at` and clears `last_error` on the connection. Authentication failures record a safe error summary on the connection.

The token request uses:

```text
https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/token
scope = https://graph.microsoft.com/.default
grant_type = client_credentials
```

For certificate auth, ADB sends a PS256-signed private-key JWT assertion with a five-minute lifetime.

## 17. Add each Shared Mailbox in the operations UI

Once the Graph connection exists:

1. Sign in as a staff user with the required Ticketing settings permissions.
2. Open `/admin/settings`.
3. The **Microsoft 365 connection** section should show `ADB Microsoft 365`.
4. Under **Shared ticket mailboxes**, choose **Add shared mailbox**.
5. Enter:
    - Shared Mailbox email address;
    - optional display name;
    - Brand;
    - purpose: Support, Sales, Accounts, Operations or General;
    - default Ticket Queue.
6. Save.

If exactly one enabled Graph connection exists, the UI/API selects it automatically. If multiple connections exist later, the UI asks which connection owns the mailbox.

Mailbox creation performs a real Graph access check against:

```text
GET /v1.0/users/<mailbox>/mailFolders/inbox?$select=id
```

The Mailbox row is not saved unless the connection can access that mailbox.

The selected Ticket Queue must either belong to the same Brand or be a global queue.

## 18. Celery requirements

Mailbox ingestion is background work. In production both a Celery worker and Celery Beat must be running.

Beat periodically dispatches:

```text
ticketing.enqueue_graph_mailbox_syncs
```

which enqueues one sync task for each enabled Mailbox whose enabled Graph connection has a supported app-only credential.

Default sync interval:

```env
TICKETING_GRAPH_SYNC_INTERVAL_SECONDS=60
```

Minimum accepted interval is 30 seconds.

Per-mailbox distributed sync lock default:

```env
TICKETING_GRAPH_SYNC_LOCK_SECONDS=900
```

This lock prevents overlapping workers from synchronising the same mailbox concurrently.

The sync process stores Graph delta links/cursors on the Mailbox, so normal polling does not repeatedly re-import the whole mailbox. Provider/message identifiers make ingestion idempotent.

## 19. Initial functional test

After the connection/mailbox are configured and Celery is running:

1. Send a test email from a known ClientContact address to a configured support mailbox.
2. Wait for a sync dispatch.
3. Confirm a Ticket/TicketMessage appears in the expected Brand/Queue.
4. Confirm Client/Contact matching occurred if the sender exists as a ClientContact.
5. Reply from the Ticket UI.
6. Confirm the message is sent from the configured Shared Mailbox and delivery state becomes sent.
7. Reply to that email externally.
8. Confirm it threads back onto the same Ticket rather than creating an unrelated Ticket.
9. Test a message with a small attachment and confirm quarantine/download policy behaves as configured.
10. Test a Vendor sender/rule if Vendor routing is enabled.

## 20. Client-secret authentication (temporary/non-production option)

The backend supports `client_secret`, but certificate auth is the preferred production configuration.

If a client secret is temporarily required, create it in Entra **Certificates & secrets -> Client secrets**, record the value immediately, and store it in an Internal StoredCredential using this exact secret key:

```python
store_credential_secrets(
    credential,
    {"client_secret": "<SECRET-VALUE>"},
)
```

Create the connection with:

```python
authentication_method=MicrosoftGraphConnection.AuthenticationMethod.CLIENT_SECRET
```

Microsoft recommends certificates instead of client secrets for production and recommends shorter secret lifetimes if secrets are used.

## 21. Certificate rotation runbook

Rotate before expiry; do not wait for the old certificate to fail.

Recommended overlap procedure:

1. Generate/provision the replacement RSA certificate/private key.
2. Upload the new **public** certificate to the same Entra app registration while keeping the old certificate valid.
3. Verify both certificates are present during the overlap window.
4. Replace the encrypted ADB credential payload using `store_credential_secrets()` with the new `private_key` and `certificate` values.
5. Acquire a Graph token/test a mailbox.
6. Confirm normal Celery sync/replies work.
7. Remove the old public certificate from Entra only after the new credential is proven.
8. Securely destroy obsolete private-key material according to your secret-management process.
9. Update expiry/rotation documentation/monitoring.

Changing the certificate does not require recreating the Entra application, Exchange service-principal pointer, RBAC scope, Graph connection or Mailbox rows.

## 22. Fernet encryption-key rotation

`CREDENTIAL_ENCRYPTION_KEYS` supports `MultiFernet` rotation.

Safe sequence:

1. Generate a new Fernet key.
2. Configure:

    ```env
    CREDENTIAL_ENCRYPTION_KEYS=<NEW-KEY>,<OLD-KEY>,...
    ```

3. Deploy the key list to every backend/worker process.
4. Re-encrypt stored credentials using the platform rotation service/command as it becomes available; currently `rotate_credential_encryption(credential)` can rotate individual records.
5. Verify all secrets can be read with the new primary key configuration.
6. Remove old keys only after every relevant payload has been re-encrypted.

Never rotate by replacing the only configured key before existing payloads have been re-encrypted; that would make them undecryptable.

## 23. Troubleshooting

### Token request returns 401 / authentication rejected

Check:

- Tenant ID is the Directory tenant ID.
- Client ID is the Application/client ID.
- Entra app contains the public certificate matching the private key stored by ADB.
- Certificate is not expired/not-yet-valid.
- Stored secret keys are exactly `private_key` and `certificate`.
- Private key is RSA PEM.
- `passphrase` is supplied if the PEM is encrypted.
- `CREDENTIAL_ENCRYPTION_KEYS` is identical/available to the process attempting authentication.
- server clock is accurate; certificate assertions are short-lived.

The Graph connection's `last_error` records a safe summary of authentication failures.

### Token works but mailbox verification returns 403

Check:

- Exchange service-principal pointer was created with the **Enterprise Application service principal Object ID**.
- `Application Mail.ReadWrite` and `Application Mail.Send` assignments exist.
- `Test-ServicePrincipalAuthorization` reports the mailbox in scope.
- the mailbox matches the CustomAttribute/SharedMailbox scope filter.
- broad/scoped permission changes have had enough propagation time.

### Intended Shared Mailbox is out of scope

For the recommended custom-attribute scope:

```powershell
Get-Mailbox "support@example.com" |
  Format-List DisplayName,RecipientTypeDetails,CustomAttribute15
```

It should be a `SharedMailbox` and carry the expected ticketing custom attribute.

### A user mailbox unexpectedly works

This is a security warning. Check the Entra app's **API permissions** for broad Graph Mail application grants. Exchange `Test-ServicePrincipalAuthorization` only tests the Exchange RBAC assignments; an independent Entra permission can grant access outside that result.

### Mailbox verification returns 404

Check:

- mailbox address/UPN is correct;
- mailbox exists in Exchange Online;
- it is fully provisioned;
- you are adding the actual mailbox address rather than an unrelated alias if Graph resolution is ambiguous.

### Connection is shown but no mail synchronises

Check:

- Graph connection `enabled=True`;
- Mailbox `enabled=True`;
- connection references a credential;
- auth method is `certificate` or `client_secret`;
- Celery worker is running;
- Celery Beat is running;
- Redis/broker is reachable;
- Mailbox `last_error`, `last_synced_at`, `last_successful_sync_at`;
- `TICKETING_GRAPH_SYNC_INTERVAL_SECONDS` is valid (minimum 30 seconds).

You can manually dispatch a sync from a Django shell for diagnostics:

```python
from apps.ticketing.tasks import sync_graph_mailbox_task

result = sync_graph_mailbox_task(<MAILBOX-ID>)
print(result)
```

For normal operation, let Celery perform the task rather than using synchronous shell calls.

### A mailbox is accessible to Graph but should not be ingested

Disable/remove it from ADB Mailbox configuration. The application only syncs enabled database Mailbox records.

If the app should not even be technically able to access it, also remove it from the Exchange RBAC resource scope (for example by removing the chosen CustomAttribute value).

## 24. Security checklist

Before production:

- [ ] Entra application is single-tenant unless a multi-tenant requirement is explicit.
- [ ] production uses certificate authentication.
- [ ] private key is never committed to Git.
- [ ] `CREDENTIAL_ENCRYPTION_KEYS` is secret-managed outside Git.
- [ ] StoredCredential is Internal.
- [ ] Graph secret payload uses encrypted credential service, not legacy plaintext fields.
- [ ] Exchange RBAC scope contains only intended Shared Mailboxes.
- [ ] `Application Mail.ReadWrite` is scoped.
- [ ] `Application Mail.Send` is scoped.
- [ ] equivalent broad Entra Mail application grants have been removed unless explicitly required.
- [ ] an intended Shared Mailbox tests `InScope=True`.
- [ ] an unintended/user mailbox is not in the ticketing scope.
- [ ] only intended addresses have enabled ADB Mailbox rows.
- [ ] Celery worker + Beat use the same credential encryption keys as the backend.
- [ ] certificate expiry/rotation is monitored/documented.
- [ ] Ticket Queue/Client permission boundaries have been tested with non-superuser staff.

## 25. Official Microsoft references

- [Role Based Access Control for Applications in Exchange Online](https://learn.microsoft.com/en-us/exchange/permissions-exo/application-rbac)
- [Microsoft Graph permissions reference](https://learn.microsoft.com/en-us/graph/permissions-reference)
- [Microsoft identity platform certificate credentials](https://learn.microsoft.com/en-us/entra/identity-platform/certificate-credentials)
- [Add and manage application credentials in Microsoft Entra ID](https://learn.microsoft.com/en-us/entra/identity-platform/how-to-add-credentials)
- [Get access without a user / client credentials flow](https://learn.microsoft.com/en-us/graph/auth-v2-service)
- [Connect to Exchange Online PowerShell](https://learn.microsoft.com/en-us/powershell/exchange/connect-to-exchange-online-powershell)
- [Exchange Online PowerShell module](https://learn.microsoft.com/en-us/powershell/exchange/exchange-online-powershell-v2)
- [Filterable Exchange recipient properties](https://learn.microsoft.com/en-us/powershell/exchange/filter-properties)
- [Test-ServicePrincipalAuthorization](https://learn.microsoft.com/en-us/powershell/module/exchangepowershell/test-serviceprincipalauthorization)

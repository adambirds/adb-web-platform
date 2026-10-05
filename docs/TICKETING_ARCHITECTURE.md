# Ticketing Architecture

## Purpose

Ticketing is the canonical communications hub for the ADB Business Platform.
It unifies Microsoft 365 email, public website contact submissions and future
portal/API communication into the same operational thread model.

The system is not only an email archive. It is a current-first work queue with
Client/Contact/Vendor context, assignment, priority, internal notes, time
tracking, governed attachments and deterministic routing.

Microsoft Graph certificate/private-key/client-secret material is stored through
the Credential Vault. The secret-storage and human secret-action contract is
defined in `CREDENTIAL_VAULT_ARCHITECTURE.md`; Microsoft deployment details are
in `MICROSOFT_GRAPH_TICKETING_SETUP.md`.

---

## 1. Product principles

- A **Ticket** is the operational conversation/thread.
- A **TicketMessage** is one inbound or outbound customer/external message.
- A **TicketNote** is staff-only internal discussion.
- Brand, Client, Contact, Vendor, Mailbox and Queue are separate concepts.
- Known Client/Contact resolution happens before Vendor classification.
- Unknown senders are valid operational Tickets, not automatically spam.
- Microsoft Graph connection/application authentication is configured once per
  tenant/application, not once per Shared Mailbox.
- Operational mailboxes are Microsoft 365 Shared Mailboxes.
- Database Mailbox records determine which technically accessible mailboxes the
  ADB application actually synchronises.
- Graph authentication secrets live in Vault Credentials rather than duplicate
  plaintext Ticketing settings.
- Ingestion and delivery are idempotent/retry-safe where possible.
- Threading never relies on subject text alone.
- Classification/routing is deterministic and explainable first; AI is not a
  dependency for core ticketing.
- Attachments are untrusted input and pass through quarantine/policy controls.
- Capability + Queue scope + Client scope are enforced by Django.
- The default UI shows actionable work; resolved/closed history stays available
  explicitly.

---

## 2. Core models

### MicrosoftGraphConnection

Represents an application/tenant-level Graph integration.

Key concerns:

- tenant ID;
- application/client ID;
- authentication method;
- encrypted certificate/client-secret Credential reference;
- enabled/verification/error state;
- timestamps.

Certificate/private-key/client-secret material belongs in the Credential Vault,
not ordinary Graph settings responses. Backend service decryption is distinct
from human reveal/copy/download permission.

For the normal ADB tenant, one enabled Graph connection is reused by every
configured Ticketing Shared Mailbox.

### Mailbox

Represents one Shared Mailbox used operationally by Ticketing.

Key concerns:

- Graph connection;
- email address/display name;
- Brand;
- purpose;
- default Ticket Queue;
- enabled state;
- persisted Graph delta/sync state;
- success/error timestamps.

The Mailbox table is an **application allow-list**. A mailbox being reachable by
the Entra/Exchange application does not make it a Ticket source until it is
configured and enabled in ADB.

A Mailbox does not own another copy of the Graph private key/certificate.

### TicketQueue

Represents operational routing and one of the major object-scope boundaries.

Typical queues include support/sales/accounts/operations and a cross-brand
`Vendors & Services` queue where appropriate.

Queue access is scopeable independently from Client access.

### Vendor / VendorSenderRule

Vendor records represent retained third-party/service correspondence.
Sender rules are data-backed matching/routing policy.

Rules support exact address/domain matching, target Queue, optional priority,
enabled/order/notes and can be changed without a deployment.

Vendor mail remains a normal Ticket. A match routes/contextualises it; it does
not discard it as spam.

### Ticket

The current Ticket identity carries operational context such as:

- human-readable reference;
- Brand;
- Queue;
- Client/primary Contact when known;
- Vendor when matched;
- subject;
- status/priority/classification/source;
- assignment;
- lifecycle/response timestamps.

Future Project/Task/Infrastructure links may be added only where there is a real
workflow; they are not required for the Ticket identity itself.

### TicketMessage

Stores one inbound/outbound message with:

- direction;
- sender/recipient data;
- matched Contact;
- subject/body representations;
- provider and provider-message ID;
- internet Message-ID/In-Reply-To/References;
- delivery state/errors;
- external sent/received time;
- staff creator for authored messages.

Provider identifiers and internet threading headers remain critical for
idempotency and safe thread matching.

### TicketNote

Internal staff-only note attached to a Ticket.

The operations UI renders Notes **chronologically inside the conversation
feed**, visually distinct from inbound/outbound messages. Notes are not cramped
into a disconnected side panel.

### TicketAttachment

Stores governed attachment metadata such as:

- original/safe filename;
- declared/detected MIME type;
- size;
- SHA-256;
- storage/quarantine identity;
- scan status/engine/result;
- quarantine/safe/scanned timestamps.

Download policy is enforced separately from message visibility.

---

## 3. Unified ingestion pipeline

All sources feed a canonical ingestion service:

```text
Incoming payload
    -> source adapter
    -> canonical message
    -> normalise body/headers
    -> attachment quarantine/policy
    -> abuse/spam evaluation
    -> resolve Client/Contact/Vendor
    -> classify
    -> route Brand/Queue/Priority
    -> match/create Ticket thread
    -> persist Ticket/Message
    -> scan attachments when enabled
    -> downstream workflows/notifications
```

Source adapters translate provider-specific data; they do not own routing
policy.

Initial sources:

- Microsoft Graph Shared Mailboxes;
- public website contact forms.

Future-compatible sources may include:

- Client portal;
- API/webhook submission;
- monitoring/infrastructure integrations where a Ticket is the right
  operational escalation object.

---

## 4. Microsoft Graph model

The normal ADB configuration is:

```text
one Microsoft 365 tenant
    + one Entra application
    + one certificate Credential in the Vault
    + one MicrosoftGraphConnection
    + many configured Shared Mailboxes
```

### Exchange boundary

Production uses Exchange Online RBAC for Applications as the Microsoft-side
resource boundary.

For ADB's agreed current setup, the preferred management scope matches all
Shared Mailboxes dynamically:

```powershell
RecipientTypeDetails -eq 'SharedMailbox'
```

This intentionally means:

- a newly created Shared Mailbox enters the Exchange resource scope
  automatically;
- no new RBAC assignment/rule is required for each mailbox;
- licensed `UserMailbox` recipients stay outside the intended Ticketing scope;
- ADB still chooses which Shared Mailboxes to ingest through enabled database
  `Mailbox` records.

A more restrictive tagged/custom-attribute scope remains a valid alternative
if the tenant later contains Shared Mailboxes that the Ticketing application
must not be technically able to access.

Do not combine scoped Exchange permissions with equivalent broad Entra Mail
application grants in a way that restores organisation-wide access. Those
grants are additive.

### Credential boundary

The Exchange scope answers which Microsoft resources the app may access. The
Vault answers how ADB stores the app's certificate/private-key material and who
may perform human secret actions. The enabled Mailbox rows answer which Shared
Mailboxes ADB actually synchronises.

These are three separate controls and must not be conflated.

See `CREDENTIAL_VAULT_ARCHITECTURE.md` for encryption/key rotation and
`MICROSOFT_GRAPH_TICKETING_SETUP.md` for deployment.

### Adding a Shared Mailbox

The normal ADB operator flow should be application configuration, not Microsoft
application setup:

1. create the Shared Mailbox in Microsoft 365;
2. add/verify it in ADB;
3. choose Brand/purpose/default Queue;
4. enable it.

The operator should not re-enter the tenant ID, application ID, certificate or
create another Exchange role assignment for each mailbox.

If multiple Graph tenant connections are supported in active use later, the UI
may need to ask which connection owns the mailbox.

---

## 5. Graph synchronisation and outbound delivery

Graph integration supports:

- multiple configured Shared Mailboxes;
- persisted delta sync state;
- reading messages/headers;
- downloading file attachments;
- preserving internet threading headers;
- outbound replies/new messages from the configured mailbox;
- provider delivery/error state;
- retries/backoff;
- duplicate-ingestion protection;
- worker locking/idempotency.

Celery handles mailbox sync and outbound delivery. Reusable Graph/message
business logic belongs in services so it can be tested and reused outside task
functions.

The Celery/service path decrypts the linked Graph Credential server-side and
never needs a human reveal operation. Every process that performs that work must
have the appropriate `CREDENTIAL_ENCRYPTION_KEYS` key ring.

One remaining resilience refinement is the rare ambiguous-send case where
Microsoft may accept a send but the worker loses the provider response before
persisting success. This should be hardened without weakening duplicate-send
protection.

---

## 6. Thread matching

Use high-confidence signals in priority order:

1. explicit ADB Ticket reference in outbound subject/header context;
2. internet Message-ID / In-Reply-To / References;
3. reliable provider conversation identifiers;
4. conservative fallback logic only where safe.

Never merge unrelated communication based only on a similar subject.

Inbound imports and retries must remain idempotent by provider/internet
identifiers.

---

## 7. Body normalisation and rendering

Store safe original HTML/plain representations plus normalised text where
useful for display/search.

Normalisation may remove quoted reply history/signature noise conservatively,
but retaining some signature content is preferable to deleting genuine new
customer content.

HTML must be sanitised before rendering.

---

## 8. Client, Contact and Vendor resolution

Normalise sender identity and try Client/Contact matching before Vendor rules.

When a ClientContact matches:

- associate the message with that Contact;
- associate the Ticket with its Client where unambiguous;
- expose the Ticket in Client and Contact context.

Only after Client resolution fails should VendorSenderRule be evaluated.

Unknown senders remain valid Tickets and can later be associated manually if
needed.

---

## 9. Classification and routing

Spam/abuse detection and business routing are separate concerns.

Classification may include concepts such as:

- client support;
- sales;
- accounts;
- vendor;
- automated system;
- monitoring;
- newsletter/marketing;
- probable spam;
- unknown.

Routing inputs include:

- source Mailbox/default Queue;
- Brand;
- Client/Contact match;
- Vendor sender rules;
- recipient alias;
- deterministic subject/body rules;
- spam score;
- later learned classification if justified.

Routing should remain explainable enough that an operator can understand why a
Ticket landed where it did.

---

## 10. Attachment security

Attachments are untrusted even when malware scanning is disabled.

Always-on policy includes:

1. size limits;
2. safe filename/path handling;
3. SHA-256;
4. MIME/content detection;
5. controlled quarantine storage;
6. recording blocked content without exposing it;
7. permission/scope checks before download.

ClamAV is the preferred initial scanner and may run locally or centrally.

When scanning is disabled, policy-safe pending/previously failed content may be
downloadable according to the configured policy. When scanning is enabled,
only a clean/safe verdict is downloadable. Infected or policy-blocked content
is never downloadable.

Enabling scanning must cause historic pending content to become gated until it
is processed rather than implicitly trusting it.

TicketAttachment downloads and Credential secret-file downloads are different
security flows; each keeps its own permission/audit/policy checks.

---

## 11. Operational Ticket work queue

The main `/admin/tickets` page is a **work queue**, separate from generic Ticket
collection APIs used by Client/Contact/history panels.

Established top-level focus:

### Work

- **My Tickets** — default;
- **Unassigned**;
- **All Active**;
- enabled **Queue** views.

### History

- **Resolved**;
- **Closed**;
- **All Tickets**.

Waiting on Customer is intentionally lower-priority/quieter than work waiting
on ADB.

Ticket focus supports server-side sorting including operational priority,
updated time, priority, creation and subject.

Rows open the shared record drawer where appropriate while full detail routes
remain available.

### Per-user default Queues

`StaffAccessProfile.default_ticket_queues` stores the user's normal Queue focus:

- no stored selection -> all accessible enabled Queues;
- explicit subset -> use that subset in default work views;
- selecting all accessible Queues normalises back to the empty/all state.

This is a preference only and cannot expand Queue access.

---

## 12. Ticket workspace

The Ticket workspace is conversation-first and exposes operational controls
without forcing navigation to unrelated screens.

Established behaviour includes:

- status/priority/Queue/assignment actions;
- inbound/outbound message chronology;
- chronological internal Notes as visually distinct staff-only cards;
- Note composer beneath the conversation;
- customer reply controls;
- governed attachment handling;
- Client/Contact/Vendor context;
- live Time timer and contextual Time history.

As Infrastructure/KB mature, Ticket context may surface relevant technical
resources/runbooks through the same permission policies. Credentials should be
linked through those resources rather than copied into Ticket Notes/messages.

---

## 13. Lead email and CRM integration

Lead communication must stay inside the unified Ticket model.

Sending email from a Lead:

1. selects a configured Shared Mailbox available for the Lead's Brand/context;
2. creates/continues an outbound Sales Ticket conversation;
3. creates the outbound TicketMessage in queued delivery state;
4. sends through Celery/Graph;
5. appears in the Lead communication history;
6. remains part of the Ticket history if the Lead is converted to a Client.

There is no parallel `mailto:` sales-email path because that would bypass
tracking/threading/history.

Inbound Lead matching and outbound Lead email both use sender/recipient email
relationships so the conversation is retained during conversion.

---

## 14. Website contact forms

Public Brand contact forms submit to the shared backend with Brand/source
context and feed the same Lead + Ticket ingestion path.

The public capture path may have its own anti-abuse controls, but it must not
create a disconnected enquiries inbox.

Lead capture should remain resilient if downstream Ticket routing temporarily
fails according to the established ingestion contract.

Public form endpoints never expose or require access to Vault secrets.

---

## 15. Permissions

Ticket operations use capability + Ticket Queue scope + Client scope where
applicable.

Capabilities distinguish actions such as:

- view;
- create/change;
- reply;
- add internal note;
- assign;
- close/reopen;
- governed attachment download;
- configure Queues/Mailboxes/Graph;
- configure Vendor routing.

The main focus views, Queue preferences, record drawers, Client/Contact panels
and Time controls all use the same backend policy rather than bypassing it.

Graph configuration capability does not automatically grant Credential
reveal/copy/download. Those permissions remain in the Credential domain.

See `PERMISSIONS_AND_ACCESS_MODEL.md` and
`CREDENTIAL_VAULT_ARCHITECTURE.md`.

---

## 16. Background processing

Celery handles work that should not block requests, including:

- mailbox sync;
- attachment retrieval;
- malware scanning/backfill;
- outbound delivery;
- retry/backoff;
- suitable asynchronous classification/routing;
- later notifications.

Critical operations remain idempotent so retries do not duplicate Tickets,
Messages or sends.

Background tasks that need a secret use the Vault's server-side credential
service; they do not call human reveal/copy endpoints.

---

## 17. Future refinements

The Ticket domain is operationally usable. Future work should be driven by real
usage and surrounding platform maturity rather than another foundational
rewrite.

Likely later refinements:

- ambiguous Graph-send resilience;
- richer search/automation;
- explicit Task/Project/Infrastructure/KB links where workflows justify them;
- notifications/preferences;
- SLA/escalation behaviour;
- Client portal communication through the same Ticket thread model.

Do not create a second communications system or a second secret store for any
of these features.

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

## Application transactional email

Django account verification, password resets and staff invitations share the
platform's Infisical Graph authentication through `MicrosoftGraphEmailBackend`.
`DEFAULT_FROM_EMAIL` is the single authorised application sender; it must be a
Microsoft 365 Shared Mailbox in the application's scoped Exchange send boundary.
Application messages are sent directly through Graph MIME `sendMail`, without
creating Tickets or requiring inbound Mailbox configuration. MIME preserves
recipient types, attachments and plain/HTML alternatives. Bodies/account tokens
are not persisted by the transport. SMTP/console environment configuration is
removed; Django tests retain their isolated in-memory test backend.

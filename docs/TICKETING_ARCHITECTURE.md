# Ticketing Architecture

## Purpose

The ticketing system is the primary communications hub for the ADB Business Platform. It must ingest support and enquiry traffic from multiple sources, associate it with the correct ADB brand and operational queue, resolve known clients and contacts, preserve complete message threads and attachments, and expose the surrounding client context to authorised staff.

The implementation should build on the useful behaviour in the existing Stacked Finds support system without copying its single-mailbox assumptions or tightly coupling ingestion logic to Celery tasks.

## Core principles

- A Ticket is the operational thread. Individual emails, contact-form submissions and replies are Ticket Messages.
- Brand, Client and Queue are separate concepts.
- A ticket may be client-owned or unassociated while sender resolution/classification is pending.
- A client ticket may identify a specific primary Client Contact while retaining all participants on individual messages.
- Microsoft Graph connections and mailboxes are database-backed configuration, not hard-coded Django settings.
- Microsoft Graph application authentication is connection-level infrastructure and must not be repeated for each mailbox.
- ADB operational ticket mailboxes are Microsoft 365 Shared Mailboxes; licensed user mailboxes are not ticketing sources.
- Multiple Microsoft tenants/connections and an arbitrary number of configured Shared Mailboxes must remain supportable.
- Ingestion is idempotent. Provider message IDs and internet Message-ID values must prevent duplicate imports.
- Normalisation, classification, routing and attachment scanning are explicit pipeline stages rather than a single polling function.
- Backend permissions and object scopes remain authoritative.
- Sensitive attachment and credential operations are separately permissioned and audit logged.

## Primary models

### MicrosoftGraphConnection

Represents an application/tenant-level Microsoft Graph connection.

Suggested fields:

- name
- tenant_id
- client_id
- authentication_method
- certificate credential/reference
- enabled
- last_verified_at
- last_error
- created_at / updated_at

Certificate/private-key material must use the platform credential/storage architecture rather than being returned through ordinary APIs. Normal ticketing settings should present the connection as platform infrastructure rather than asking an operator to enter application or certificate details when adding each mailbox.

### Mailbox

Represents one mailbox consumed by the platform. For the ADB Microsoft 365 tenant, operational ticket mailboxes are Shared Mailboxes.

Suggested fields:

- graph_connection
- email_address
- display_name
- brand
- mailbox_type/purpose
- default_queue
- enabled
- sync_state / Graph delta link
- last_synced_at
- last_successful_sync_at
- last_error
- created_at / updated_at

Examples include `support@adbwebdesigns.co.uk`, `support@adbsoftwaresolutions.co.uk`, `support@adbtechnology.co.uk` and accounts mailboxes.

The Mailbox table is the application-level allow-list for ticket ingestion. A Shared Mailbox being accessible to the Graph application does not make it a ticket source until it is explicitly configured and enabled here.

### TicketQueue

Operational queue used for routing and staff access.

Suggested fields:

- name
- key
- brand (nullable where a genuinely cross-brand queue is useful)
- purpose
- default_priority
- enabled
- ordering

Queue access must integrate with the platform permission/scope model so staff can be granted access to only specific queues where required.

### Ticket

Suggested fields:

- reference / human-readable ticket number
- brand
- queue
- client (nullable)
- primary_contact (nullable)
- subject
- status
- priority
- classification
- source
- assigned_to
- created_at
- updated_at
- first_response_at
- last_message_at
- resolved_at
- closed_at

Future relationships may include Project and other operational resources, but these should not be required for the initial ticket foundation.

### TicketParticipant

Optional explicit representation of people/addresses involved in a thread where necessary for richer threading and CC behaviour.

### TicketMessage

Stores one inbound or outbound message.

Suggested fields:

- ticket
- direction
- sender_name
- sender_address
- to / cc / bcc recipients
- matched_contact (nullable)
- subject
- body_html
- body_text
- body_text_normalised
- provider
- provider_message_id
- internet_message_id
- in_reply_to
- references
- sent_or_received_at
- delivery_status
- delivery_error
- created_by for staff-authored messages
- created_at

Provider identifiers must be indexed where appropriate.

### TicketAttachment

Suggested fields:

- message
- original_filename
- safe/stored filename or storage key
- declared_content_type
- detected_content_type
- size
- sha256
- scan_status
- scan_engine
- scan_result
- quarantined_at
- scanned_at
- safe_at
- created_at

Incoming files should not be exposed for download until they pass the attachment policy and malware scan.

### TicketNote

Internal staff-only note separate from customer-visible messages.

Suggested fields:

- ticket
- author
- body
- created_at
- updated_at

## Ingestion pipeline

All sources feed the same internal ingestion service.

```text
Incoming payload
    -> source adapter
    -> canonical message
    -> body/header normalisation
    -> attachment quarantine
    -> spam/abuse evaluation
    -> sender/client/contact resolution
    -> message classification
    -> brand/queue/priority routing
    -> thread matching
    -> ticket/message persistence
    -> attachment scanning
    -> downstream notifications/workflows
```

### Source adapters

Initial sources:

- Microsoft Graph mailboxes
- public website contact forms

Future-compatible sources:

- API/webhook ingestion
- monitoring/infrastructure integrations
- client portal submissions

Adapters should only translate provider-specific payloads into a canonical ingestion object. They should not contain routing policy.

## Microsoft Graph ingestion

Prefer Graph delta queries/subscriptions where practical rather than permanently polling only unread Inbox messages. The persistence model must retain provider sync state so ingestion can resume safely after restarts.

The Graph integration must support:

- multiple configured Shared Mailboxes;
- reading messages and headers;
- downloading file attachments;
- preserving internet Message-ID, In-Reply-To and References values;
- sending replies from the mailbox associated with the ticket;
- CC/BCC where supported by the UI;
- provider errors and retry state;
- idempotent ingestion;
- processed/archive behaviour that does not rely solely on marking messages read.

### ADB Microsoft 365 deployment model

The normal ADB deployment uses one tenant/application-level Graph connection with certificate-based application authentication configured once. Mailboxes added to ticketing reuse that connection; adding a mailbox must not require re-entering a certificate, client ID, tenant ID or interactive Microsoft login.

Exchange Online must provide the outer security boundary for application mailbox access. Use Exchange Online RBAC for Applications with one dynamic management scope whose recipient restriction matches Microsoft 365 Shared Mailboxes, conceptually:

```powershell
New-ManagementScope `
  -Name "ADB Ticketing Shared Mailboxes" `
  -RecipientRestrictionFilter "RecipientTypeDetails -eq 'SharedMailbox'"
```

The required Exchange application mail roles are assigned to that scope once. Because the scope is property-based, a newly-created Shared Mailbox enters the scope automatically without creating another RBAC rule. Licensed `UserMailbox` recipients do not match this scope and are therefore outside the ticketing application's intended Exchange resource boundary.

Do not combine this resource-scoped Exchange permission model with an equivalent unscoped Microsoft Entra mail grant in a way that restores organisation-wide mailbox access. Exchange RBAC for Applications and Entra application grants are additive, so deployment configuration must preserve the scoped boundary.

The application then applies a narrower operational selection: Celery only synchronises enabled `Mailbox` records stored in the ADB database. The Graph application being technically allowed to access all Shared Mailboxes is not permission to enumerate or ingest every Shared Mailbox automatically.

For a deployment with exactly one enabled Graph connection, mailbox creation should automatically use it. If multiple Microsoft 365 tenant connections are configured in future, the admin UI may ask which connection owns the Shared Mailbox.

## Thread matching

Use several signals in priority order rather than relying on one subject token:

1. explicit platform ticket reference embedded in outbound subjects/headers;
2. internet Message-ID / In-Reply-To / References relationships;
3. known provider conversation identifiers where reliable;
4. conservative fallback matching only where safe.

Never merge unrelated conversations based only on a similar subject.

## Body normalisation and signature removal

The existing Stacked Finds implementation demonstrates useful quoted-reply stripping. The ADB platform should move this into a reusable normalisation service.

Store both original sanitised HTML/plain representations and a normalised display/search body where appropriate.

Normalisation should handle common reply markers and quoted history from Outlook, Gmail and other common clients without destroying genuinely new content. Signature removal should be conservative; retaining a small amount of signature text is preferable to deleting customer content.

HTML must be sanitised before rendering in the admin UI.

## Sender, client and contact resolution

Normalise email addresses and attempt matching against active Client Contacts first, then other known client addresses.

When a contact is matched:

- associate the message with that contact;
- associate the ticket with the contact's client where unambiguous;
- expose the ticket on both the Client workspace and the Client Contact workspace.

Unknown senders remain valid tickets and may later be associated manually or through classification/routing rules.

## Classification and routing

Spam detection and business routing are different concerns.

Suggested classifications:

- client_support
- sales
- accounts
- vendor
- automated_system
- monitoring
- newsletter_marketing
- probable_spam
- unknown

The first implementation should combine deterministic rules and transparent scoring. Classification reasons should be retained so operators can understand why a message was routed.

Routing inputs may include:

- mailbox/default queue;
- assigned brand;
- sender/client/contact match;
- sender/domain allow/block/vendor rules;
- recipient alias;
- subject/body rules;
- spam score;
- future learned classification.

Vendor newsletters and automated notifications should be routed away from urgent customer queues rather than indiscriminately marked as spam.

## Attachment security

Attachments are untrusted input.

Initial safety pipeline:

1. enforce configured size limits;
2. normalise/sanitise filename and never trust path input;
3. calculate SHA-256;
4. detect content type from bytes as well as provider metadata;
5. quarantine the file;
6. reject or specially handle prohibited executable/script formats according to policy;
7. asynchronously scan with a malware scanner;
8. expose download/preview only after a safe result.

ClamAV is the preferred initial self-hosted scanner, but the scanning service should expose an interface so another engine can be substituted later.

Scanning failures/timeouts must fail closed for downloads: `unknown` or `scan_failed` is not equivalent to safe.

## Permissions

Ticketing introduces both capability and scope permissions.

Capabilities should distinguish at least:

- view tickets
- create tickets
- change tickets
- reply to tickets
- add internal notes
- assign tickets
- close/reopen tickets
- view/download safe attachments
- configure queues
- configure mailboxes/Graph connections

Scopes must support restricting staff to permitted clients and permitted ticket queues. A user must satisfy both applicable capability and scope checks.

## Admin UX

### Ticket list

The main Ticket workspace must be server-side paginated from its first implementation.

Filters should include:

- queue
- brand
- status
- priority
- assigned staff member
- client
- classification
- mailbox/source
- date range
- free-text search

Useful views may include My Tickets, Unassigned, Customer Replied, Waiting for Customer, Urgent, Spam/Quarantine and queue-specific views.

### Ticket detail

The ticket screen should be message/thread focused with an adjacent contextual workspace containing authorised client information.

Target contextual access:

- Client summary and contacts
- Client Knowledge Base
- Client Infrastructure
- Client Credentials (subject to separate credential permissions)
- Client Projects
- related Tasks/Time where relevant

The ticket view must never bypass existing access-control checks simply because the ticket references a client.

### Client and contact workspaces

Client detail pages should expose all visible tickets associated with that client.

Individual Client Contact pages should expose tickets/messages involving that contact.

## Website contact forms

Public contact forms on each brand website should submit into the same ingestion pipeline, supplying the brand and form/source metadata explicitly.

Contact-form ingestion should support anti-abuse controls independently of mailbox spam scoring and should retain IP/user-agent metadata only where needed and in accordance with the platform's privacy policy.

## Background processing

Celery should handle work that should not block API requests, including:

- mailbox synchronisation;
- attachment retrieval;
- malware scanning;
- outbound email delivery;
- retries/backoff;
- classification/routing jobs where asynchronous processing is appropriate;
- notifications.

Critical ingestion operations must be idempotent so Celery retries cannot duplicate tickets/messages.

## Development data

The development seeder should eventually generate:

- multiple ticket queues across all brands;
- multiple configured demo mailboxes without real secrets;
- tickets linked to different clients and contacts;
- unknown/vendor/spam examples;
- varied statuses/priorities/classifications;
- multi-message inbound/outbound threads;
- internal notes;
- attachment metadata with safe fake files and scan states.

No live Microsoft credentials or real customer email content belong in fixtures.

## Initial implementation order

1. TicketQueue, Ticket, TicketMessage, TicketNote and TicketAttachment models plus permissions.
2. Paginated ticket list/detail APIs and seeded development data.
3. Admin ticket list and thread UI.
4. Client and Client Contact ticket relationships/workspaces.
5. MicrosoftGraphConnection and Mailbox configuration models/settings UI.
6. Graph adapter and idempotent inbound sync.
7. reusable body normalisation/thread matching services.
8. outbound replies and attachment handling.
9. quarantine and malware scanning.
10. classification/routing/vendor/spam rules.
11. website contact-form ingestion.

This sequence allows the ticket domain and admin UX to be tested thoroughly with seeded data before introducing live external mailbox traffic.

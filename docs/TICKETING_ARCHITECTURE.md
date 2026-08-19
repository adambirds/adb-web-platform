# Ticketing Architecture

## Purpose

The ticketing system is the primary communications hub for the ADB Business Platform. It must ingest support and enquiry traffic from multiple sources, associate it with the correct ADB brand and operational queue, resolve known clients, contacts and vendors, preserve complete message threads and attachments, and expose the surrounding client context to authorised staff.

The implementation builds on the useful behaviour in the existing Stacked Finds support system without copying its single-mailbox assumptions or tightly coupling ingestion logic to Celery tasks.

## Core principles

- A Ticket is the operational thread. Individual emails, contact-form submissions and replies are Ticket Messages.
- Brand, Client, Vendor and Queue are separate concepts.
- A ticket may be client-owned, vendor-associated or unassociated while sender resolution/classification is pending.
- A client ticket may identify a specific primary Client Contact while retaining all participants on individual messages.
- Microsoft Graph connections and mailboxes are database-backed configuration, not hard-coded Django settings.
- Microsoft Graph application authentication is connection-level infrastructure and must not be repeated for each mailbox.
- ADB operational ticket mailboxes are Microsoft 365 Shared Mailboxes; licensed user mailboxes are not ticketing sources.
- Multiple Microsoft tenants/connections and an arbitrary number of configured Shared Mailboxes must remain supportable.
- Ingestion is idempotent. Provider message IDs and internet Message-ID values must prevent duplicate imports.
- Normalisation, classification, routing and attachment scanning are explicit pipeline stages rather than a single polling function.
- Vendor identification is database-backed operational policy. It must be configurable without a code deployment.
- Malware scanning is a deployment policy. The platform must support running without a scanner and later switching to a central ClamAV service without changing the ticket data model.
- Backend permissions and object scopes remain authoritative.
- Sensitive attachment and credential operations are separately permissioned and audit logged.

## Primary models

### MicrosoftGraphConnection

Represents an application/tenant-level Microsoft Graph connection.

Key fields:

- name
- tenant_id
- client_id
- authentication_method
- certificate credential/reference
- enabled
- last_verified_at
- last_error
- created_at / updated_at

Certificate/private-key material uses the platform credential/storage architecture rather than being returned through ordinary APIs. Normal ticketing settings present the connection as platform infrastructure rather than asking an operator to enter application or certificate details when adding each mailbox.

### Mailbox

Represents one mailbox consumed by the platform. For the ADB Microsoft 365 tenant, operational ticket mailboxes are Shared Mailboxes.

Key fields:

- graph_connection
- email_address
- display_name
- brand
- mailbox purpose
- default_queue
- enabled
- Graph delta link
- last_synced_at
- last_successful_sync_at
- last_error
- created_at / updated_at

Examples include `support@adbwebdesigns.co.uk`, `support@adbsoftwaresolutions.co.uk`, `support@adbtechnology.co.uk` and accounts mailboxes.

The Mailbox table is the application-level allow-list for ticket ingestion. A Shared Mailbox being accessible to the Graph application does not make it a ticket source until it is explicitly configured and enabled here.

### TicketQueue

Operational queue used for routing and staff access.

Key fields:

- name
- key
- brand (nullable where a genuinely cross-brand queue is useful)
- purpose
- default_priority
- enabled
- ordering

Queue access integrates with the platform permission/scope model so staff can be granted access to only specific queues where required. The initial vendor implementation includes a global `Vendors & Services` queue so third-party operational mail does not clutter customer-facing queues.

### Vendor

Represents an external provider or service whose correspondence should be retained in ticketing but normally routed away from customer queues.

Key fields:

- name
- website_url
- notes
- enabled
- created_at / updated_at

Examples include GitHub, DigitalOcean, PayPal, Microsoft, Elegant Themes, Google, Wordfence and LastPass. These examples are initial database data rather than a permanent hard-coded allow-list.

### VendorSenderRule

Defines an explicit sender rule used to identify and route vendor/service mail.

Key fields:

- vendor
- match_type (`email` or `domain`)
- match_value
- target_queue (nullable)
- priority override (optional)
- enabled
- ordering
- notes
- created_at / updated_at

Exact-address rules take precedence over domain rules. Domain rules match subdomains, so a rule for `github.com` also covers mail from a subdomain of `github.com`. A rule may route an unusually important sender to Operations or a higher priority rather than the normal Vendors & Services queue.

Rules are deliberately retained and can be disabled rather than requiring deletion. This keeps routing policy visible and auditable.

### Ticket

Key fields:

- reference / human-readable ticket number
- brand
- queue
- client (nullable)
- primary_contact (nullable)
- vendor (nullable)
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

A known Client/Contact relationship takes precedence over a vendor sender rule. This prevents a genuine customer address from being silently treated as vendor traffic merely because it happens to use a domain that is also configured for a provider.

Future relationships may include Project and other operational resources, but these are not required for the initial ticket foundation.

### TicketParticipant

Optional explicit representation of people/addresses involved in a thread where necessary for richer threading and CC behaviour.

### TicketMessage

Stores one inbound or outbound message.

Key fields:

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

Provider identifiers are indexed where appropriate.

### TicketAttachment

Key fields:

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

Attachment storage and malware gating are separate concerns. Files always pass through the platform's attachment policy/quarantine layer even when malware scanning is disabled.

### TicketNote

Internal staff-only note separate from customer-visible messages.

Key fields:

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
    -> sender/client/contact/vendor resolution
    -> message classification
    -> brand/queue/priority routing
    -> thread matching
    -> ticket/message persistence
    -> attachment scanning when enabled
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

Adapters only translate provider-specific payloads into a canonical ingestion object. They do not contain routing policy.

## Microsoft Graph ingestion

Prefer Graph delta queries/subscriptions where practical rather than permanently polling only unread Inbox messages. The persistence model retains provider sync state so ingestion can resume safely after restarts.

The Graph integration supports:

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

Exchange Online provides the outer security boundary for application mailbox access. Use Exchange Online RBAC for Applications with one dynamic management scope whose recipient restriction matches Microsoft 365 Shared Mailboxes, conceptually:

```powershell
New-ManagementScope `
  -Name "ADB Ticketing Shared Mailboxes" `
  -RecipientRestrictionFilter "RecipientTypeDetails -eq 'SharedMailbox'"
```

The required Exchange application mail roles are assigned to that scope once. Because the scope is property-based, a newly-created Shared Mailbox enters the scope automatically without creating another RBAC rule. Licensed `UserMailbox` recipients do not match this scope and are therefore outside the ticketing application's intended Exchange resource boundary.

Do not combine this resource-scoped Exchange permission model with an equivalent unscoped Microsoft Entra mail grant in a way that restores organisation-wide mailbox access. Exchange RBAC for Applications and Entra application grants are additive, so deployment configuration must preserve the scoped boundary.

The application then applies a narrower operational selection: Celery only synchronises enabled `Mailbox` records stored in the ADB database. The Graph application being technically allowed to access all Shared Mailboxes is not permission to enumerate or ingest every Shared Mailbox automatically.

For a deployment with exactly one enabled Graph connection, mailbox creation automatically uses it. If multiple Microsoft 365 tenant connections are configured in future, the admin UI may ask which connection owns the Shared Mailbox.

## Thread matching

Use several signals in priority order rather than relying on one subject token:

1. explicit platform ticket reference embedded in outbound subjects/headers;
2. internet Message-ID / In-Reply-To / References relationships;
3. known provider conversation identifiers where reliable;
4. conservative fallback matching only where safe.

Never merge unrelated conversations based only on a similar subject.

## Body normalisation and signature removal

The existing Stacked Finds implementation demonstrates useful quoted-reply stripping. The ADB platform moves this into a reusable normalisation service.

Store both original sanitised HTML/plain representations and a normalised display/search body where appropriate.

Normalisation handles common reply markers and quoted history from Outlook, Gmail and other common clients without destroying genuinely new content. Signature removal remains conservative; retaining a small amount of signature text is preferable to deleting customer content.

HTML must be sanitised before rendering in the admin UI.

## Sender, client, contact and vendor resolution

Normalise email addresses and attempt matching against active Client Contacts first, then other known client addresses.

When a contact is matched:

- associate the message with that contact;
- associate the ticket with the contact's client where unambiguous;
- expose the ticket on both the Client workspace and the Client Contact workspace.

Only after client resolution fails should explicit Vendor sender rules be evaluated. Exact sender-address rules win over domain rules. Domain rules support subdomains and identify the associated `Vendor` record, target queue and optional priority override.

Vendor messages remain normal auditable Tickets. They are not discarded, hidden or converted to spam merely because a sender rule matched. An operator can therefore find and move a message if a sender was classified as a vendor incorrectly.

Unknown senders remain valid tickets and may later be associated manually or through classification/routing rules.

## Classification and routing

Spam detection and business routing are different concerns.

Current classifications include:

- client_support
- sales
- accounts
- vendor
- automated_system
- monitoring
- newsletter_marketing
- probable_spam
- unknown

The initial implementation combines deterministic rules and transparent scoring. Classification reasons are logged so operators can understand why a message was routed.

Routing inputs include:

- mailbox/default queue;
- assigned brand;
- sender/client/contact match;
- database-backed vendor sender rules;
- recipient alias;
- subject/body rules;
- spam score;
- future learned classification.

Vendor/service correspondence is routed to the rule's explicit target queue where configured, otherwise to a matching brand vendor queue, then the global `Vendors & Services` queue. An exact sender rule can intentionally send a security/billing/operations address elsewhere with a different priority. Vendor newsletters and automated notifications are retained away from urgent customer queues rather than indiscriminately marked as spam.

## Attachment security

Attachments are untrusted input even when malware scanning is temporarily disabled.

The always-on attachment safety layer:

1. enforces configured size limits;
2. normalises/sanitises filenames and never trusts path input;
3. calculates SHA-256;
4. detects content type from bytes as well as provider metadata;
5. stores accepted content in controlled quarantine storage;
6. records policy-blocked files without exposing their content;
7. applies the separate ticket-attachment capability and ticket/client/queue scope checks before download.

ClamAV is the preferred initial self-hosted malware scanner, but the scanning service exposes an interface so another engine can be substituted later. `clamd` may be local to the deployment or a central private service reachable by Celery workers through `TICKETING_CLAMAV_HOST` and `TICKETING_CLAMAV_PORT`.

Malware scanning is controlled by `TICKETING_MALWARE_SCANNING_ENABLED` and is disabled by default for the initial rollout:

- **disabled:** `pending` or previous `scan_failed` attachments that passed the always-on attachment policy may be downloaded by authorised staff;
- **enabled:** only attachments with a clean `safe` verdict are downloadable; pending/failed scans remain unavailable;
- **infected or policy-blocked:** never downloadable in either mode.

When scanning is enabled, new attachments are queued for ClamAV immediately. Celery Beat also dispatches pending/failed attachments for scanning so content received while scanning was disabled is picked up after the feature is enabled. This means switching the environment flag on immediately makes unscanned content unavailable until it is processed, rather than trusting historic pending files.

Scanner connection failures, timeouts and indeterminate replies fail closed while scanning is enabled and are retried with backoff.

## Permissions

Ticketing introduces both capability and scope permissions.

Capabilities distinguish at least:

- view tickets
- create tickets
- change tickets
- reply to tickets
- add internal notes
- assign tickets
- close/reopen tickets
- view/download ticket attachments permitted by the active malware policy
- configure queues
- configure mailboxes/Graph connections
- configure vendors and sender rules

Scopes support restricting staff to permitted clients and permitted ticket queues. A user must satisfy both applicable capability and scope checks.

## Admin UX

### Ticket list

The main Ticket workspace is server-side paginated from its first implementation.

Filters include or may expand to include:

- queue
- brand
- status
- priority
- assigned staff member
- client
- classification
- mailbox/source
- date range
- free-text search, including vendor names

Useful views may include My Tickets, Unassigned, Customer Replied, Waiting for Customer, Urgent, Spam/Quarantine, Vendors & Services and queue-specific views.

### Ticket detail

The ticket screen is message/thread focused with an adjacent contextual workspace containing authorised client/vendor information.

Target contextual access:

- Client summary and contacts
- matched Vendor/service identity
- Client Knowledge Base
- Client Infrastructure
- Client Credentials (subject to separate credential permissions)
- Client Projects
- related Tasks/Time where relevant

The ticket view never bypasses existing access-control checks simply because the ticket references a client.

### Vendor routing settings

The platform Settings workspace lists Vendors and sender rules. Operators can add new vendors and exact-address/domain rules without a code deployment, choose an explicit queue and priority where required, and disable a vendor or individual rule without deleting historical tickets.

### Client and contact workspaces

Client detail pages expose all visible tickets associated with that client.

Individual Client Contact pages expose tickets/messages involving that contact.

## Website contact forms

Public contact forms on each brand website submit into the same ingestion pipeline, supplying the brand and form/source metadata explicitly.

Contact-form ingestion supports anti-abuse controls independently of mailbox spam scoring and retains IP/user-agent metadata only where needed and in accordance with the platform's privacy policy.

## Background processing

Celery handles work that should not block API requests, including:

- mailbox synchronisation;
- attachment retrieval;
- malware scanning when enabled;
- backfilling pending/failed scans when malware scanning is enabled;
- outbound email delivery;
- retries/backoff;
- classification/routing jobs where asynchronous processing is appropriate;
- notifications.

Critical ingestion operations are idempotent so Celery retries cannot duplicate tickets/messages.

## Development data

Development data covers:

- multiple ticket queues across brands plus cross-brand operational queues;
- multiple configured demo mailboxes without real secrets;
- tickets linked to different clients and contacts;
- unknown/vendor/spam examples;
- initial Vendor records and sender-domain rules;
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
9. quarantine and optional malware scanning.
10. classification/routing/vendor/spam rules.
11. website contact-form ingestion.

The initial vertical slice now implements this sequence. Follow-up work should refine operational rules and deployment configuration rather than expanding this foundation PR indefinitely.

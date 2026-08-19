# Current State and Operational Roadmap

This document is the implementation companion to:

- `docs/PLATFORM_MASTER_PLAN.md` — canonical product/architecture plan;
- `docs/PERMISSIONS_AND_ACCESS_MODEL.md` — capability and scope rules;
- `docs/DOMAIN_MODEL_AUDIT.md` — model audit decisions;
- `docs/TICKETING_ARCHITECTURE.md` — ticketing/communications architecture;
- `docs/MICROSOFT_GRAPH_TICKETING_SETUP.md` — Microsoft 365/Graph deployment runbook.

It records what is actually implemented and, importantly, what is still missing before the public websites become the primary development focus.

## 1. Current repository topology

```text
backend/
packages/
sites/
    adb-software-solutions/
    adb-web-designs/
    adb-technology/
    auth-adb-software-solutions/
```

`sites/adb-software-solutions/` is the combined ADB Software Solutions application. Its authenticated operations workspace lives under `/admin`; there is no separate admin application/deployment.

The authentication/account application remains separate at `sites/auth-adb-software-solutions/`.

## 2. Foundation status

### Completed architecture/foundation

- [x] Shared Django backend is the business-data and authorisation authority.
- [x] Django Ninja is the established API layer.
- [x] ADB Software Solutions, Web Designs and Technology are first-class Brands.
- [x] Client/Internal ownership conventions are established.
- [x] Capability permissions and Client access scopes exist.
- [x] Append-only AuditEvent foundation exists.
- [x] CMS content is Brand-aware and public content is isolated by Brand.
- [x] Authentication frontend has been migrated to Next.js while preserving Django sessions/TOTP/WebAuthn.
- [x] ADB Software Solutions public/admin topology has been unified into one Next.js app with `/admin`.
- [x] Internal operations shell, navigation and reusable data-table/state primitives exist.
- [x] Deterministic development seed data exists.
- [x] Celery worker/beat and Redis orchestration are available.
- [x] Devcontainer CI builds on AMD64 and ARM64.

### Documentation/configuration work in progress

- [x] Replace stale separate-admin architecture in canonical plans.
- [x] Record the expanded operational roadmap before public-site focus.
- [x] Mark obsolete root planning docs as superseded.
- [x] Add a full Microsoft Graph / Exchange RBAC deployment runbook.
- [ ] Keep the runbook updated if Graph credential/storage or mailbox UI changes.

## 3. Ticketing and communications

The ticketing foundation is implemented end-to-end and is no longer a future-only phase.

### Implemented

- [x] TicketQueue, Ticket, TicketMessage, TicketNote and TicketAttachment domains.
- [x] queue/client permission scoping.
- [x] paginated/filterable Ticket APIs and list/detail workspace.
- [x] assignment, status, priority and queue operations.
- [x] internal notes and customer replies.
- [x] Client and Contact Ticket context.
- [x] MicrosoftGraphConnection and Mailbox configuration.
- [x] encrypted integration credential support.
- [x] certificate/client-secret app-only Graph authentication.
- [x] Shared Mailbox verification before save.
- [x] Graph delta sync, persisted cursors and worker locking.
- [x] inbound message normalisation/thread matching.
- [x] outbound Graph replies with Celery retries/duplicate-send controls.
- [x] website contact-form Lead -> canonical Ticket ingestion.
- [x] deterministic classification/routing and probable-spam quarantine behaviour.
- [x] database-backed Vendor + VendorSenderRule routing.
- [x] attachment quarantine, filename/size/hash/MIME policy.
- [x] optional ClamAV malware scanning with central-scanner support.
- [x] attachment download policy exposed to the UI.

### Follow-up ticket refinements

These are not prerequisites for starting other operational modules, but remain useful follow-up work:

- [ ] harden ambiguous Graph-send idempotency for the rare case where Graph accepts a send but the worker loses the response before persistence;
- [ ] continue improving operational ticket search/filter/automation as real usage identifies needs;
- [ ] add richer links from Tickets into Tasks/Time/KB/Infrastructure as those modules mature;
- [ ] add notification preferences/agent notifications when the broader notification system is designed.

## 4. Clients and Contacts

### Implemented

- [x] Client and ClientContact models.
- [x] Client permission/scope policy foundation.
- [x] Client list/register API/UI.
- [x] Client detail workspace foundation.
- [x] Client contacts/projects/tickets can be surfaced in context.
- [x] Contact email matching participates in inbound Ticket resolution.

### Missing for day-to-day use

- [ ] create Client from the custom operations UI.
- [ ] edit Client.
- [ ] archive/reactivate Client.
- [ ] create/edit/archive contacts.
- [ ] manage primary/billing/technical contact semantics.
- [ ] improve Client detail into the main operational hub.
- [ ] add Client sections for Infrastructure, KB, Credentials, Tasks and Time.
- [ ] add Client period summaries (especially time by week/month).
- [ ] permission-aware quick actions from the Client workspace.

## 5. CRM / Leads

### Implemented

- [x] Lead domain foundation and Brand/source concepts.
- [x] Lead list/register foundation.
- [x] website contact form creates a Lead.
- [x] new Contact Form Leads feed the canonical Ticket ingestion path.
- [x] Lead/ticket creation is idempotent and public lead capture fails open if ticket routing fails.

### Missing

- [ ] Lead detail workspace.
- [ ] create Lead manually.
- [ ] edit Lead.
- [ ] archive/close Lead.
- [ ] owner/assignee workflows.
- [ ] practical pipeline/list/filter views.
- [ ] communication/ticket history visible from the Lead.
- [ ] explicit ticket/email linking for manually-created/updated Leads.
- [ ] contact deduplication/matching workflows.
- [ ] Lead -> Client/Contact conversion while retaining Ticket/communication history.
- [ ] optional value/currency/follow-up metadata where useful.

## 6. Projects

### Implemented

- [x] operational Project model separated from public Portfolio/CaseStudy.
- [x] Project register/list foundation.
- [x] basic Client relationship and development data.

### Missing

- [ ] Project detail page/workspace.
- [ ] create Project.
- [ ] edit Project.
- [ ] archive/change status.
- [ ] Client/Internal project workflows.
- [ ] dates/milestones and ownership/participants where useful.
- [ ] related Tasks.
- [ ] related Time entries and summaries.
- [ ] related Tickets/KB/Infrastructure links.
- [ ] project-centric timer start/stop actions.

## 7. Tasks

### Implemented

- [x] Task model/domain foundation.
- [x] standalone tasks are supported conceptually and do not require Projects.
- [x] Task register/list foundation.
- [x] assignment/due/priority concepts exist in the operational model where established.

### Missing

- [ ] create Task.
- [ ] edit Task.
- [ ] delete/archive Task according to lifecycle rules.
- [ ] mark complete/reopen.
- [ ] recurrence UX/worker behaviour where recurrence is enabled.
- [ ] list modes: My Tasks, Today, Upcoming, Overdue, Completed.
- [ ] filters by Client, Project, assignee, status and priority.
- [ ] Project-linked, Client-linked and future Ticket-linked quick creation.
- [ ] task detail/workspace where detail justifies it.
- [ ] task-centric timer start/stop.
- [ ] Calendar integration.

## 8. Calendar / work planning

### Current status

There is no complete operations calendar yet.

### Required

- [ ] day/week/month calendar views.
- [ ] aggregate Task due/start dates.
- [ ] aggregate Project milestones/deadlines.
- [ ] support recurring work once materialised.
- [ ] filter by user, Client, Project and source type.
- [ ] permission-aware event loading.
- [ ] design a first-class Event/Meeting domain later without pretending every Task is an Event.
- [ ] leave a clean integration path for external calendars if/when that becomes useful.

## 9. Time tracking

### Implemented

- [x] TimeEntry domain foundation.
- [x] Time register/list foundation.
- [x] Project/Client relationships exist where currently modelled.

### Missing

- [ ] manually add time.
- [ ] edit time.
- [ ] delete time subject to permissions.
- [ ] running timer model/lifecycle.
- [ ] Start timer action.
- [ ] Stop timer action with backend-calculated duration.
- [ ] enforce one active timer per user initially.
- [ ] start/stop from Project.
- [ ] start/stop from Task.
- [ ] start/stop from Ticket.
- [ ] direct Client association for valid non-project work.
- [ ] daily/weekly/monthly views.
- [ ] totals by Client, Project, Task, Ticket and staff user.
- [ ] Client workspace time reporting by week/month/custom range.
- [ ] Project/Ticket contextual time totals.
- [ ] future billable/invoice linkage without making invoicing a current dependency.

## 10. Knowledge Base

### Implemented

- [x] Knowledge Base model/register foundation.
- [x] Client/Internal ownership foundation.
- [x] permission/scoping foundation.

### Missing

- [ ] create/edit/archive/delete-policy workflow.
- [ ] document detail/read experience.
- [ ] categories/sections/tags.
- [ ] controlled Markdown/rich-text editing.
- [ ] attachments where justified.
- [ ] author/editor metadata in UI.
- [ ] version/change history.
- [ ] Client-context navigation.
- [ ] links to Tickets, Projects and Infrastructure.
- [ ] global and Client-context search.
- [ ] explicit future portal visibility, private by default.

## 11. Credentials vault

### Implemented

- [x] StoredCredential model.
- [x] Client/Internal ownership.
- [x] encrypted secret payload service using Fernet/MultiFernet.
- [x] environment-managed encryption keys.
- [x] separate view/reveal/copy capabilities.
- [x] service-level decryption path for integrations such as Microsoft Graph.
- [x] audit support for user secret reveal/copy.
- [x] metadata register/list foundation.

### Missing

- [ ] custom operations UI to create credentials securely.
- [ ] edit metadata.
- [ ] replace/rotate secret values.
- [ ] reveal UX.
- [ ] copy UX.
- [ ] expiry/rotation reminders/metadata.
- [ ] relationships to Infrastructure/Application records.
- [ ] Client-context credential navigation.
- [ ] search metadata only, never secret content.
- [ ] remove/deprecate remaining legacy plaintext-field use before production credential migration.

The Microsoft Graph bootstrap runbook currently documents a safe shell/service bootstrap path because full credential CRUD UI is not yet complete.

## 12. Infrastructure inventory

### Implemented

- [x] structured model foundation covering Servers, Databases, Websites, Domains, SSL Certificates, Licences, Applications and related operational resource types.
- [x] Infrastructure overview/register foundations.
- [x] Client/Internal ownership conventions.

### Missing

- [ ] full create/edit/archive workflows across resource types.
- [ ] useful detail workspaces.
- [ ] relationships among Application, Website, API, Database, Server, Domain, Licence and Certificate records.
- [ ] Credential links instead of duplicated secrets.
- [ ] KB/document links.
- [ ] Client-context Infrastructure views.
- [ ] expiry/renewal operational views and dashboard widgets.
- [ ] global/client search.

## 13. Users and Access

### Current problem

The custom operations navigation includes Users & Access but the route currently resolves to 404. This is a priority operational defect/feature gap.

### Required

- [ ] create a working Users & Access route/workspace.
- [ ] staff user list/detail.
- [ ] create/invite/activate/deactivate according to the existing identity model.
- [ ] Group/capability permission management.
- [ ] Client scope management.
- [ ] Ticket Queue scope management.
- [ ] clear effective-permission display.
- [ ] audit permission/scope changes.
- [ ] backend permission-boundary tests.

Routine staff administration must not require making users Django superusers.

## 14. Dashboard

### Implemented

- [x] initial operational dashboard/API with fixed summary content.

### Missing

- [ ] configurable widget catalogue.
- [ ] per-user persisted dashboard layout/configuration.
- [ ] reorder/move/resize where practical.
- [ ] widget permission filtering.
- [ ] Ticket Queue widget configurable to a selected queue.
- [ ] Assigned-to-me Ticket widget.
- [ ] unassigned/overdue/open Ticket widgets.
- [ ] My Tasks/Overdue/Upcoming widgets.
- [ ] active timer/recent Time widgets.
- [ ] Lead follow-up widgets.
- [ ] Project milestone/status widgets.
- [ ] Infrastructure expiry/renewal widgets.
- [ ] calendar agenda widget.

Widgets must query through normal scoped backend services/APIs rather than bypassing access rules.

## 15. Client workspace completion target

A Client should ultimately be one of the most useful pages in the entire platform.

From a Client, authorised staff should be able to access:

- [x] basic Client details.
- [x] Contacts foundation.
- [x] Tickets foundation.
- [x] Projects foundation.
- [ ] Leads/sales history where relevant.
- [ ] Infrastructure.
- [ ] Knowledge Base.
- [ ] Credentials.
- [ ] Tasks.
- [ ] Time entries.
- [ ] Time totals by week/month/custom period.
- [ ] activity/history.
- [ ] contextual create actions for Project/Task/Time/KB/Infrastructure/Credential where permission permits.

Related data must remain permission-scoped. Client context enriches navigation; it does not widen access.

## 16. Public websites

The public-site CMS/content plumbing and contact-form ingestion foundations exist, but the public websites are **not the next main phase**.

Primary public-site feature development is deferred until the internal operational platform has completed the core items in sections 4–15 sufficiently to run normal ADB work.

Public-site fixes, security work and stable integration changes can still happen opportunistically.

## 17. Ordered implementation sequence

This is the current intended sequence, subject to normal small adjustments as implementation reveals dependencies:

1. **Docs/config/dependency health**
   - canonical roadmap reconciliation;
   - Microsoft Graph deployment runbook;
   - Dependabot/security updates;
   - CI green.
2. **Clients/Contacts + Users & Access**
   - full CRUD and scopes;
   - complete Client hub foundation;
   - repair Users & Access 404.
3. **Leads + Projects + Tasks operational workflows**
   - detail/create/edit/status/complete/list modes;
   - Ticket/email links for Leads;
   - contextual relationships.
4. **Knowledge Base + Credentials + Infrastructure**
   - IT Glue-style CRUD/detail/search/relationships;
   - secure vault reveal/copy/rotation.
5. **Time Tracking + Calendar**
   - running timers from Task/Project/Ticket;
   - reporting by period/context;
   - calendar/agenda aggregation.
6. **Integrated Client workspaces + configurable Dashboard**
   - full cross-domain Client context;
   - user-configurable widget layouts.
7. **Public websites**
   - complete the three brand sites against stable platform contracts.
8. **Later commercial/client-facing features**
   - portal, quotes, contracts, invoicing, Stripe/payments.

## 18. Definition of internal-platform readiness for public-site focus

The internal platform does not need every imaginable feature before public-site work, but it should meet this practical gate:

- Clients and Contacts can be created/edited/managed in the custom UI;
- Leads can be viewed/managed and their communication relationship is visible;
- Projects and Tasks have usable detail/CRUD/workflow screens;
- Users & Access works;
- Knowledge Base/Credentials/Infrastructure have functional CRUD/detail workflows;
- Time supports manual entries and start/stop timers with contextual links;
- Calendar provides useful work planning;
- Client workspace exposes the major related operational domains;
- dashboard is materially useful and at least supports configurable/persisted widgets;
- CI/security/dependency health is green.

At that point the internal platform is sufficiently coherent that the public sites can be built without repeatedly redesigning the operational contracts underneath them.
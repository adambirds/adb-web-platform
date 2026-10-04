# Business domains

Use each app guide to find models, business rules, APIs and tests.

- [Staff capabilities and object scopes](access_control/README.md) — Staff access profiles, Client grants and Ticket Queue grants. Django permissions supply capabilities; this app supplies object visibility.
- [Clients, Contacts, Projects and Time](clients/README.md) — The main operational context for Client work. This app also owns Projects, manual Time Entries and persistent Running Timers, including first-class Internal work.
- [Shared platform foundations](core/README.md) — Brand identity, audit history, preferences and cross-domain operational projections. Brand identity is separate from Client/Internal ownership.
- [Encrypted Credential Vault](credentials/README.md) — Client/Internal credential metadata and encrypted secret payloads. Metadata access and secret reveal/copy/download are separate permissioned capabilities.
- [Leads and commercial enquiries](crm/README.md) — Lead assignment, lifecycle, Client conversion and communication projections. Email remains part of the shared Ticket/Graph pipeline.
- [Technical resources and topology](infrastructure/README.md) — Structured Client/Internal resources, specialist technical records and typed relationships. Legacy identity bridges and reconciliation remain explicit until migration is complete.
- [Knowledge documents and protected attachments](knowledge_base/README.md) — Client/Internal document trees, Markdown content, immutable versions and resource links. Portal visibility is explicit; attachments use protected access and scanning.
- [Resource monitoring and technical health](monitoring/README.md) — Scheduled checks, historical results and failure/recovery incidents attached to Infrastructure resources.
- [Work management and Calendar](tasks/README.md) — Standalone Internal, Client-owned and Project-owned Tasks, including lists, sections, subtasks, dependencies, recurrence and comments. Calendar Events share operational ownership rules.
- [Unified communication and Microsoft Graph](ticketing/README.md) — Canonical Tickets unify Shared Mailbox email, public contact forms and operational replies. Client and Ticket Queue scope, sensitive attachment actions and audited operations remain backend-authoritative.
- [Brand-aware public editorial content](website/README.md) — Public blog posts, testimonials, FAQs and portfolio content, plus contact-form entrypoints. Marketing pages remain code-owned; public Portfolio is separate from operational Project.

Identity lives separately in [authentication](../authentication/README.md).
Shared bootstrap code lives in [adbsoftwaresolutions](../adbsoftwaresolutions/README.md).

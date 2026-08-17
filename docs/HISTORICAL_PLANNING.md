# Historical Planning Documents

The repository contains two root-level planning documents that pre-date the current multi-brand ADB Business Platform architecture:

- `ADB_SOFTWARE_SOLUTIONS_BUILD_PLAN.md`
- `DJANGO_ARCHITECTURE.md`

They are retained because they contain useful original product ideas and implementation context, particularly around the internal operations platform, infrastructure inventory, credentials, knowledge base, projects, tasks, and time tracking.

They are **historical documents, not the current architectural specification**.

## Canonical documentation

When implementing or reviewing the platform, use this precedence order:

1. `docs/PLATFORM_MASTER_PLAN.md` — canonical product vision and target architecture.
2. `docs/PERMISSIONS_AND_ACCESS_MODEL.md` — canonical capability and object-scope model.
3. `docs/DOMAIN_MODEL_AUDIT.md` — current decisions about existing Django domains and models.
4. `docs/CURRENT_STATE_AND_FOUNDATION_CHECKLIST.md` — implementation status and ordered roadmap.
5. The historical root-level planning documents listed above.

If a historical document conflicts with a canonical document, the canonical document wins.

## Important superseded assumptions

In particular, agents must not revive these older assumptions without an explicit new decision:

- the platform serves only `adbsoftwaresolutions.co.uk`;
- public content belongs to one website rather than one or more `Brand` records;
- simple Admin/Staff/Read-only roles are sufficient for authorisation;
- client scope and ticket-queue scope do not need separate object-level controls;
- the public website and internal admin are the same frontend application;
- contact forms terminate in a standalone enquiry/lead workflow rather than the planned ticket/communications system;
- operational Projects and public case studies/Portfolio are the same concept;
- tasks must belong to projects;
- credentials can be treated as ordinary plaintext fields;
- DRF/GraphQL are undecided API layers for the current platform. The current backend uses Django Ninja for the APIs being actively developed.

## Current platform additions not represented in the old plans

The current architecture also includes major concepts added after those documents were written:

- three first-class public Brands: ADB Software Solutions, ADB Web Designs, and ADB Technology;
- code-owned marketing pages with Brand-aware CMS content;
- shared authentication/account application;
- fine-grained Django capability permissions plus object scope;
- append-only audit events;
- a dedicated future ticketing domain;
- Microsoft Graph mailbox ingestion across multiple branded support/accounts/sales mailboxes;
- automatic ClientContact-to-ticket matching;
- client/internal ownership as a platform-wide rule;
- later client portals, contracts, quotes, invoicing, and Stripe payments.

The historical documents may still be mined for useful details, but any extracted idea must be reconciled with the canonical architecture before implementation.

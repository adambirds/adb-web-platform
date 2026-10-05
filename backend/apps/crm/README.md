# Leads and commercial enquiries

Lead assignment, lifecycle, Client conversion and communication projections. Email remains part of the shared Ticket/Graph pipeline.

## Code map

| Location                                             | Responsibility                                       |
| ---------------------------------------------------- | ---------------------------------------------------- |
| [models.py](./models.py)                             | Lead records and status/outcome definitions          |
| [services.py](./services.py)                         | Lead business rules and conversion                   |
| [tasks.py](./tasks.py)                               | Background CRM work                                  |
| [ninja/admin_views.py](./ninja/admin_views.py)       | Lead administration                                  |
| [ninja/overview_views.py](./ninja/overview_views.py) | Lead workspace projections                           |
| [ninja/email_views.py](./ninja/email_views.py)       | Ticket-backed Lead email                             |
| [tests/](./tests/)                                   | Domain regression, API and permission-boundary tests |
| [migrations/](./migrations/)                         | Ordered database history                             |
| [admin.py](./admin.py)                               | Django admin registration                            |
| [apps.py](./apps.py)                                 | Django app configuration                             |

## Tests and related code

From the repository root, run `tools/test-backend apps.crm.tests`.
For a single module, use `tools/test-backend apps.crm.tests.test_<topic>`.

API routers are assembled in
[adbsoftwaresolutions/ninja/routers.py](../../adbsoftwaresolutions/ninja/routers.py).
Internal browser workflows live in
[the combined Software Solutions application](../../../sites/adb-software-solutions/README.md).

Read the [backend guide](../../README.md) for shared conventions and the
[canonical documentation map](../../../docs/README.md) before domain changes.

## Lead stages and sources

Migration `0005_default_lead_options` installs starter configuration without
requiring demo-data seeding. Sales stages are New, Contacted, Qualified, Proposal,
Negotiation, Won and Lost. Sources include Email, Phone, Website, Contact Form,
Referral, LinkedIn, Facebook, Instagram, X / Twitter, TikTok, YouTube, WhatsApp,
Organic search, Paid advertising, Event / networking and Other. Existing names
are matched without case sensitivity and existing configuration is preserved.

The lead create/edit form offers **Add stage** and **Add source** actions.
Catalogue entries are shared platform configuration: adding sources requires
`crm.add_leadsource`, and adding stages requires `crm.add_leadstatus`. Lead CRUD
permissions alone do not grant these capabilities. Custom stages require an
explicit Open/Won/Lost outcome; their display name does not determine reporting.
New lead forms preselect New, while Source remains unknown until chosen.

Assignment determines who owns the lead; sales stage describes its sales
progress. The list uses **No sales stage** for missing stages, reserves
**Unassigned** for missing owners, and refreshes immediately after drawer
assignment, editing or conversion.

### Direct stage changes and conversion

Lead workspaces and drawers expose a sales-stage selector plus **Mark as won**
and **Mark as lost** actions without opening Edit. The dedicated stage endpoint
requires `crm.change_lead` and updates only the stage and modification timestamp.
Quick actions resolve configured stages by their explicit outcome, not names.
The list refreshes after the action.

Converting a Lead to a Client also sets a Won stage within the same transaction
as Client/Contact creation and Ticket linking. An existing custom Won stage is
preserved. If no Won stage is configured, conversion fails before creating any
Client or Contact. Converted leads cannot use the direct stage action to reopen
or mark the opportunity Lost.

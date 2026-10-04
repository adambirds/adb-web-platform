# Unified communication and Microsoft Graph

Canonical Tickets unify Shared Mailbox email, public contact forms and operational replies. Client and Ticket Queue scope, sensitive attachment actions and audited operations remain backend-authoritative.

## Code map

| Location                                                   | Responsibility                                                          |
| ---------------------------------------------------------- | ----------------------------------------------------------------------- |
| [models.py](./models.py)                                   | Queues, Tickets, messages, notes, attachments and mailbox configuration |
| [config.py](./config.py)                                   | Ticketing environment configuration                                     |
| [services/ingestion.py](./services/ingestion.py)           | Canonical message ingestion and thread matching                         |
| [services/contact_forms.py](./services/contact_forms.py)   | Public-form Ticket ingestion                                            |
| [services/graph.py](./services/graph.py)                   | Inbound Graph adapter                                                   |
| [services/graph_auth.py](./services/graph_auth.py)         | App-only Graph authentication                                           |
| [services/graph_outbound.py](./services/graph_outbound.py) | Outbound Graph adapter                                                  |
| [services/replies.py](./services/replies.py)               | Reply workflow                                                          |
| [services/routing.py](./services/routing.py)               | Queue routing                                                           |
| [services/classification.py](./services/classification.py) | Message classification                                                  |
| [services/attachments.py](./services/attachments.py)       | Attachment handling                                                     |
| [services/scanning.py](./services/scanning.py)             | Malware scanning                                                        |
| [services/sla.py](./services/sla.py)                       | Queue targets and Ticket SLA health                                     |
| [tasks.py](./tasks.py)                                     | Mailbox sync, delivery and scanning workers                             |
| [signals.py](./signals.py)                                 | Model signal registration                                               |
| [ninja/](./ninja/)                                         | Ticket operations, configuration and communication APIs                 |
| [tests/](./tests/)                                         | Domain regression, API and permission-boundary tests                    |
| [migrations/](./migrations/)                               | Ordered database history                                                |
| [admin.py](./admin.py)                                     | Django admin registration                                               |
| [apps.py](./apps.py)                                       | Django app configuration                                                |

## Tests and related code

From the repository root, run `tools/test-backend apps.ticketing.tests`.
For a single module, use `tools/test-backend apps.ticketing.tests.test_<topic>`.

API routers are assembled in
[adbsoftwaresolutions/ninja/routers.py](../../adbsoftwaresolutions/ninja/routers.py).
Internal browser workflows live in
[the combined Software Solutions application](../../../sites/adb-software-solutions/README.md).

Read the [backend guide](../../README.md) for shared conventions and the
[canonical documentation map](../../../docs/README.md) before domain changes.

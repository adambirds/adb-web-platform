# Knowledge documents and protected attachments

Independent Client/Internal document trees, Markdown content, immutable versions and resource links.
The workspace starts with a Client/Internal picker; collection and option APIs
require one selected owner. The browser presents inline folders/articles with
breadcrumbs and list/grid views. `browse=true` returns directory contents, and
search includes descendants inside the selected owner. Creation inherits that
owner and the current folder. See
[`KNOWLEDGE_BASE_ARCHITECTURE.md`](../../../docs/KNOWLEDGE_BASE_ARCHITECTURE.md). Portal visibility is explicit; attachments use protected access and scanning.

## Code map

| Location                                                 | Responsibility                                       |
| -------------------------------------------------------- | ---------------------------------------------------- |
| [models.py](./models.py)                                 | Sections, documents, versions and attachments        |
| [services.py](./services.py)                             | Document writes, versions and lifecycle rules        |
| [attachment_security.py](./attachment_security.py)       | Attachment quarantine and access rules               |
| [tasks.py](./tasks.py)                                   | Attachment scanning jobs                             |
| [ninja/views.py](./ninja/views.py)                       | Knowledge workspace APIs                             |
| [ninja/attachment_views.py](./ninja/attachment_views.py) | Protected attachment endpoints                       |
| [tests/](./tests/)                                       | Domain regression, API and permission-boundary tests |
| [migrations/](./migrations/)                             | Ordered database history                             |
| [admin.py](./admin.py)                                   | Django admin registration                            |
| [apps.py](./apps.py)                                     | Django app configuration                             |

## Tests and related code

From the repository root, run `tools/test-backend apps.knowledge_base.tests`.
For a single module, use `tools/test-backend apps.knowledge_base.tests.test_<topic>`.

API routers are assembled in
[adbsoftwaresolutions/ninja/routers.py](../../adbsoftwaresolutions/ninja/routers.py).
Internal browser workflows live in
[the combined Software Solutions application](../../../sites/adb-software-solutions/README.md).

Read the [backend guide](../../README.md) for shared conventions and the
[canonical documentation map](../../../docs/README.md) before domain changes.

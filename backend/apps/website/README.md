# Brand-aware public editorial content

Public blog posts, testimonials, FAQs and portfolio content, plus contact-form entrypoints. Marketing pages remain code-owned; public Portfolio is separate from operational Project.

## Code map

| Location                                                                         | Responsibility                                       |
| -------------------------------------------------------------------------------- | ---------------------------------------------------- |
| [models.py](./models.py)                                                         | Editorial and portfolio records                      |
| [ninja/views.py](./ninja/views.py)                                               | Brand-scoped public content and contact APIs         |
| [ninja/admin_views.py](./ninja/admin_views.py)                                   | Editorial administration                             |
| [ninja/schemas.py](./ninja/schemas.py)                                           | Public and CMS contracts                             |
| [management/commands/seed_marketing.py](./management/commands/seed_marketing.py) | Marketing development fixtures                       |
| [tests/](./tests/)                                                               | Domain regression, API and permission-boundary tests |
| [migrations/](./migrations/)                                                     | Ordered database history                             |
| [admin.py](./admin.py)                                                           | Django admin registration                            |
| [apps.py](./apps.py)                                                             | Django app configuration                             |

## Tests and related code

From the repository root, run `tools/test-backend apps.website.tests`.
For a single module, use `tools/test-backend apps.website.tests.test_<topic>`.

API routers are assembled in
[adbsoftwaresolutions/ninja/routers.py](../../adbsoftwaresolutions/ninja/routers.py).
Internal browser workflows live in
[the combined Software Solutions application](../../../sites/adb-software-solutions/README.md).

Read the [backend guide](../../README.md) for shared conventions and the
[canonical documentation map](../../../docs/README.md) before domain changes.

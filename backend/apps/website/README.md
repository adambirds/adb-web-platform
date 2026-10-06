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

Publication is explicit: Portfolio, Testimonial and FAQ default to drafts, and
BlogPost respects its publish date. `/api/public/collections/{resource}` paginates
published Brand-scoped content with search/category/service filters. The established
array APIs remain available. Admin create/update operations are transactional;
invalid Brand assignments roll back the record rather than leaving partial content.

`ninja/media_views.py` adds capability-protected image upload/removal. It accepts
PNG/JPEG/WebP up to 8 MB and 20 million pixels, strips metadata, resizes to 2400
pixels maximum and saves WebP. Raw SVG/HTML uploads are rejected. Publication and
media editing use existing `website.add_*`/`website.change_*` capabilities.

`import_web_designs_content` reads the ignored WordPress JSON archive and imports
five selected articles and the owner-confirmed recovery case study as drafts.
It never overwrites or publishes existing content; `--dry-run` previews the scope.
Use the admin CMS to approve copy, upload imagery and publish each record.

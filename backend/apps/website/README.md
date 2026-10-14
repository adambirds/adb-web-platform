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

`export_wordpress_content` creates a versioned, self-contained public WordPress
JSON archive with original media bytes and small frontend URL manifests.
`import_wordpress_content` restores every archived post/project as a Brand-scoped
draft without contacting WordPress. Reruns preserve existing records and files;
`--dry-run` validates without writes. Marketing pages are archived for reference.
The old five-article importer has been replaced. See
[the migration archive guide](../../../docs/migrations/README.md) for the exact
export, Git checkpoint, offline import and review commands.

`seed_web_designs_demo` creates a repeatable local Web Designs dataset: 12
published portfolio entries, 12 articles, 3 explicitly fictional testimonials,
10 FAQs and sample website-concept screenshots. It requires `DEBUG=1` and a local database host.
Run `python backend/manage.py seed_web_designs_demo` from the repository root;
`--clear` removes only its reserved demo records and their images, preserving
real content and imported drafts. The entries are published to make the public
preview complete and must be removed before production use of that database.

`seed_public_brand_demo` supplies separate local Software Solutions and Technology
previews: 3 projects, 3 articles, 2 fictional testimonials and 6 FAQs per Brand.
The bundled images are original fictional application/operational workspace
concepts, rather than Web Designs screenshots. It requires `DEBUG=1` and a local
database host, preserves edits on repeat runs and rejects reserved-ID collisions.

```bash
DEBUG=1 python backend/manage.py seed_public_brand_demo
DEBUG=1 python backend/manage.py seed_public_brand_demo --brand software
DEBUG=1 python backend/manage.py seed_public_brand_demo --brand technology --clear
DEBUG=1 python backend/manage.py seed_public_brand_demo --clear
```

Cleanup removes only the selected Brand's reserved `demo-ss-` / `demo-tech-`
records and images. Real content and Web Designs demos are preserved. Remove
these published preview records before using the database for production.

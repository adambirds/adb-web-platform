# Versioned WordPress migration archive

The archive deliberately belongs in Git at
`backend/apps/website/fixtures/wordpress/adb-web-designs.json`, so the backend
Docker image includes it through its existing backend copy step. This directory
contains the runbook. The JSON contains public editorial
content and original image bytes, not credentials, private WordPress settings,
leads or tickets. It is separate from the ignored supplied asset library.

## Before switching off WordPress

Run from the repository root with the normal backend environment available:

```bash
python backend/manage.py export_wordpress_content \
  --url https://adbwebdesigns.co.uk \
  --output backend/apps/website/fixtures/wordpress/adb-web-designs.json \
  --routes-directory sites/adb-web-designs/src/content
```

The exporter:

- Enumerates every page of public posts, pages, projects, categories, tags,
  authors and media; it does not stop at WordPress's 100-record page limit.
- Preserves source HTML, excerpts, original IDs/slugs/dates, SEO metadata and
  public author/taxonomy/media metadata.
- Embeds every media file as base64 with byte count and SHA-256. It prefers the
  original WordPress upload over Optimole-transformed URLs. No live image download
  is needed during import.
- Fails rather than silently creating a partial archive. A failed content/media
  fetch leaves the previous JSON archive intact. Limits are 8 MB per file and
  128 MB total media, and the completed JSON must remain below 90 MB so it can
  be versioned as a single ordinary GitHub file; no WordPress account is required.
- Regenerates small `wordpress-urls.json` and `wordpress-editorial-aliases.json`
  routing files when `--routes-directory` is supplied. Media bytes are never
  imported into a frontend JavaScript bundle.

Pause WordPress publishing while taking the final export. Then inspect the counts,
review the diff and commit the archive **and the two routing JSONs together**:

```bash
git add backend/apps/website/fixtures/wordpress/adb-web-designs.json \
  sites/adb-web-designs/src/content/wordpress-urls.json \
  sites/adb-web-designs/src/content/wordpress-editorial-aliases.json
git commit -m "chore: Refresh the WordPress migration archive."
```

Keep a normal WordPress database/uploads backup for rollback too; this public
export is not a backup of passwords, settings, unpublished WordPress drafts or
private content. The checked-in snapshot from 15 October 2026 contains 14 posts,
two projects, 60 pages, five categories, zero tags, one author and 39 image files.

## Import after WordPress has gone offline

Use the versioned JSON from the deployed revision. Preview the import first:

```bash
python backend/manage.py import_wordpress_content \
  --source backend/apps/website/fixtures/wordpress/adb-web-designs.json \
  --brand adb-web-designs \
  --dry-run
```

Then import into the intended database. For local development:

```bash
python backend/manage.py import_wordpress_content \
  --source backend/apps/website/fixtures/wordpress/adb-web-designs.json \
  --brand adb-web-designs \
  --media-base-url http://localhost:8000
```

Inside the deployed backend container (whose working directory already contains
`manage.py`), use the archive shipped with that image:

```bash
python manage.py import_wordpress_content \
  --source apps/website/fixtures/wordpress/adb-web-designs.json \
  --brand adb-web-designs \
  --media-base-url https://api.adbsoftwaresolutions.co.uk
```

For production, change the media origin to the real publicly accessible backend
or media host, for example `--media-base-url https://api.adbsoftwaresolutions.co.uk`.
If storage already returns absolute public URLs, that flag can be omitted. Use a
stable public origin, not temporary signed URLs. This is the origin that browsers
will use for inline images; it must serve the configured media path over HTTPS.

The importer does not contact WordPress, Optimole or other source image hosts.
It reads the JSON and writes to Django's configured database/media storage; remote
target storage still needs its own normal connectivity and credentials.

All blog and project records are created as **unpublished drafts**, scoped only to
Web Designs. No draft is selected for publication automatically. The importer
restores author, categories/tags, descriptions and featured images, converts
headings/lists/links/code/emphasis to Markdown, strips scripts/iframes/Divi wrapper
shortcodes and rewrites known inline images to restored CMS media. Portfolio body
copy goes into `solution`; `challenge`, `results` and technologies remain blank
rather than being invented. Original project HTML remains in the JSON.

Ordinary WordPress marketing pages, including embedded FAQ/testimonial text, are
archived for reference, not turned into CMS marketing pages or fabricated FAQ/
testimonial records. Those need manual extraction/review. Unused media stays in
the archive; only featured/inline images used by newly imported entries are saved
to CMS storage. Imported raster images are normalized to bounded WebP files with
metadata removed. The original bytes remain in Git.

Reruns skip existing blog/project slugs and preserve edits, publication state,
Brand assignments and images. Existing taxonomies in another Brand stop the
import instead of extending its visibility. Validation/integrity failures write
nothing; database errors roll back newly created records and remove new media
files. A dry run performs validation and collision checks with no database/media
writes. An existing partial draft from the older importer is also preserved;
compare it against this complete archive if you want to restore omitted detail.

## Choose what to publish

Open `/admin/content` in the Software Solutions application. Filter to Web
Designs and drafts; review the blogs and portfolio entries. Update old claims,
prices, links, formatting, project sections and image alternatives before
publishing the entries you want. Discard or leave the others unpublished.

All exported article/project aliases are publication-gated, including articles
previously proposed for retirement. Publishing one makes its old permalink and
numeric ID redirect to its new CMS URL. Keeping it as a draft produces a real 404
on the public website. Publication does not require re-running the importer or
restoring WordPress.

For the wider URL/media/DNS cutover, follow the
[migration runbook](../WEB_DESIGNS_MIGRATION_RUNBOOK.md). This archive preserves
media for offline import; it does not automatically recreate every old
`/wp-content/uploads/...` URL. Preserve useful externally linked media URLs
separately as described there.

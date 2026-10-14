# ADB Web Designs WordPress migration

Audited **15 October 2026**. The live WordPress site remains unchanged. The
replacement is local source code; nothing in this audit switches DNS, deploys
production or publishes CMS content.

## Crawl results and evidence

The crawl fetched the live site's robots file, all seven sitemap files, paginated
public WordPress REST collections and every reachable internal HTML link. It also
checked numeric WordPress IDs, slash/no-slash variants, HTTP/www variants, feeds,
search pagination, attachments and known historic routes. Requests used three
workers, identified themselves as an owner-authorised migration audit and were
read-only. HTML was parsed directly; this was not a JavaScript-rendered crawl.

- **84 unique sitemap page/archive URLs**. Image entries inside the XML repeat
  many times and are not additional pages.
- The public REST API exposes **60 pages, 14 posts, two projects and 39 media
  records**. Some REST records and archives are absent from individual sitemaps.
- **389 distinct URL checks**, plus seven sitemap files: 385 URL checks ended in
  200 and four in 404, after following any redirects; no network errors remained.
- **115 numeric ID links** were checked against live WordPress. All redirect to
  their published permalink or media file; these are real migration entry points.
- **160 referenced/resolved asset URLs** were inventoried: 39 first-party images,
  117 Optimole image URLs and four CleanTalk tracking-pixel variants. All 39
  first-party images were fetched, directly or through attachment redirects;
  external assets were inventoried, not comprehensively downloaded or
  availability-tested. Do not copy tracking pixels into the new content.

The inventory is exhaustive for the published REST objects and the reachable
link graph discovered from these seeds. It cannot prove that there are no old,
unlinked URLs in backlinks, search results or access logs. Before launch, merge
Search Console page/link exports and recent production access-log URLs into the
inventory. No authenticated WordPress content or personal enquiry data was read.

Reviewable evidence:

- [Every checked URL and its migration outcome](WEB_DESIGNS_CRAWL_URLS.csv): 396
  rows including the seven sitemap endpoints; query/slash/host variants stay
  separate. `live_status` is the final response after following redirects;
  `live_redirect_statuses` describes earlier responses.
- [Image and attachment references](WEB_DESIGNS_CRAWL_ASSETS.csv).
- [WordPress numeric IDs and their old permalinks](WEB_DESIGNS_WORDPRESS_IDS.csv).
- [Canonical permalink decisions](WEB_DESIGNS_URL_MIGRATION.json).

Raw HTML, XML, JSON exports, scripts and HTTP check results are retained locally
under `website-assets/web-designs/wordpress-crawl-2026-10-15/`, which is ignored
by Git and Docker. The tracked CSVs retain URLs and metadata, not article bodies.

## What is implemented

The original 84 sitemap URL decisions already existed. This audit extended the
migration to cover legacy sitemap/homepage endpoints and numeric links.

| Outcome                             | Implementation                                                                                                                           |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Keep an existing page               | Keep its permalink and serve the rebuilt page with a self-referencing canonical.                                                         |
| Consolidate a location/service page | Permanent server redirect to the relevant existing regional, country or service page.                                                    |
| Keep an old article or case study   | Redirect only when its exact replacement is published for Web Designs in the CMS; otherwise 404.                                         |
| Remove an article                   | Real 404, with the site's normal navigation and useful recovery links.                                                                   |
| Old WordPress sitemap endpoint      | Permanent redirect directly to `/sitemap.xml`.                                                                                           |
| `/home/` or `/index.php`            | Permanent redirect to `/`.                                                                                                               |
| `/?page_id=…` or `/?p=…`            | Resolve the old ID to the final retained/consolidated page or publication-checked editorial replacement. Retired/unknown IDs return 404. |
| `/?attachment_id=…`                 | Currently 404; asset preservation requires a separate explicit file decision.                                                            |

`sites/adb-web-designs/redirects.json` now contains **58 unconditional rules**.
Next.js `permanent: true` and `permanentRedirect()` return **308**, which is a
permanent server redirect, rather than a WordPress-style 301. Both 301 and 308
are suitable for this migration. The old path and the new path remain on
`https://adbwebdesigns.co.uk`; there is no domain rename.

The ID map is `sites/adb-web-designs/src/content/wordpress-urls.json`; the
homepage guard is `WordPressEntry.ts`. It contains the actual 76 page/post/project
IDs from this crawl. It intentionally does not send unknown IDs or media IDs to
the homepage. Add any other historical IDs discovered in logs/Search Console only
after identifying their original content and replacement.

Examples:

| Old URL                                  | New outcome                                                            |
| ---------------------------------------- | ---------------------------------------------------------------------- |
| `/blackburn-website-design/`             | 308 → `/lancashire-website-design/`                                    |
| `/sydney-website-design/`                | 308 → `/australia-website-design/`                                     |
| `/uk-search-engine-optimisation/`        | 308 → `/services/search-engine-optimisation/`                          |
| `/projects/`                             | 308 → `/portfolio/`                                                    |
| `/?page_id=11387`                        | 308 → `/about/`                                                        |
| `/wordpress-how-to-secure-your-website/` | 308 → its `/blog/…/` replacement only after publication; otherwise 404 |
| `/textzformatter-review/`                | 404; do not send a software-review reader to the homepage              |

Google recommends relevant page-to-page redirects, direct final destinations and
404/410 for removed content without a similar replacement. Blanket redirects to
the homepage can produce soft 404s. See
[Google's URL migration guidance](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes)
and [redirect status guidance](https://developers.google.com/search/docs/crawling-indexing/301-redirects).

## Decisions before cutover

### Selected articles and case studies

All 14 original articles and both projects are now archived for offline draft
import, including the nine previously proposed for retirement. Nothing is
published automatically. Choose which drafts to keep in `/admin/content`; leaving
an article unpublished keeps its old permalink and numeric ID at 404. Publishing
it activates its exact alias automatically. Refresh dated advice before launch.

The existing shortlist (WordPress SEO/benefits/security, freelancer vs agency and
spam prevention) remains a useful starting point, not an import filter. Welcome
to Travel should reflect the confirmed hacked/malware recovery engagement. Both
project bodies import as drafts without invented challenge/results statements.

**Run the final export and commit it before deploying**, because WordPress will
then go offline. The JSON contains original image bytes as well as public source
content; the importer needs only that file and the target database/media storage.
The previous five-article `import_web_designs_content` command has been replaced.
Use the [archive guide](migrations/README.md) for the exact export/import commands,
Git checkpoint, collision behavior and review workflow.

### Media, feeds and archives

The 39 attachment records and their 39 resolved first-party image files are not
migrated by the page redirect table. Some files are WordPress-scaled variants.
For images used by retained articles/case studies, or with useful external links:

1. Preserve the old `/wp-content/uploads/...` URL in the new site's `public/`
   directory or a persistent media origin; alternatively redirect it to an
   equivalent deployed image.
2. For an old attachment page or attachment ID, redirect directly to that final
   image URL. Avoid a chain through the old attachment permalink.
3. Preserve or redirect any linked resized variants explicitly. Changing the
   parent page does not automatically redirect its image URL.
4. For unwanted/unreferenced images, keep a deliberate 404. Do not redirect an
   image URL to an HTML homepage or portfolio index.

The offline archive now preserves all 39 original files in Git. Draft import
restores featured/inline images to CMS storage, but does not recreate their old
WordPress upload URLs automatically. These legacy media rows
are explicitly marked `review_media` in the CSV and remain a pre-launch decision.
Optimole-hosted URLs cannot be controlled by a redirect on this domain; replace
those references in migrated content with images hosted under your control.

Old RSS/comment feeds, search pagination and additional paginated author/category
archives currently return 404. The new site does not have RSS or an equivalent
site-wide search. Keep them retired unless traffic/subscriber evidence warrants
building an equivalent. Do not blindly redirect old `/blog/page/2/` to a new page
number: the article selection and page sizes have changed.

One old testimonial detail URL already redirects to the WordPress homepage. The
new site returns 404 for it. If the actual approved testimonial is retained,
redirect it to `/testimonials/` only after verifying the quote exists there.

## Production cutover

1. **Capture a rollback backup.** Export the WordPress database and uploads;
   retain the old deployment, DNS values and TLS configuration. The public crawl
   is evidence, not a backup of private WordPress settings/data.
2. **Complete content and file decisions.** Publish only reviewed CMS content;
   remove local demo entries; resolve retained media URLs and any important URLs
   found in Search Console/access logs. Check portfolio, testimonial and FAQ
   collections have real content, not local fixtures.
3. **Prepare production hosting.** Deploy the Web Designs Next.js application
   with the redirect table and ID map in the build. Configure backend/API/media
   access and public forms. Ensure your CDN/proxy forwards legacy paths and query
   strings to Next.js instead of serving a generic SPA fallback or cached page.
4. **Keep all host variants working.** Provision TLS for both `adbwebdesigns.co.uk`
   and `www.adbwebdesigns.co.uk`. Keep HTTP→HTTPS and www→non-www permanent
   redirects at ingress. Preserve query strings so WordPress IDs reach the guard.
   Existing live host variants passed the audit; reproduce that behavior on the
   new ingress. No provider-specific ingress configuration is assumed here.
5. **Test before switching DNS.** Use the production deployment/host override to
   request every old path, query variant and destination. Check 301/308 + `Location`,
   final 200, canonical metadata, 404s, sitemap and forms. Redirect straight to
   the final destination; avoid loops and unnecessary chains. Do not expect the
   local dev server to reload a required JSON redirect table without restarting.
6. **Keep staging out of search.** Restrict staging with authentication where
   possible. Remove staging-only `noindex`/crawl blocks before the public launch.
   Keep your Search Console domain verification DNS record, or preserve the
   verification file/meta tag if that is how ownership was verified.
7. **Switch the existing domain to the new deployment.** Plan a low DNS TTL ahead
   of time and account for cache propagation. Verify contact submission creates
   the correct Web Designs lead/ticket before considering the cutover complete.
8. **Refresh Search Console.** Submit `https://adbwebdesigns.co.uk/sitemap.xml`,
   remove obsolete sitemap submissions, inspect important old/new URLs and
   monitor indexing/redirect errors. A Change of Address request is unnecessary:
   the domain is unchanged. Keep old permalink redirects for at least a year,
   preferably indefinitely where they remain useful, as
   [Google recommends](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes).
9. **Watch and rollback if necessary.** Check 404 logs, request failures,
   indexing and traffic after launch; add mappings only for genuinely equivalent
   content. Roll back DNS/deployment if critical pages/forms fail. Do not shut
   down the old hosting until propagation and rollback checks are complete.

## Validation performed

The subsequent offline workflow is covered by backend tests, including an import
of the real versioned snapshot with source network requests disabled. The snapshot
contains 14 articles and two projects. All remain drafts until manual publication.

- Existing live site: 389 URL checks and seven sitemap fetches; all discovered
  public objects were enumerated. Four genuine 404s: Cloudflare's email-protection
  route, `/index.php/feed/` and two deliberately nonexistent ID probes.
- Replacement: **177 permalink/endpoint checks**: 106 permanent redirects,
  29 retained-page responses and 42 intended retired/unpublished 404s.
- Replacement: **117 numeric-ID checks**: 60 direct permanent redirects and
  57 intended retired/unpublished/attachment/unknown-ID 404s; no mismatches.
- Web Designs tests: **36 passed**, including ID resolution, publication gating,
  malformed IDs, retained routes, redirects and destination-chain checks.

HTTP checks used a temporary isolated Next.js dev instance with the updated
configuration; the user's existing server was not restarted. They establish
local behavior, not production ingress/CDN configuration. An HTTP crawl also
does not validate rendered JavaScript, visual layout or analytics behavior.

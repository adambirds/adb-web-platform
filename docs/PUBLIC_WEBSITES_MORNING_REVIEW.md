# Public websites: morning review

Implementation work started on 6 October 2026. No commits or deployments are
being made. This records assumptions to review rather than interrupting overnight
work. Validation results and final implementation notes will be added below.

## Decisions to confirm

1. **Broader software consultancy:** not advertised at launch. The confirmed
   AI-built app/code review offer includes scoped technical findings; a wider
   advisory service can be added later if wanted.
2. **Working arrangements:** project scope and schedules are agreed individually.
   Hosting and maintenance are offered, but no hours, fixed prices, emergency
   cover, guaranteed response times or full-time availability are invented.
3. **Legal/policy copy:** controller/trading details, contact/address requirements,
   retention periods, actual infrastructure processors and any international
   transfer arrangements need review. Policy routes will be implemented with
   editable copy and excluded from indexing until approved. No cookie analytics,
   advertising trackers, external fonts or third-party embeds are being added.
4. **Existing CMS content:** newly created portfolio/testimonial/FAQ entries are
   drafts until explicitly published, just like blog posts. Existing entries also
   need publication review before the new public sites display them.
5. **Old Web Designs content:** useful original project/article content can be
   imported as editable CMS drafts. Unsupported claims, old pricing, old phone
   numbers and direct email details must not be carried over. Welcome to Travel's
   hacked/malware-infected starting situation is confirmed; do not invent recovery
   metrics or technical attack details.
6. **International pages:** describe remote work from Manchester. Do not infer
   that every international Web Designs client is also a software/DevOps client.
7. **Redirects:** redirect related old content to a relevant existing destination.
   If there is no meaningful replacement, retain a proper not-found/retired
   response instead of redirecting unrelated posts to a sales page.
8. **Public social imagery:** exact supplied logos with code-drawn brand artwork
   are preferable here to generating new photography or approximating the logos.
   Generated images can still be added for editorial subjects when useful.

## Implementation and validation

All three public sites are implemented with distinct homepages, 19 confirmed
service pages, individually written location/country pages, contact/thank-you,
About/working arrangements, policy routes and server-rendered CMS collections
and detail pages. Marketing copy lives in each site's `src/content/site.ts` and
`home.ts`; editorial content is managed in `/admin/content`.

CMS additions include explicit draft/published state for portfolio, testimonials
and FAQs; service associations; image alternative text; portfolio search copy;
scheduled blog publication; and protected upload/removal of normalized images.
The generated migration has been applied locally. Existing publication state
needs review because portfolio/testimonial/FAQ now default to drafts.

Five original Web Designs articles and the confirmed Welcome to Travel recovery
case study were imported as drafts. The importer skips existing records, and its
second run confirmed idempotency. The old Budget Girl URL is a conditional alias:
it returns 404 until an approved case study is created and published. No sample
projects, testimonial clients, ratings or performance metrics were invented.

The 84 old WordPress URLs have explicit decisions in the migration ledger.
Forty-eight relevant permanent redirects were checked with and without trailing
slashes (96 requests), with correct single-hop 308 destinations. Retired articles
and unpublished editorial aliases return actual 404s.

Production routing supports `API_INTERNAL_URL` for frontend SSR/contact calls,
`INTERNAL_API_HOSTS` for exact backend private hostnames and `PUBLIC_MEDIA_URL`
for publicly reachable image URLs. All are documented in the root README and
environment example. Backend media requires persistent storage and public HTTPS
routing. No additional Redis service is required. Each Brand needs an enabled
Ticket Queue before launch; its sales Shared Mailbox is needed for Graph replies.

Verification completed:

- Production builds for all three Next.js apps, including Software `/admin`.
- A real Chromium crawl of 77 code-owned/collection pages: HTTP status, one H1,
  canonical/description/Open Graph/schema, desktop/mobile overflow, theme
  persistence, menu closing, form failure/retry and thank-you navigation.
- Populated CMS browser checks using isolated fixtures: featured project switching,
  article/project details, safe Markdown, FAQ/testimonials, search, pagination,
  invalid-page 404s and populated sitemaps. Fixtures never touched the local database.
- Backend website/contact-ticket tests, including publication, Brand isolation,
  permissions, private-host media URLs, image limits and enquiry throttling.
- Frontend public transport/navigation tests and the existing Software regression suite.
- Required repository lint, strict Python typing and shared CSS checks.

Final results: **38 backend tests**, **195 Software frontend regression tests**
and **16 public transport/navigation tests** passed. All three production builds,
repository lint, explicit shared-source ESLint, shared CSS validation and migration
consistency checks passed. The final crawl reported **77 pages and 96 redirect
requests with zero failures**; populated CMS fixture checks also passed.

Production has not been deployed. The browser form tests
intercepted submission responses; the Django integration tests exercised actual
Lead/Ticket creation in the test database, without adding test enquiries to your
local working data.

To preview locally, run Django normally, then the site's `dev` command from the
root README (Software 3000, Web Designs 3002, Technology 3003). Verification used
separate temporary ports and did not replace your own servers. Preview screenshots
are saved in the ignored `website-mockup/production-preview/` folder.

Before launch, review the policy/trading information and all imported drafts,
approve service wording and confirm whether the unadvertised broader consultancy
service should remain excluded. The websites can be previewed and edited now.

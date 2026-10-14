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

## Policy and retention decisions — 6 October 2026

Web Designs policies now describe Adam Birds trading as ADB Web Designs, contact
through a form, DigitalOcean London hosting, intended launch GA4 statistics
enabled by default, and 36-month unsuccessful enquiry review with mandatory
approval. Earlier notes about absent analytics or permanent enquiries are
superseded. Cookies/preferences controls are implemented on privacy and cookie
pages. Set the measurement ID and complete the root README Google setup before
launch. No address is published, as requested; business correspondence/address
requirements remain a launch review item. Confirm Google contractual/UK transfer
arrangements and Microsoft 365 data locations rather than assuming all providers
process data only in London. Mailbox copies/backups need separate retention.

## Software Solutions and Technology — 14 October 2026

The approved Web Designs design, full policies and statistics controls now cover
both brands. Their content follows the agreed service inventory; no contracting,
core-hours support or unconfirmed consultancy has been introduced. About and
location copy are rewritten for each business.

Assumptions carried from the shared platform: Adam Birds is the operator, privacy
contact uses the form, hosting is DigitalOcean London, and unsuccessful enquiry
retention is 36 months with manual approval. No address is published. Confirm
correspondence/address requirements and provider processing/transfer arrangements
before launch. Configure separate GA4 properties/IDs and statistics-only settings
using the root README. No external Google settings or real data were changed.
Software's additional authenticated-cookie/operations wording is included.
No fake portfolio or client feedback has been published for either new Brand.

Verification for the family rollout: all three isolated production builds,
206 Software frontend tests, 23 Web Designs frontend tests, 8 Technology
frontend tests and 35 backend website tests passed. A Chromium crawl checked
231 page renders across desktop/390px/320px, with no runtime, canonical, heading
or overflow failures. It also checked social images, dark/light persistence,
and analytics/theme-storage opt-outs. Browser analytics used local tag stubs
and test IDs; no statistics were sent to Google. Captures are in the ignored
`website-mockup/brand-family-review/` directory.

Final interaction checks also passed for all three mobile menus and contact-form
failure/retry/thank-you journeys. Form responses were intercepted, so no test
enquiries were stored in the local database. The Software production admin
render excluded the public measurement ID. Temporary preview servers are stopped;
the owner's existing development servers on 3000/3002/3003 are untouched.

## Editorial previews and copy follow-up

Removed public full-time employment wording and put the current Brand first in
related-business About paragraphs. Homepages now include a Brand-scoped FAQ
preview as well as portfolio, articles and testimonials. Software/Technology
collections were empty; at the owner's request, clearly labelled fictional
records have been added to the local CMS with a removable guarded seed command.
Web Designs already had published previews and continues using its own records.
The seed is documented in the website app README; remove demos before launch.

Follow-up verification passed: 48 populated homepage/About/editorial/list/detail
page checks on desktop and mobile, including all four CMS sections, links and
project images; all three production builds; the website backend suite, guarded
seed cleanup tests, public navigation tests, typing and repository lint. Local
Software and Technology records remain editable through `/admin/content`.

## Follow-up checkpoint

The owner requested focused local commits for the completed Software/Technology
rollout, shared design/privacy components, CMS previews and obsolete admin URL
configuration cleanup. Production deployment remains a separate step.

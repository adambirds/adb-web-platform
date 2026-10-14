## Public website editing

Run `pnpm --dir sites/adb-web-designs dev` from the repository root (port 3002).
Edit `src/content/site.ts` for services, locations, About, policies and contact copy;
edit `src/content/home.ts` for homepage text and `src/content/page-design.ts`
for inner-page labels and introductions. Homepage copy is grouped by visible
section (`hero`, `services`, `about`, `journal`, `testimonials`, `contact`, `work`).
`workFallback` is used only when there are no published CMS projects. Project
names, images and descriptions, article previews and quotes come from the CMS. The approved homepage composition lives in
`src/components/public/HomePage.tsx`; `WebPages.tsx` carries its typography, cyan
sections and numbered layouts through services, locations, About, contact, policies
and CMS pages. Brand styling lives in `src/styles/public.css`.

Blog, portfolio, testimonials and FAQs are published through `/admin/content` in
the Software operations app. Assign this Brand explicitly, save a draft, upload
images from its edit form and publish after review. Empty collections are hidden
from navigation and sitemaps. Public requests use the shared backend; configure
`API_INTERNAL_URL` at runtime if a private server-to-server origin is needed.

See the root README public setup guide and `docs/PUBLIC_WEBSITES_MORNING_REVIEW.md`
for launch assumptions, policy review and validation.

## Local demo content

The local CMS has a removable Web Designs preview dataset: 12 projects, 12
articles, 3 testimonials and 10 FAQs, with original fictional website screenshots. All
entries are explicitly marked as fictional demos and published for local previews.
They can also be edited in `/admin/content`.

From the repository root, with the backend Python environment active:

```bash
DEBUG=1 python backend/manage.py seed_web_designs_demo
# Explicitly replace existing demo covers with the bundled website concepts:
DEBUG=1 python backend/manage.py seed_web_designs_demo --refresh-images
DEBUG=1 python backend/manage.py seed_web_designs_demo --clear
```

Seeding is repeatable and skips existing entries. Cleanup removes only the
command’s reserved `demo-wd-` / `Demo WD / ` entries and their images, preserving
real content and imported drafts. The command requires Django debug mode and a
local development database host. Clear demo content before using this database
for a production launch; it is not client work or an endorsement.

Demo image sources are native HTML/CSS in
`backend/apps/website/fixtures/web_designs_demo/concept.html`. The bundled PNG
screenshots populate the actual CMS image fields; they are not a second
frontend-only portfolio. Normal seed runs preserve image edits;
`--refresh-images` deliberately replaces the reserved demo images only.

## Policies and usage statistics

Edit `src/content/policies.ts` for privacy, cookie and website terms text, business
facts and the update date. Privacy enquiries use the contact form. Privacy and
cookie pages include working analytics and theme-storage controls. Set runtime
`GA4_WEB_DESIGNS_MEASUREMENT_ID` to enable normal GA4 statistics; no Google script
is loaded without a valid ID. See the root README for Google account settings.
Unsuccessful enquiries are reviewed after 36 months and require manual deletion
approval; [the retention guide](../../docs/LEAD_RETENTION.md) explains the scope.

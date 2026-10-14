## Public website editing

Run `pnpm --dir sites/adb-technology dev` from the repository root (port 3003).
Edit `src/content/site.ts` for services, locations, About and contact copy;
edit `src/content/home.ts` for homepage text. The homepage layout/artwork lives in
`src/components/public/HomePage.tsx` and brand styling in `src/styles/public.css`.

Blog, portfolio, testimonials and FAQs are published through `/admin/content` in
the Software operations app. Assign this Brand explicitly, save a draft, upload
images from its edit form and publish after review. Empty collections are hidden
from navigation and sitemaps. Public requests use the shared backend; configure
`API_INTERNAL_URL` at runtime if a private server-to-server origin is needed.

See the root README public setup guide and `docs/PUBLIC_WEBSITES_MORNING_REVIEW.md`
for launch assumptions, policy review and validation.

## Shared public design, policies and analytics

The approved Web Designs design is carried through public homepages, services,
areas, About, contact, editorial collections/detail pages, thank-you and 404.
`src/content/page-design.ts` supplies inner-page labels; `src/content/policies.ts`
supplies operator/hosting/retention facts and Brand-specific service wording.
Shared numbered layouts and policy renderers are in `packages/ui/src/public`;
`family.css` supplies the common styling. Homepage copy and composition stay local.

Privacy and cookie pages offer working analytics and theme-storage preferences.
Set `GA4_TECHNOLOGY_MEASUREMENT_ID` at runtime to enable the
brand's statistics. Without a valid ID, no Google script loads. See the root README
for each Google property’s statistics-only configuration and launch checks.
The public layout reads runtime configuration after the request boundary;
analytics is not part of authenticated operations or account/security flows.

Main content is code-owned; editorial entries remain Brand-scoped in the CMS.
No Web Designs demo records are copied into this Brand's portfolio. The common
unsuccessful-enquiry policy is 36 months with manual deletion approval, documented
in `docs/LEAD_RETENTION.md`. Review correspondence/address and external processing
arrangements before launch; no production deployment is part of this change.

## Local editorial preview records

The local CMS now has 3 fictional projects, 3 sample articles, 2 explicitly
fictional testimonials and 6 FAQs for this Brand, including original application
concept images. These are actual editable CMS records, not frontend-only data.
Homepages show four FAQ previews and link to the full collection.

Run `DEBUG=1 python backend/manage.py seed_public_brand_demo --brand technology`
from the repository root to recreate the previews. Add `--clear` to remove only
this Brand's reserved demo entries and images. Seeding preserves existing edits
and rejects production/non-local configuration. Remove demos before launch.

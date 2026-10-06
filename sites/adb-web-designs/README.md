## Public website editing

Run `pnpm --dir sites/adb-web-designs dev` from the repository root (port 3002).
Edit `src/content/site.ts` for services, locations, About, policies and contact copy;
edit `src/content/home.ts` for homepage text. The homepage layout/artwork lives in
`src/components/public/HomePage.tsx` and brand styling in `src/styles/public.css`.

Blog, portfolio, testimonials and FAQs are published through `/admin/content` in
the Software operations app. Assign this Brand explicitly, save a draft, upload
images from its edit form and publish after review. Empty collections are hidden
from navigation and sitemaps. Public requests use the shared backend; configure
`API_INTERNAL_URL` at runtime if a private server-to-server origin is needed.

See the root README public setup guide and `docs/PUBLIC_WEBSITES_MORNING_REVIEW.md`
for launch assumptions, policy review and validation.

# Public website rebuild

This records the confirmed public-site direction from 6 October 2026. It updates
the earlier independent-brand direction: the sites should visibly belong to the
same ADB family while retaining different page compositions and service messaging.

## Confirmed decisions

- ADB Web Designs replaces the existing WordPress site at
  `https://adbwebdesigns.co.uk`. Its old URLs require an explicit migration or
  permanent redirect decision before launch.
- Software Solutions and Technology are new public websites.
- All three sites default to dark mode with cyan accents. A header theme switch
  offers light mode and remembers the visitor's preference. Internal operations
  remain dark-only.
- Shared typography, navigation conventions and visual details establish the
  family relationship; homepage layouts, imagery and copy distinguish each site.
- Position Adam's work as freelance, using direct first-person copy rather than
  implying an agency or a large team. Avoid generic slogans and unsupported claims.
- Manchester is the confirmed location. Do not display phone numbers or direct
  email contact details; enquiries use contact forms.
- Each site supports services, about, contact, portfolio, blog, testimonials and
  FAQs. Editorial content remains brand-scoped and editable through the existing
  administration CMS. Public portfolio is separate from operational Projects.
- Contact forms identify Brand and use the existing Django Lead/Ticket ingestion.
- Marketing copy belongs in clearly named local content files, separate from
  rendering components. CMS content remains editable in administration.
- Link to related ADB brands in the footer and at relevant service boundaries.
- Use the supplied Technology logo; it replaces the earlier temporary Software
  Solutions logo instruction.
- Retain a smaller, useful set of local service pages and international market
  pages. Rebuild their content around actual customer needs rather than changing
  the location name in one template.
- Use the image-generation tool where it improves social-share/editorial imagery.
  Branded social images should include the correct supplied logo and fit each
  page's subject and the site's visual identity.

## Page inventory and revised availability

See [the proposed page/service inventory](PUBLIC_WEBSITE_PAGE_INVENTORY.md) for
all shared routes, brand-specific service pages, area pages and content sources.
The page and service lists are a review proposal, not a final approved catalogue.

The preferred visual direction is the third temporary design study: three
business websites with distinct compositions and an ADB family identity. These
are freelance businesses, not personal portfolio websites. The production sites
will be multi-page; homepage sections introduce and link to substantial pages.

Adam now has a full-time platform engineer role. Remove contracting, embedded
team/staff-augmentation offers and full-time availability from public copy.
Hosting and maintenance are confirmed services; agree their operational scope
and schedules before publishing specific commitments. This changes marketing availability, not the
platform's operational Project or future commercial Contract models.

## Confirmed service scope

- Web Designs: design/development using Next.js, WordPress, Shopify or Squarespace;
  ecommerce; website hosting and maintenance; technical SEO and local SEO.
- Website rescue explicitly includes hacked and malware-infected site recovery,
  cleanup/restoration and security improvements. Welcome to Travel's engagement
  started with a hacked/malware-infected website, as confirmed by the user; the
  CMS case study must describe the recovery work actually delivered.
- Software Solutions: applications, APIs/integrations, automation, mobile apps
  and code reviews for AI-built/vibe-coded projects.
  Software consultancy remains a proposed bounded advisory service pending a
  decision; contracting/staff augmentation remains excluded.
- Technology: cloud/DevOps, infrastructure, migrations, building deployment
  pipelines, server management, server rebuilds and app deployment/security
  hardening (including AI-built apps). Code review and remediation belongs with
  Software Solutions; deployment/infrastructure belongs with Technology.
  Do not promise core-hours
  technical support, emergency response or 24/7 managed operations.
- Copywriting, social media management and broader marketing campaigns are not
  part of the Web Designs offer. Service schedules, prices and commitments must
  reflect separately agreed arrangements.

## Local asset library

`website-assets/` is ignored by Git and Docker. It currently retains 112 supplied
files, including two macOS metadata files, with original filenames and source
formats preserved. The manifest records SHA-256 hashes, dimensions and inspection
notes; all moved-file hashes have been verified.

- `web-designs/logos/`: original Web Designs logo variants and design sources.
- `web-designs/images/`: portrait, old-site photography, portfolio and blog images.
- `web-designs/wordpress-snapshot/`: public sitemap and REST content snapshots.
- `software-solutions/Logos/ADB Software Solutions/`: Software Solutions logos.
- `technology/logos/`: Technology outlined SVGs, transparent PNGs, PDFs and source.
- `asset-manifest.json`: file inventory and inspection results.

Raster images, SVGs and PDF-compatible Illustrator files have visual previews.
EPS sources were inspected through headers/metadata and available previews, with
their corresponding Illustrator/SVG/PNG versions reviewed. The Affinity source
is retained alongside matching exported images. Do not deploy source design files,
macOS metadata, obsolete screenshots or entire upload directories.

Keep originals in this library. Copy selected deployment files into the relevant
site's `public/` directory with descriptive filenames. Prefer outlined SVGs for
logos and appropriate optimised raster exports for photography. The Technology
folder's README identifies the editable font-dependent source and deployment
variants; use the outlined variants in the website.

## Social-share imagery

Create polished brand-specific Open Graph/Twitter images and relevant page-level
variants. Use image generation when suitable for the image or background, with
the supplied logo as a reference when the image includes it. Inspect the result
for logo accuracy, readable text, adequate contrast and cropping before use.
Do not substitute a generated approximation for the supplied logo. Exact logo
and text placement can also use deterministic code-based composition with a
generated background when this gives a more reliable result.

Keep imagery aligned with the shared navy/cyan identity, with differences that
reflect each brand's services. Avoid generic futuristic imagery, fabricated
project screenshots or invented client branding. Use a 1200 × 630 social image
as the normal starting point; keep critical logo/text comfortably within crop-safe
margins. Add image metadata and alt text, and provide a useful brand fallback
when a CMS entry has no custom social image. Selected final assets belong in each
site's `public/`; preserve references and source outputs in the ignored library.

## Local and international service pages

Manchester remains the actual base. The initial retained local set is Manchester,
Salford, Wigan, Lancashire and Greater Manchester, with a UK-wide page for remote
work beyond nearby areas. These represent areas served, not additional offices or
separate business addresses. Further towns should earn their own page through
useful distinct content rather than a location-name substitution.

Retain Australia and USA pages to support the real international client base.
Describe working remotely with a Manchester-based freelancer: asynchronous
communication, agreeing meeting times across time zones, practical handovers and
ongoing support arrangements. Do not claim Australian/American residency, offices
or local status, or promise working hours, response times or local currency terms
that have not been agreed. Existing city/state pages can consolidate into those
country pages unless there is a strong reason and enough useful material to
retain them separately.

Each retained page needs its own purpose and copy, relevant services, clear
working arrangements and useful FAQs. Reference genuine relevant CMS projects or
testimonials where available; never invent local clients or results. Share layout
primitives, not identical location copy. Link pages naturally from service and
coverage navigation, and ensure they offer more than a route to the same contact
form. Do not mass-produce thin pages for every place name.

Use location-specific metadata and self-canonical URLs for retained pages. Schema
must distinguish the actual Manchester base from areas served. A local office
address or branch entity must not be invented for any service area. UK/Australia/
USA pages can all be English-language service content; do not add hreflang purely
because a location appears in the URL. Introduce regional/language alternates
only when pages are actually equivalent regional/language versions.

See Google's [doorway-abuse guidance](https://developers.google.com/search/docs/essentials/spam-policies#doorway-abuse)
and [international-site guidance](https://developers.google.com/search/docs/specialty/international/managing-multi-regional-sites).

## SEO and migration

Server-render meaningful public content. Provide page-specific titles,
descriptions, canonical URLs, Open Graph/Twitter images, robots rules, XML
sitemaps and appropriate structured data. Structured data must match visible
content; do not invent ratings, reviews, service locations or project outcomes.
Keep `/admin` and authentication/security pages excluded from indexing even when
Software Solutions public routes become indexable.

The live WordPress sitemap inventory contains 84 URLs: 59 pages, 14 articles plus
the blog index, two project detail pages plus their index, five categories, one
project category and one author archive. Nested image URLs are excluded from
these counts.

See [the implemented URL map](WEB_DESIGNS_URL_MIGRATION.json). Relevant static
redirects are active in Web Designs; editorial aliases activate only once their
replacement CMS records are published. The user permits selective retirement and does
not require a complete blog import. Initial candidates for refreshed CMS articles
cover WordPress security, spam prevention, CMS benefits, SEO and choosing a
freelancer. Preserve the two real project records if their content remains useful.
Final copy must be reviewed before publishing; do not carry old prices or stale
claims into new pages automatically.

Keep the useful local/country pages above and rewrite their content. Consolidate
other location pages into the closest relevant retained area or country page;
retired datestamped articles without meaningful replacements return a real 404.
Preserve useful detail pages through CMS entries and permanent redirects
when paths change. Category destinations must offer corresponding filtering or
content. Verify every destination exists, the redirect has one hop, internal
links use canonical paths and obsolete URLs stay out of the new sitemap. Avoid
blanket redirects to the homepage.

## Implementation sequence

1. Inspect and organise assets; audit old URLs and confirm positioning/theme.
2. Build the public layout boundaries, accessible navigation and theme switch.
3. Create each brand's editable copy and distinct homepage/service layouts,
   including purposeful local and international service pages.
4. Connect CMS listing/detail pages and contact forms to scoped backend APIs.
5. Add metadata, structured data, social images, sitemap and robots behavior.
6. Prepare selected CMS migrations and activate verified permanent redirects.
7. Check desktop/mobile layouts, both themes, keyboard navigation, form behavior,
   brand isolation, indexing boundaries and production builds for all three sites.

Site implementation and verified static redirects are complete. Five selected
original articles and the confirmed Welcome to Travel recovery case study are
editable CMS drafts. Publication and production cutover require the owner review
recorded in `PUBLIC_WEBSITES_MORNING_REVIEW.md`; no deployment or commit has been made.

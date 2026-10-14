# Public website design reference review

Reviewed on 6 October 2026 following the user's feedback that the implemented
designs still feel generic. This is a proposed visual direction, not approval of
new copy, services or a replacement implementation. The existing commercial,
CMS, SEO and freelance-business requirements remain in force.

## Review evidence

Read all five reference homepages. Inspected desktop and mobile browser captures
of Shape, Fhoke, Atomic Object and Thoughtbot, including sections below the hero.
Also opened Fhoke's website-design service page and Thoughtbot's Harvard Business
Review case study. Superrb's live browser view returned a security challenge on
both host variants; its public content was readable through the web reader.
Atomic Object's hero contained a blocked embedded-media message, so the video
experience could not be assessed reliably. Local research captures are temporary
files under `/tmp/adb-reference-review/`, not deployment assets.

## Reference observations and useful lessons

### [MadeByShape](https://madebyshape.co.uk/)

Large, relatively light-weight typography sits inside a shaped composition with
moving project imagery. Below the introduction, staggered project images dominate
the page. Small labels and restrained navigation leave the work space to speak.
The mobile composition retains its character rather than becoming a stack of
unrelated cards. Useful lesson: build the page around work and deliberate image
placement, with a recognisable relationship between text and media.

### [Fhoke](https://www.fhoke.com/)

Condensed display type establishes a strong identity before any project appears.
The homepage then switches into broad project sections with different colours,
large imagery and short descriptions. Its
[website-design page](https://www.fhoke.com/services/website-design/) carries the
same typography into a substantial service introduction. Useful lesson: type,
scale and section rhythm can create distinction without elaborate decorations.

### [Superrb](https://www.superrb.com/)

The accessible content puts storytelling at the centre of the proposition and
gives individual projects distinct descriptions. The homepage moves from this
positioning into work and service explanations. Useful lesson: establish a
coherent idea and make the work demonstrate it. Its live animation and visual
layout still need direct inspection; do not treat third-party gallery images as
evidence of the current design.

### [Atomic Object](https://atomicobject.com/)

The visible homepage uses a clear software-development proposition, generous
spacing, contrasting dark and light sections, photography and client products.
It connects the offering to business needs and explains the working relationship.
Useful lesson: expertise becomes credible through concrete explanation and proof,
rather than decorative technical symbols.

### [Thoughtbot](https://thoughtbot.com/)

Warm dark backgrounds, a distinct combination of text styles, staff portraits
and a large featured product demonstration establish both people and technical
work. The featured case connects product imagery, the engagement and a client's
account of the result. Its
[HBR case study](https://thoughtbot.com/case-studies/HBR-new-mobile-app) provides
a dedicated place to explain the project. Useful lesson: show how software helps
someone and explain the delivery decisions alongside the product.

## Diagnosis of the current ADB designs

The current compositions differ, but their typography, dark surfaces and cyan
emphasis still produce a similar overall rhythm. With no published CMS projects,
the large generic illustration becomes the main visual evidence. Long service
lists then repeat a heading, description and link at roughly the same weight.
The result has little variation between the introduction, services and business
story. The shared inner-page presentation makes the brands feel even closer.

Changing accent colours or adding more animation would not resolve this. The
next design study should establish typography, real media, composition and page
hierarchy together.

## Proposed ADB direction

### Web Designs

Use a more expressive display face and a composition built around substantial
website imagery. Alternate large project features with quieter explanatory
sections. Give website rescue its own visual story: the problem, the recovery
work and the restored website. Welcome to Travel is the confirmed engagement;
only approved CMS content should supply public project claims. Hosting,
maintenance and technical/local SEO remain substantial service pages.

### Software Solutions

Use product-oriented compositions: legible interface detail, annotated workflows
and an explanation of the problem being solved. Give applications, integrations,
automation and mobile work different visual treatments. Any demonstration made
for the design must be labelled as illustrative, not presented as client work.
Explain code review through concrete review concerns and the delivery process.

### Technology

Use precise layouts, selective monospace labels and diagrams that explain actual
deployment or migration concepts. Give cloud, pipelines and server work distinct
sections. Avoid simulated monitoring dashboards or success statistics that imply
operational evidence. Keep the agreed limits on support availability explicit in
service copy.

### Family identity and full-page scope

Retain the supplied logos, dark default, cyan accent, theme switch and related
brand links. Vary the display typography, imagery, spacing and composition by
brand. Carry each identity through homepage, services, service detail, about,
contact, editorial collections and case studies. Preserve semantic headings,
readable contrast, reduced-motion behaviour, responsive navigation and existing
SEO/redirects.

## Next reviewable deliverable

Create a revised study in the ignored `website-mockup/` directory covering a
homepage and service-detail page for each brand, with at least one representative
case-study composition. Show desktop, mobile and light-mode treatments. Include
the empty-CMS state deliberately: the design must feel complete before projects
and testimonials are published. Use supplied ADB assets and original compositions;
reference-site imagery, slogans and distinctive artwork are not ADB assets.

This review changes the proposed visual direction. It does not approve prices,
availability, additional services, fabricated evidence or publication of drafts.

## First implementation pass after the checkpoint

The complete initial website/CMS implementation is saved in commit `e74c153`
(`feat: Build three public brand websites and publishing workflows.`). The user
explicitly authorised this checkpoint before beginning the redesign.

The subsequent redesign runs in the three existing apps:

- Web Designs uses Archivo Black display typography, offset headline alignment,
  a full-width image/story feature and a larger introduction with Adam's portrait.
- Software Solutions uses DM Sans, serif emphasis and an explicitly illustrative
  business workflow. It is not presented as delivered client work.
- Technology uses Space Grotesk, monospace labels and an explicitly labelled
  reference release flow linking into the relevant services.
- Typography and brand styling also carry through service, about, contact and CMS
  pages. Dark/light themes and the existing route/SEO contracts are retained.
- Fonts are served locally, with their upstream Open Font License files included.
  The new homepage text remains in each brand's `src/content/home.ts`.

**Image assumption for review:** when Web Designs has no published CMS projects,
its feature uses the supplied Welcome to Travel mockup and the previously
confirmed hacked/malware-infected starting situation. This is a code-owned service
example linking to website rescue, not publication of the CMS draft case study.
No draft case-study body, recovery metrics or attack details are exposed.
Published CMS projects replace that fallback and retain selectable project controls.

Desktop/mobile and light-mode captures are available locally in the ignored
`website-mockup/redesign-preview/` directory. These are review artifacts; the
implementation is in the actual apps. This pass is ready for visual feedback,
not a declaration that the user has approved the new design.

Validation for this pass includes all three production builds; the 18 public-site
and featured-project tests; an actual browser crawl of 77 pages and 96 permanent
redirect requests; populated CMS fixture checks; desktop, 390px and 320px checks
of home/service/about/contact pages; fonts, images and theme switching; and
explicit ESLint, Stylelint, formatting and repository lint checks. No backend
model, migration, API or operational workflow was changed by the redesign.

## Approved Web Designs direction: whole-site rollout

The user approved the redesigned Web Designs homepage and asked to carry that
look through the whole site before revisiting Software Solutions and Technology.
Web Designs now uses local page compositions for the service directory, individual
services, location pages, About, working arrangements, contact, policies, CMS
collections and detail pages, thank-you and 404. The homepage remains the reference:
Archivo display type, dark/white contrast, cyan scope bands, numbered sections,
large imagery and a larger footer. Shared public forms, safe Markdown, pagination,
metadata and Brand-scoped CMS APIs remain authoritative.

The local CMS has 12 fictional projects, 12 articles, 3 sample testimonials and
10 FAQs with clearly labelled original demo cover art. The development-only
`seed_web_designs_demo` command is repeatable; `--clear` removes its reserved
records and images while preserving real content and imported drafts. This is
preview data, not evidence of delivered projects or genuine endorsements.

Local review captures are in the ignored `website-mockup/web-designs-full-review/`
directory. Browser checks cover 36 populated routes, 96 single-hop permanent
redirect requests, canonical metadata/schema, images, search, pagination, theme,
menus, project switching and 320/390px widths. Backend tests verify repeatable
seeding, Web Designs isolation, production rejection and selective cleanup.

## Whole-site approval and checkpoint — 14 October 2026

The user approved the current Web Designs site and requested focused commits.
The checkpoint includes its full page rollout, larger logo, revised copy,
fictional CMS preview dataset, policies and privacy controls. Earlier Software
Solutions and Technology homepage studies are checkpointed separately; their
whole-site redesigns remain future work. The associated manually approved Lead
retention workflow is documented in `LEAD_RETENTION.md`. Nothing is deployed.

## Software Solutions and Technology rollout — 14 October 2026

The approved Web Designs visual language is now used across both other brands:
large Archivo headings/logos, dark/light themes, cyan scope bands, numbered service
and information pages, editorial layouts and the large footer. Software uses a
build/connect/automate feature; Technology uses a source/check/release/run flow.
Both keep their own services and copy. Shared policies, privacy choices and GA4
behavior are parameterised by Brand. Public analytics does not load in `/admin`.
This rollout was implemented locally. The user subsequently requested a commit
checkpoint for all completed changes; no production deployment was requested.

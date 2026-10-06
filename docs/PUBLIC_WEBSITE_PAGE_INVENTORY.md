# Public website pages and services

Updated 6 October 2026. The agreed service and page structure is implemented.
Editorial detail routes appear when matching CMS records are published; broader
software consultancy remains unconfirmed and is excluded from launch navigation.
Read with [the public website brief](PUBLIC_WEBSITES_PLAN.md).

## Confirmed direction and changed availability

- The third temporary design study is the preferred visual direction. Carry its
  brand-specific compositions into proper multi-page business websites.
- These are freelance businesses, not personal portfolio sites. Adam's direct
  involvement belongs in business positioning and the About page.
- Adam now has a full-time platform engineer role. Do not advertise contracting,
  staff augmentation, embedded team roles or full-time availability.
- Web hosting, maintenance, ecommerce, technical/local SEO and mobile application
  development are confirmed. Website rescue explicitly includes hacked and
  malware-infected websites.
- Website delivery supports Next.js, WordPress, Shopify and Squarespace.
- Technology covers cloud/DevOps, infrastructure, migrations, deployment pipelines,
  server management and server rebuilds. Do not promise core-hours technical support.
- Code reviews for AI-built/vibe-coded projects and app deployment preparation
  with security hardening are confirmed additions.
- Software consultancy is a proposal awaiting a decision on the bounded advisory
  scope below. Do not infer working hours or delivery commitments from the old plan.
- No speculative service prices, emergency support, 24/7 operations or guaranteed
  response times should be inserted into marketing copy.

## Content ownership

**Local** means code-owned copy in a clearly named content file in the relevant
site; copy stays separate from page components. **CMS** means editorial records
managed in the existing admin and explicitly assigned to the relevant Brand.
**Mixed** combines local marketing text/layout with brand-scoped CMS records.
CMS-based pages still render meaningful public content on the server.

Services, About, legal/policy text and area pages are local. Blogs, public
Portfolio, Testimonials and FAQs are CMS. The homepage and service/area pages can
show relevant CMS excerpts. The contact form uses the shared Django Brand-aware
Lead + Ticket ingestion flow; it is not a CMS record or standalone email sender.

Portfolio is public editorial content, distinct from operational Projects.
A record can be intentionally assigned to multiple Brands; content must not leak
between Brands by default. Empty editorial sections should not ship placeholder
projects, quotes or blog posts. Routes may be implemented before content exists,
but empty collections should stay out of navigation and the sitemap until useful.

## Pages on all three sites

Each domain gets its own versions of these pages, with relevant copy and design.
`[slug]` denotes a route family populated by actual CMS records, not a single page.

| Route                    | Purpose                                                                                             | Content                               |
| ------------------------ | --------------------------------------------------------------------------------------------------- | ------------------------------------- |
| `/`                      | Brand-specific introduction, core services, selected work and enquiry routes.                       | Mixed                                 |
| `/about/`                | Explain the business, Adam's experience/direct involvement, Manchester base and freelance delivery. | Local; optional CMS testimonials      |
| `/services/`             | Service directory and routes to individual service pages.                                           | Local                                 |
| `/working-together/`     | Enquiry, scope, delivery, handover and realistic availability; no contracting offers.               | Local                                 |
| `/areas-served/`         | Explain Manchester base, UK coverage and remote international working; link useful area pages.      | Local                                 |
| `/contact/`              | Brand-specific enquiry form feeding the shared Lead + Ticket system.                                | Local + backend submission            |
| `/contact/thank-you/`    | Submission confirmation and agreed expectations.                                                    | Local; noindex, excluded from sitemap |
| `/portfolio/`            | Browse genuine public projects/case studies for this Brand.                                         | CMS + local introduction              |
| `/portfolio/[slug]/`     | Project challenge, work delivered, outcome, images and technologies.                                | CMS                                   |
| `/blog/`                 | Browse this Brand's published articles, with pagination/filtering.                                  | CMS + local introduction              |
| `/blog/[slug]/`          | Published article, author information, images and related content.                                  | CMS                                   |
| `/blog/category/[slug]/` | Browse articles within a relevant, populated Brand category.                                        | CMS; substantive categories only      |
| `/testimonials/`         | Genuine client feedback relevant to the Brand.                                                      | CMS + local introduction              |
| `/faqs/`                 | Brand-specific questions about services and working arrangements.                                   | CMS + local introduction              |
| `/privacy-policy/`       | Accurate policy for forms, personal information and relevant integrations.                          | Local; approved policy text needed    |
| `/cookie-policy/`        | Explain cookies/storage actually used and available preferences.                                    | Local; match implemented behavior     |
| `/terms/`                | Website-use terms; not an invented client contract or pricing policy.                               | Local; approved text needed           |

No standalone testimonial-detail, FAQ-detail, tag-archive, author-archive, search
landing, pricing, careers, booking or client-portal pages are proposed at launch.
Search/filter controls can live within their relevant collection pages.
Site-specific 404/error pages are UI states, not indexed marketing pages.
Each site also needs generated `sitemap.xml`, `robots.txt` and page-level metadata
and social imagery. Software Solutions `/admin` remains outside the public site.

## ADB Web Designs

Confirmed Web Designs scope includes design/development, website rescue,
hosting, maintenance, ecommerce, technical SEO and local SEO. Builds can use
Next.js, WordPress, Shopify or Squarespace according to the project. Platform
coverage belongs in relevant service copy; no additional platform-specific page
is automatically implied beyond the existing proposed WordPress page.

| Proposed service page                   | Work covered                                                                                                                                 | Content / decision                                 |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `/services/web-design/`                 | Business website design/development using Next.js, WordPress, Shopify or Squarespace.                                                        | Local + relevant CMS work/FAQs; confirmed          |
| `/services/wordpress/`                  | WordPress builds, rebuilds and improvements.                                                                                                 | Local + relevant CMS work/FAQs; confirmed platform |
| `/services/website-rescue/`             | Recovery of hacked/malware-infected websites, cleanup/restoration and security improvements; also faults, performance and unfinished builds. | Local + relevant CMS work/FAQs; confirmed          |
| `/services/hosting/`                    | Website hosting and agreed management responsibilities.                                                                                      | Local + CMS FAQs; confirmed                        |
| `/services/website-maintenance/`        | Updates, backups, upkeep and agreed website maintenance.                                                                                     | Local + CMS FAQs/testimonials; confirmed           |
| `/services/ecommerce/`                  | Online-shop builds and integrations, including Shopify/WordPress and other suitable supported platforms.                                     | Local + CMS work/FAQs; confirmed                   |
| `/services/search-engine-optimisation/` | Technical SEO and local SEO, including site technical foundations and local business visibility.                                             | Local + CMS FAQs/work; confirmed scope             |

Copywriting, social media management and broader marketing campaigns are not part
of the offer. Do not promise search rankings or introduce specific packages or
support response times without agreement.

The user confirmed that Welcome to Travel approached ADB with a hacked,
malware-infected website. The case study should explain that starting problem
and the recovery work actually delivered. Do not invent attack details,
measured results or broader security guarantees.

Existing useful area URLs remain the proposed canonical URLs:

| Route                                 | Distinct purpose                                                             | Content |
| ------------------------------------- | ---------------------------------------------------------------------------- | ------- |
| `/manchester-website-design/`         | The actual Manchester base and local business website work.                  | Mixed   |
| `/salford-website-design/`            | Website work for Salford businesses; area served, not another office.        | Mixed   |
| `/wigan-website-design/`              | Website work for Wigan businesses; its own useful audience-focused copy.     | Mixed   |
| `/lancashire-website-design/`         | Wider Lancashire coverage and remote collaboration.                          | Mixed   |
| `/greater-manchester-website-design/` | Regional coverage beyond the individual town/city pages.                     | Mixed   |
| `/uk-website-design/`                 | Working remotely with UK businesses outside the immediate area.              | Mixed   |
| `/australia-website-design/`          | Manchester-based delivery for Australian clients and time-zone arrangements. | Mixed   |
| `/usa-website-design/`                | Manchester-based delivery for US clients and time-zone arrangements.         | Mixed   |

Local area copy is individually written. CMS work, testimonials and FAQs are used
only where genuinely relevant; do not invent location-specific evidence.

Possible initial CMS records, still requiring a content/currentness review:

| Proposed CMS page                                          | Status                                                     |
| ---------------------------------------------------------- | ---------------------------------------------------------- |
| `/portfolio/budget-girl/`                                  | Existing real portfolio record; review before publication. |
| `/portfolio/welcome-to-travel/`                            | Existing real portfolio record; review before publication. |
| `/blog/is-wordpress-a-great-cms-for-seo/`                  | Candidate for a refreshed CMS article.                     |
| `/blog/wordpress-what-are-the-benefits/`                   | Candidate for a refreshed CMS article.                     |
| `/blog/wordpress-how-to-secure-your-website/`              | Candidate for a refreshed CMS article.                     |
| `/blog/freelancer-vs-agency-who-will-design-your-website/` | Candidate for a refreshed CMS article.                     |
| `/blog/how-to-prevent-spam-comments-on-wordpress/`         | Candidate for a refreshed CMS article.                     |

The [old URL map](WEB_DESIGNS_URL_MIGRATION.json) is still a proposal. Ecommerce
and SEO service destinations now correspond to confirmed offerings; the SEO
destination must describe technical/local SEO rather than a broad marketing offer. Verify every destination,
content relevance and one-hop permanent redirect before activation. Retired
category routes must retain an appropriate filtered/category destination.

## ADB Software Solutions

The existing plan includes bespoke applications/SaaS, APIs/integrations,
automation, mobile development and consultancy. The current mockup showed the
first four. AI-built project/code reviews are now confirmed; broader software
consultancy is still an unconfirmed advisory proposal. Contracting is
removed from the public offer.

| Proposed service page             | Work covered                                                                                | Source / decision                                   |
| --------------------------------- | ------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| `/services/web-applications/`     | Business applications, internal tools and scoped SaaS product work.                         | Local + CMS work/FAQs; review project size/capacity |
| `/services/api-integrations/`     | APIs and connections between existing systems.                                              | Local + CMS work/FAQs; core scope                   |
| `/services/automation/`           | Business workflows, repetitive tasks and bots.                                              | Local + CMS work/FAQs; core scope                   |
| `/services/mobile-applications/`  | Mobile products that connect to backend/business systems.                                   | Local + CMS work/FAQs; confirmed                    |
| `/services/software-consultancy/` | Bounded architecture reviews, planning and second opinions.                                 | Local + CMS FAQs/work; review whether still offered |
| `/services/ai-code-review/`       | Scoped code reviews for AI-built/vibe-coded apps, prioritised findings and practical fixes. | Local + CMS work/FAQs; confirmed                    |

### AI-built app and code reviews — confirmed

Add `/services/ai-code-review/`: a local service page for people who have built
an app with AI/vibe-coding tools and want an experienced developer to review it.
Relevant Brand-assigned CMS work, FAQs and testimonials can supplement the page.
Use accessible wording such as "Code reviews for AI-built apps"; "vibe coding"
can appear naturally in the copy without judging the person or their tools.

The scoped review can cover architecture/maintainability, authentication and
permissions, data handling, exposed secrets, dependencies, validation, error
handling, useful tests and deployment blockers. Deliver a prioritised findings
report with practical fixes and next steps. Implementation/remediation can be
agreed separately. Findings must identify the code and scope reviewed; avoid
blanket claims that an app has become fully secure or certified for production.

Cross-link to Technology's app deployment service when the project needs an
operational setup. Keep application code review owned by Software Solutions;
this specific confirmed service does not approve every broader consultancy offer.

Software consultancy means a bounded advisory engagement: architecture/codebase
review, an integration feasibility review, or a written technical plan. The
deliverable might be recommendations and a prioritised implementation plan,
rather than a software build. It does not mean embedded team work, contracting,
ongoing CTO cover or general business consultancy. Keep this service/page pending
until the user decides whether to offer it.

No staff augmentation, team-joining or contractor availability pages. SaaS
product work is a service candidate, not a proposal to launch an ADB SaaS product.

Proposed narrower location/market set, subject to genuine Brand relevance:

| Route                               | Purpose                                                            | Content |
| ----------------------------------- | ------------------------------------------------------------------ | ------- |
| `/manchester-software-development/` | Actual local base and software services for Manchester businesses. | Mixed   |
| `/uk-software-development/`         | Scoped remote software projects across the UK.                     | Mixed   |
| `/australia-software-development/`  | Remote UK-based software delivery for Australian businesses.       | Mixed   |
| `/usa-software-development/`        | Remote UK-based software delivery for US businesses.               | Mixed   |

Do not replicate every Web Designs town page on this new site. Portfolio and blog
details come from genuine Brand-assigned CMS records; none are invented to fill
the launch sitemap.

## ADB Technology

Confirmed scope is cloud/DevOps, infrastructure, migrations, deployment
pipelines, server management and server rebuilds. The proposed service pages
below replace the ambiguous systems-support offer. Broad DevOps copy introduces
the discipline; the deployment-pipelines page covers the specific CI/CD service.

| Proposed service page             | Work covered                                                                        | Content / decision               |
| --------------------------------- | ----------------------------------------------------------------------------------- | -------------------------------- |
| `/services/cloud-infrastructure/` | Cloud setup, infrastructure design and improvements.                                | Local + CMS work/FAQs; confirmed |
| `/services/cloud-migrations/`     | Planning and carrying out cloud/infrastructure migrations.                          | Local + CMS work/FAQs; confirmed |
| `/services/devops/`               | Infrastructure automation and improvements to software delivery.                    | Local + CMS work/FAQs; confirmed |
| `/services/deployment-pipelines/` | Building and improving deployment/CI/CD pipelines.                                  | Local + CMS work/FAQs; confirmed |
| `/services/server-management/`    | Agreed server administration, configuration and upkeep.                             | Local + CMS work/FAQs; confirmed |
| `/services/server-rebuilds/`      | Rebuilding servers and restoring/redeploying the required services.                 | Local + CMS work/FAQs; confirmed |
| `/services/app-deployment/`       | Prepare and deploy existing apps with agreed infrastructure and security hardening. | Local + CMS work/FAQs; confirmed |

### App deployment and security hardening — confirmed

Add `/services/app-deployment/`: a local service page for taking an existing app,
including an AI-built project, from a working prototype toward a production
setup. Supplement with genuinely relevant Brand-scoped CMS evidence and FAQs.

Agree readiness checks and code remediation with Software Solutions as needed.
Technology work can include hosting/infrastructure setup, environment/secrets
configuration, domains/TLS, access controls, deployment pipelines, database
migration arrangements, logging/monitoring, backups, rollback and a documented
handover. Choose the actual work for the application rather than selling a fixed
technical checklist to every customer. Deployment-pipelines remains the narrower
CI/CD page; app-deployment covers the wider launch engagement.

Define the scope and operational ownership. Security hardening is scoped work,
not a guarantee that the app has no vulnerabilities, a certification, or an
implicit promise of ongoing support/core-hours availability. Cross-link back to
Software Solutions for application code review and implementation work.

Server management is an agreed technical service, not an implied core-hours
helpdesk. No contractor placements, guaranteed core-hours technical support,
emergency-response offer or 24/7 managed operations. Technical reviews can be
part of the scoped services above; a standalone technical-consultancy page is
not currently needed. No residential repairs, hardware retail or broad MSP offer
is proposed.

Proposed narrower location/market set, subject to genuine Brand relevance:

| Route                       | Purpose                                                               | Content |
| --------------------------- | --------------------------------------------------------------------- | ------- |
| `/manchester-cloud-devops/` | Actual Manchester base and the relevant infrastructure/DevOps offer.  | Mixed   |
| `/uk-cloud-devops/`         | Scoped technical projects delivered remotely across the UK.           | Mixed   |
| `/australia-cloud-devops/`  | Remote UK-based infrastructure/DevOps work for Australian businesses. | Mixed   |
| `/usa-cloud-devops/`        | Remote UK-based infrastructure/DevOps work for US businesses.         | Mixed   |

Do not claim that Web Designs' international clients automatically substantiate
Technology or Software Solutions case studies. Only use genuinely relevant work.

## Navigation and brand boundaries

Primary navigation can expose Services, Work/Portfolio, About and Contact, with
Blog, FAQs, Testimonials, Working together, coverage and policies placed where
useful. All pages need contextual links; not every route belongs in the header.
Web Designs handles the website; Software Solutions handles bespoke business
software; Technology handles the infrastructure/delivery underneath. Relevant
service pages and the footer cross-link the businesses.

Homepage sections are summaries that lead to these pages. Preserve the preferred
brand artwork and composition without copying the mockup's entire one-page stack
into production. No new backend/CMS architecture is implied by this inventory.

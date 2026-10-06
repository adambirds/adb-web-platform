import type { PublicSite } from "@adb/ui/public/types";

/** Edit marketing copy here. Editorial content lives in the brand-scoped CMS. */
export const site: PublicSite = {
    brand: "adb-web-designs",
    name: "ADB Web Designs",
    shortName: "Web Designs",
    domain: "https://adbwebdesigns.co.uk",
    description:
        "Freelance website design, development, ecommerce, recovery, hosting, maintenance and technical/local SEO from Manchester.",
    kind: "web",
    services: [
        {
            slug: "web-design",
            title: "Web design & development",
            description:
                "Freelance business website design and development in Manchester. Next.js, WordPress, Shopify and Squarespace builds, with direct developer involvement.",
            introduction:
                "A website should explain your business and make it easy for people to take the next step. I work with you on the structure, design and development, from a new site to a complete rebuild.",
            sections: [
                {
                    heading: "Start with the business",
                    paragraphs: [
                        "Before choosing layouts or a platform, we look at what the website needs to do: the services you sell, the questions customers ask and the information you already have. That gives the pages a purpose and the project a workable scope.",
                    ],
                },
                {
                    heading: "Choose a platform that fits",
                    paragraphs: [
                        "I can build in Next.js, WordPress, Shopify or Squarespace. The choice depends on your content, integrations, shop requirements and how you want to maintain the site. A small business website and a custom application do not need the same setup.",
                    ],
                },
                {
                    heading: "Build the whole website",
                    paragraphs: [
                        "The work includes responsive layouts, navigation, accessible interaction and technical search foundations. Content and page structure are considered together. We agree what you will supply, what needs moving from an old site and what happens after launch.",
                    ],
                },
                {
                    heading: "A direct working relationship",
                    paragraphs: [
                        "ADB Web Designs is a freelance business. You work directly with me on the project, with scope and delivery dates agreed around the actual work. Hosting and maintenance can be discussed alongside the build.",
                    ],
                },
            ],
            included: [
                "Page structure and responsive design",
                "Next.js, WordPress, Shopify or Squarespace development",
                "Contact forms and agreed integrations",
                "Technical search foundations and migration planning",
                "Launch and documented handover",
            ],
            related: [
                {
                    title: "WordPress websites",
                    href: "/services/wordpress/",
                },
                {
                    title: "Ecommerce",
                    href: "/services/ecommerce/",
                },
                {
                    title: "Hosting",
                    href: "/services/hosting/",
                },
            ],
        },
        {
            slug: "wordpress",
            title: "WordPress development",
            description:
                "WordPress websites, rebuilds and improvements from a freelance Manchester developer. Practical editing, integrations and ongoing maintenance.",
            introduction:
                "WordPress can be a useful home for a business website when its structure, theme and plugins are chosen carefully. I build new WordPress sites, improve existing ones and help untangle setups that have become difficult to manage.",
            sections: [
                {
                    heading: "Build around the content",
                    paragraphs: [
                        "The editing experience matters as much as the front end. We look at the pages, articles and other content you need to maintain, then agree an approach that lets you make normal updates without having to rebuild the design.",
                    ],
                },
                {
                    heading: "Review an existing website",
                    paragraphs: [
                        "An established WordPress site may have overlapping plugins, old layouts or features that no longer match the business. The first step is understanding what is there, what still needs to work and which changes will make a useful difference.",
                    ],
                },
                {
                    heading: "Handle the move carefully",
                    paragraphs: [
                        "A rebuild needs more than a new theme. Existing URLs, media, forms, integrations and search visibility need a migration decision. We agree what to keep, what to improve and how the new version will be checked before replacing the old site.",
                    ],
                },
            ],
            included: [
                "New WordPress builds and redesigns",
                "Theme and plugin integration",
                "Editing structure and content migration",
                "Performance and technical improvements",
                "Agreed hosting and maintenance options",
            ],
            related: [
                {
                    title: "Website rescue",
                    href: "/services/website-rescue/",
                },
                {
                    title: "Website maintenance",
                    href: "/services/website-maintenance/",
                },
                {
                    title: "Technical & local SEO",
                    href: "/services/search-engine-optimisation/",
                },
            ],
        },
        {
            slug: "website-rescue",
            title: "Hacked website recovery & rescue",
            description:
                "Help recovering hacked and malware-infected websites, restoring service and addressing security issues. Freelance website rescue from Manchester.",
            introduction:
                "A hacked website can leave you with redirects, unwanted content, broken access or a site you no longer trust. I help investigate the affected setup, recover the website and work through the issues that allowed the problem to persist.",
            sections: [
                {
                    heading: "Understand what has happened",
                    paragraphs: [
                        "The work starts with the affected website, available backups, hosting access and the symptoms you have seen. We establish what can be recovered and agree the steps before making changes. Please do not send passwords in the enquiry form; access can be arranged separately.",
                    ],
                },
                {
                    heading: "Recover and address the cause",
                    paragraphs: [
                        "Depending on the findings, the work can include removing malicious files, restoring a usable version, reviewing plugins and themes, correcting access and configuration issues, and rebuilding affected parts. Cleanup needs to be checked against how the site actually behaves.",
                    ],
                },
                {
                    heading: "Make the next step manageable",
                    paragraphs: [
                        "After recovery, we discuss updates, backups, access ownership and ongoing maintenance. The aim is to leave an understandable website and a practical plan for looking after it. The scope and findings determine the work; a recovery is not a blanket security guarantee.",
                    ],
                },
                {
                    heading: "Rescue is not only about malware",
                    paragraphs: [
                        "I can also help with unfinished builds, broken functionality and performance problems. Tell me what changed, what you can still access and what needs to be working again.",
                    ],
                },
            ],
            included: [
                "Review of hacked or malware-infected websites",
                "Cleanup, restoration or an agreed rebuild",
                "Review of relevant access, plugins and configuration",
                "Verification and recovery documentation",
                "Maintenance and backup arrangements",
            ],
            related: [
                {
                    title: "Website maintenance",
                    href: "/services/website-maintenance/",
                },
                {
                    title: "Hosting",
                    href: "/services/hosting/",
                },
                {
                    title: "Website rebuilds",
                    href: "/services/web-design/",
                },
            ],
        },
        {
            slug: "hosting",
            title: "Website hosting",
            description:
                "Website hosting with agreed management and a direct developer contact. Hosting for suitable business websites, discussed around the actual setup.",
            introduction:
                "Your website needs somewhere suitable to run. I offer website hosting and help choose a setup that fits the platform, traffic, data and integrations involved. Management responsibilities are agreed clearly, rather than left implicit.",
            sections: [
                {
                    heading: "Match hosting to the website",
                    paragraphs: [
                        "A WordPress installation, a Next.js application and a shop on Shopify have different hosting arrangements. We look at the platform first, then the environment and services that need managing. Platform-hosted products can still need domain and integration configuration.",
                    ],
                },
                {
                    heading: "Moving an existing site",
                    paragraphs: [
                        "A hosting move can involve website files, databases, domains, certificates and scheduled jobs. We identify the dependencies, discuss the cutover and agree checks for the new setup. Related email services need their own migration decision rather than an accidental change.",
                    ],
                },
                {
                    heading: "Know what is included",
                    paragraphs: [
                        "Hosting and website maintenance are related services, but they cover different work. We agree the environment responsibilities, backup arrangements and any ongoing application maintenance. Availability and response arrangements belong in the agreed service scope.",
                    ],
                },
            ],
            included: [
                "Suitable website hosting arrangements",
                "Domain and certificate configuration",
                "Agreed hosting migrations",
                "Backup and management responsibilities",
                "Clear ownership and handover",
            ],
            related: [
                {
                    title: "Website maintenance",
                    href: "/services/website-maintenance/",
                },
                {
                    title: "WordPress development",
                    href: "/services/wordpress/",
                },
                {
                    title: "Cloud & infrastructure",
                    href: "https://adbtechnology.co.uk/services/cloud-infrastructure/",
                },
            ],
        },
        {
            slug: "website-maintenance",
            title: "Website maintenance",
            description:
                "Business website maintenance, updates, backups and agreed improvements. Keep the scope of ongoing website care clear with a freelance developer.",
            introduction:
                "A live website needs care after the build. Maintenance can cover updates, checks, backups and small improvements, with the actual responsibilities agreed for your platform and business.",
            sections: [
                {
                    heading: "Review the starting point",
                    paragraphs: [
                        "Before taking on an existing site, I look at its platform, access, dependencies and current condition. That helps separate routine care from repair work that needs its own project. A site that is already compromised needs recovery before ordinary maintenance.",
                    ],
                },
                {
                    heading: "Agree the recurring work",
                    paragraphs: [
                        "For a WordPress site, maintenance may involve core, theme and plugin updates with appropriate checks. Other platforms need different work. We also agree backup arrangements and which kinds of content or functionality changes fall within the service.",
                    ],
                },
                {
                    heading: "Keep changes understandable",
                    paragraphs: [
                        "Updates should be accompanied by appropriate verification and a record of meaningful changes. Bigger redesigns, new features and substantial fixes can be scoped separately. Working arrangements and response expectations are agreed directly.",
                    ],
                },
            ],
            included: [
                "Platform-appropriate updates and checks",
                "Agreed backups and restore arrangements",
                "Routine maintenance and minor improvements",
                "Clear change records",
                "Separately scoped larger changes",
            ],
            related: [
                {
                    title: "Hacked website recovery",
                    href: "/services/website-rescue/",
                },
                {
                    title: "Hosting",
                    href: "/services/hosting/",
                },
                {
                    title: "Technical & local SEO",
                    href: "/services/search-engine-optimisation/",
                },
            ],
        },
        {
            slug: "ecommerce",
            title: "Ecommerce websites",
            description:
                "Online shop design and development using Shopify, WordPress/WooCommerce and suitable platforms. Freelance ecommerce development from Manchester.",
            introduction:
                "An online shop needs to support the way you sell, not just display products. I help build and improve ecommerce websites, from product structure and customer journeys to the integrations the business needs.",
            sections: [
                {
                    heading: "Choose the right shop platform",
                    paragraphs: [
                        "Shopify, WordPress with WooCommerce and other supported platforms offer different trade-offs. We look at product types, variants, fulfilment, payment options, existing tools and who will manage the shop before settling on an approach.",
                    ],
                },
                {
                    heading: "Work through the buying journey",
                    paragraphs: [
                        "Navigation, product pages, baskets and checkout all need attention. We agree the content you will provide and the configuration required for the shop. Shipping, tax and payment settings need business decisions from you rather than guesses in the build.",
                    ],
                },
                {
                    heading: "Connect the business behind the shop",
                    paragraphs: [
                        "A shop may need to exchange information with other systems. We can discuss product data, customer records and fulfilment integrations. Bespoke application or integration work can sit with ADB Software Solutions where that is the appropriate scope.",
                    ],
                },
                {
                    heading: "Move and hand over carefully",
                    paragraphs: [
                        "Existing product URLs and customer-facing pages need migration decisions. The handover should explain the agreed management tasks and any ongoing hosting or maintenance responsibilities.",
                    ],
                },
            ],
            included: [
                "Shopify and WordPress/WooCommerce builds",
                "Product and catalogue structure",
                "Responsive shop layouts",
                "Agreed payment, shipping and integration setup",
                "Migration and handover planning",
            ],
            related: [
                {
                    title: "Website development",
                    href: "/services/web-design/",
                },
                {
                    title: "API integrations",
                    href: "https://adbsoftwaresolutions.co.uk/services/api-integrations/",
                },
                {
                    title: "Technical & local SEO",
                    href: "/services/search-engine-optimisation/",
                },
            ],
        },
        {
            slug: "search-engine-optimisation",
            title: "Technical & local SEO",
            description:
                "Technical SEO and local SEO for business websites. Site structure, indexing, performance and accurate local business information, focused on the website and its visibility.",
            introduction:
                "A website needs a sound technical structure and clear information about the business it represents. I work on technical SEO and local SEO, addressing the site and local visibility rather than selling an unrelated marketing package.",
            sections: [
                {
                    heading: "Review the technical foundations",
                    paragraphs: [
                        "The review can cover crawlable pages, indexing instructions, canonical URLs, redirects, metadata, structured data and performance issues. Findings should turn into specific changes with a clear reason, rather than a list of unexplained scores.",
                    ],
                },
                {
                    heading: "Make local information useful",
                    paragraphs: [
                        "Local SEO starts with accurate business information and useful service-area content. We can review local listings and how the website represents the actual business base and areas served. A page for a town should have a purpose beyond replacing a location name.",
                    ],
                },
                {
                    heading: "Protect useful existing content",
                    paragraphs: [
                        "Rebuilds and domain or URL changes can affect established pages. We inventory the important URLs and agree what to preserve, consolidate or retire. Redirects should lead to relevant content and be checked alongside the new site.",
                    ],
                },
                {
                    heading: "Keep the offer clear",
                    paragraphs: [
                        "This service does not include promised copywriting, social media management or advertising campaigns. We agree the technical and local work involved. Search positions depend on more than a website change, so rankings are not guaranteed.",
                    ],
                },
            ],
            included: [
                "Technical site reviews and prioritised fixes",
                "Indexing, canonical and redirect checks",
                "Metadata and suitable structured data",
                "Local listing and business-information reviews",
                "Purposeful service-area pages",
            ],
            related: [
                {
                    title: "Website development",
                    href: "/services/web-design/",
                },
                {
                    title: "Website maintenance",
                    href: "/services/website-maintenance/",
                },
                {
                    title: "Manchester web design",
                    href: "/manchester-website-design/",
                },
            ],
        },
    ],
    areas: [
        {
            slug: "manchester-website-design",
            title: "Website design in Manchester",
            description:
                "I’m based in Manchester and work directly with businesses on new websites, rebuilds and existing-site improvements.",
            introduction:
                "I’m based in Manchester and work directly with businesses on new websites, rebuilds and existing-site improvements.",
            sections: [
                {
                    heading: "A Manchester-based developer",
                    paragraphs: [
                        "If you want to work with someone based in the area, the project stays with the developer building the site. We can discuss your business, content and existing setup directly. Meeting arrangements are agreed rather than assumed.",
                    ],
                },
                {
                    heading: "Local services need clear pages",
                    paragraphs: [
                        "A website for a service business needs to explain what you do, where you work and how a customer can enquire. Local SEO work can help review the technical foundations and accurate business information supporting those pages.",
                    ],
                },
            ],
            services: [
                "web-design",
                "search-engine-optimisation",
                "website-maintenance",
            ],
        },
        {
            slug: "salford-website-design",
            title: "Website design for Salford businesses",
            description:
                "Website design and development for businesses in Salford, delivered by a freelance developer based nearby in Manchester.",
            introduction:
                "Website design and development for businesses in Salford, delivered by a freelance developer based nearby in Manchester.",
            sections: [
                {
                    heading: "A website built around the business",
                    paragraphs: [
                        "Whether you are replacing an old website or putting a service online for the first time, we start with the work you do and the information customers need. Platform choice follows the project, from WordPress to a custom Next.js build.",
                    ],
                },
                {
                    heading: "An existing site can be improved",
                    paragraphs: [
                        "A rebuild is not always the first answer. Broken forms, slow pages or an awkward editing experience may have a more focused solution. I can review the site and discuss improvements, maintenance or a larger redesign.",
                    ],
                },
            ],
            services: ["web-design", "wordpress", "website-rescue"],
        },
        {
            slug: "wigan-website-design",
            title: "Website design for Wigan businesses",
            description:
                "Freelance website development for Wigan businesses, with new builds, shop websites and ongoing care delivered from Manchester.",
            introduction:
                "Freelance website development for Wigan businesses, with new builds, shop websites and ongoing care delivered from Manchester.",
            sections: [
                {
                    heading: "Make the next step clear",
                    paragraphs: [
                        "A business website needs to turn a visitor’s questions into an understandable route through your services, products or enquiry form. We agree the page structure and the content needed before choosing the design.",
                    ],
                },
                {
                    heading: "Keep website ownership practical",
                    paragraphs: [
                        "After launch, someone needs to manage content, updates and the hosting arrangement. We choose a platform you can work with and discuss maintenance where it is useful. Ecommerce and integrations can be scoped alongside the website.",
                    ],
                },
            ],
            services: ["web-design", "ecommerce", "hosting"],
        },
        {
            slug: "lancashire-website-design",
            title: "Website design for Lancashire businesses",
            description:
                "Website design, development and ecommerce for Lancashire businesses, working remotely with a Manchester-based freelance developer.",
            introduction:
                "Website design, development and ecommerce for Lancashire businesses, working remotely with a Manchester-based freelance developer.",
            sections: [
                {
                    heading: "Working across the county",
                    paragraphs: [
                        "You do not need to be in the same town to work through a website project. Content, design reviews and development can be organised remotely, with a clear scope and agreed review points.",
                    ],
                },
                {
                    heading: "Choose what the website needs to support",
                    paragraphs: [
                        "A catalogue, an online shop and a service business website have different requirements. We look at the customer journey, editing tasks and integrations, then choose between supported platforms such as WordPress, Shopify, Squarespace or Next.js.",
                    ],
                },
            ],
            services: ["web-design", "ecommerce", "website-maintenance"],
        },
        {
            slug: "greater-manchester-website-design",
            title: "Website design across Greater Manchester",
            description:
                "Business websites and existing-site improvements across Greater Manchester, from a freelance developer based in Manchester.",
            introduction:
                "Business websites and existing-site improvements across Greater Manchester, from a freelance developer based in Manchester.",
            sections: [
                {
                    heading: "Coverage beyond the city centre",
                    paragraphs: [
                        "I work with businesses across the region. The website still starts with your specific customers and services rather than a regional template. Manchester is the business base; areas served are not additional offices.",
                    ],
                },
                {
                    heading: "One project, related technical work",
                    paragraphs: [
                        "A website can depend on more than page design. Hosting, shop integrations or an application behind a form may need separate work. The related ADB businesses provide routes to discuss the appropriate software or infrastructure scope.",
                    ],
                },
            ],
            services: ["web-design", "hosting", "search-engine-optimisation"],
        },
        {
            slug: "uk-website-design",
            title: "Website design for UK businesses",
            description:
                "Remote website design and development for businesses across the UK, delivered directly by a Manchester-based freelance developer.",
            introduction:
                "Remote website design and development for businesses across the UK, delivered directly by a Manchester-based freelance developer.",
            sections: [
                {
                    heading: "A remote website project",
                    paragraphs: [
                        "The project can be organised around a written brief, shared content and agreed design reviews. You work directly with me on scope and delivery. There is no requirement to be near Manchester to discuss a build or existing-site problem.",
                    ],
                },
                {
                    heading: "Moving from an existing website",
                    paragraphs: [
                        "An established site may have useful URLs, media and shop data. We agree what to preserve or retire and consider migration as part of the work. Hosting and ongoing maintenance can be arranged where they fit the platform.",
                    ],
                },
            ],
            services: ["web-design", "wordpress", "website-maintenance"],
        },
        {
            slug: "australia-website-design",
            title: "Website development for Australian businesses",
            description:
                "Work remotely with a Manchester-based web developer on Australian business websites, ecommerce and existing-site recovery.",
            introduction:
                "Work remotely with a Manchester-based web developer on Australian business websites, ecommerce and existing-site recovery.",
            sections: [
                {
                    heading: "A UK developer, working with Australian clients",
                    paragraphs: [
                        "I have Australian clients and deliver work remotely from Manchester. This page describes that working relationship; it does not imply an Australian office or local residency. Meeting times and review arrangements are agreed around the time difference.",
                    ],
                },
                {
                    heading: "Keep the brief and handover usable",
                    paragraphs: [
                        "Clear written feedback and shared project information help work move between time zones. We agree who supplies content, who manages the platform and what needs documenting. Any support or meeting schedule is discussed for the actual project.",
                    ],
                },
                {
                    heading: "Websites, shops and rescue work",
                    paragraphs: [
                        "The scope can include a new business website, an ecommerce build or help with an existing site. Appropriate hosting, maintenance and integration arrangements are considered alongside the platform rather than assumed from the location.",
                    ],
                },
            ],
            services: ["web-design", "ecommerce", "website-rescue"],
        },
        {
            slug: "usa-website-design",
            title: "Website development for US businesses",
            description:
                "Remote website design and development for US businesses, from a Manchester-based freelance developer with international clients.",
            introduction:
                "Remote website design and development for US businesses, from a Manchester-based freelance developer with international clients.",
            sections: [
                {
                    heading: "Working remotely from Manchester",
                    paragraphs: [
                        "I work with American clients while remaining based in the UK. We agree a practical way to share content, review changes and meet when needed. US time zones differ, so meeting and response arrangements belong in the project discussion.",
                    ],
                },
                {
                    heading: "Build around your business requirements",
                    paragraphs: [
                        "The platform and content should reflect how the business operates. Product structure, integrations and local business information need your input. There is no assumption of a US office, local working hours or a particular pricing currency.",
                    ],
                },
                {
                    heading: "Manage an existing site transition",
                    paragraphs: [
                        "If you already have a website, we can review the current pages and technical setup before agreeing changes. A migration plan helps preserve useful content and establish who looks after the new site after launch.",
                    ],
                },
            ],
            services: ["web-design", "ecommerce", "website-maintenance"],
        },
    ],
    pages: [
        {
            slug: "about",
            title: "About ADB Web Designs",
            description:
                "Freelance website design, development, ecommerce, recovery, hosting, maintenance and technical/local SEO from Manchester.",
            introduction:
                "ADB Web Designs is a freelance business run by Adam Birds, based in Manchester.",
            sections: [
                {
                    heading: "Work directly with me",
                    paragraphs: [
                        "I design and develop business websites, help recover compromised sites and offer hosting and ongoing maintenance. Work can use Next.js, WordPress, Shopify or Squarespace, depending on the requirements.",
                        "The conversation, scope and technical work stay connected. You can ask questions about the decisions being made and agree what the finished work needs to include.",
                    ],
                },
                {
                    heading: "A freelance business, with agreed availability",
                    paragraphs: [
                        "Projects and ongoing services are scoped around the work involved and an agreed schedule. Availability, delivery arrangements and response expectations are agreed before the work starts.",
                    ],
                },
                {
                    heading: "Manchester-based, working further afield",
                    paragraphs: [
                        "I work remotely as well as with businesses in the surrounding area. International work remains UK-based, with meetings and review arrangements agreed around time zones.",
                    ],
                },
                {
                    heading: "Three related ADB businesses",
                    paragraphs: [
                        "Web Designs covers websites; Software Solutions covers bespoke applications and integrations; Technology covers the infrastructure and deployment underneath. Related service pages link to the appropriate business when a project crosses those boundaries.",
                    ],
                },
            ],
        },
        {
            slug: "working-together",
            title: "Working together",
            description:
                "How an enquiry becomes an agreed website project: scope, delivery, reviews and handover.",
            introduction:
                "Start with what you want to build, improve or fix. You do not need a finished technical specification to make an enquiry.",
            sections: [
                {
                    heading: "Describe the starting point",
                    paragraphs: [
                        "Tell me about the business, the existing setup and the outcome you need. Useful context includes what already works, what is getting in the way and any real timing constraints. Please keep passwords and private credentials out of the contact form.",
                    ],
                },
                {
                    heading: "Agree the work",
                    paragraphs: [
                        "We discuss fit, requirements, responsibilities and the scope before implementation. Dates, costs and any ongoing arrangements are agreed for the project. No fixed price or support schedule is implied by a service description.",
                    ],
                },
                {
                    heading: "Review as the work takes shape",
                    paragraphs: [
                        "Appropriate review points give you a chance to check the direction and clarify decisions. Material changes to the scope are discussed, so the work does not quietly become a different project.",
                    ],
                },
                {
                    heading: "Check and hand over",
                    paragraphs: [
                        "The result is checked against the agreed scope, with useful documentation and a clear understanding of who manages it afterwards. Hosting, maintenance or further development can be discussed where those services fit.",
                    ],
                },
            ],
        },
        {
            slug: "areas-served",
            title: "Areas served & remote working",
            description:
                "Manchester-based ADB Web Designs services, with local coverage and remote working across the UK and internationally.",
            introduction:
                "Manchester is the business base. I work with people nearby, across the UK and remotely in other countries.",
            sections: [
                {
                    heading: "Local working",
                    paragraphs: [
                        "Area pages describe places served rather than separate offices. The project, platform and business requirements still determine the work; a location name is not a substitute for a useful brief.",
                    ],
                },
                {
                    heading: "Working remotely",
                    paragraphs: [
                        "Written scope, shared feedback and agreed review points help remote projects stay understandable. For international work, meeting times and operational arrangements are discussed around the time difference.",
                    ],
                },
            ],
        },
        {
            slug: "privacy-policy",
            title: "Privacy policy",
            description:
                "Information about contact enquiries and personal data handled through ADB Web Designs.",
            noindex: true,
            introduction:
                "This page explains the information used when you contact ADB Web Designs through this website.",
            sections: [
                {
                    heading: "Information in your enquiry",
                    paragraphs: [
                        "The form asks for your name, email address, optional business/project name, the service you are interested in and your message. The website page associated with the enquiry is also recorded. Avoid sending passwords or other secrets.",
                    ],
                },
                {
                    heading: "How the enquiry is used",
                    paragraphs: [
                        "Your enquiry is used to respond, discuss suitable work and keep a record of the conversation. The ADB businesses use a shared business platform, with the originating business identified for each enquiry.",
                    ],
                },
                {
                    heading: "Website preferences and technical information",
                    paragraphs: [
                        "A theme preference can be stored in your browser when you use the dark/light switch. The site does not add advertising trackers or analytics cookies. The hosting and service infrastructure may process technical request information needed to operate the site.",
                    ],
                },
                {
                    heading: "Questions about your information",
                    paragraphs: [
                        "Use the contact form to ask about the information you have supplied or to raise a privacy question. Further details about the operator, retention and service providers must be confirmed before this policy is approved for launch.",
                    ],
                },
            ],
        },
        {
            slug: "cookie-policy",
            title: "Cookies & website storage",
            description:
                "Cookies and browser storage used by ADB Web Designs, including the optional dark/light theme preference.",
            noindex: true,
            introduction:
                "The public website keeps browser storage limited to the functions it actually uses.",
            sections: [
                {
                    heading: "Your display preference",
                    paragraphs: [
                        "Using the theme switch can save an optional local preference called adb-public-theme. It controls whether this site opens in light or dark mode on this browser. If storage is unavailable, the site still works with its default appearance.",
                    ],
                },
                {
                    heading: "No advertising or analytics added",
                    paragraphs: [
                        "The public pages do not add advertising trackers, third-party analytics, externally hosted fonts or embedded social widgets. Visiting a related website or signing in to the separate account/operations applications can involve those applications’ own storage.",
                    ],
                },
                {
                    heading: "Change or clear the preference",
                    paragraphs: [
                        "You can change the appearance using the header button or clear this website’s stored data in your browser settings. Cookies and storage must be reviewed again if new integrations are added.",
                    ],
                },
            ],
        },
        {
            slug: "terms",
            title: "Website terms",
            description:
                "Website-use information for ADB Web Designs. Project and service agreements are arranged separately.",
            noindex: true,
            introduction:
                "These pages describe the business and services available to discuss. They do not form a project agreement or a promise of availability.",
            sections: [
                {
                    heading: "Service information",
                    paragraphs: [
                        "The scope, cost, delivery dates and ongoing responsibilities for any work are agreed directly. Service descriptions do not imply contracting availability, guaranteed response times or a specific support schedule.",
                    ],
                },
                {
                    heading: "Content and related links",
                    paragraphs: [
                        "Articles and project information explain the relevant subject or work. Links to related businesses and external sites provide further context. Individual project requirements still need their own review.",
                    ],
                },
                {
                    heading: "Separate project arrangements",
                    paragraphs: [
                        "Client agreements, hosting arrangements and other commercial terms are separate from these website-use pages. The full operator details and final website terms need approval before launch.",
                    ],
                },
            ],
        },
    ],
    contact: {
        title: "Discuss your website",
        introduction:
            "Tell me what you would like to build, improve or fix. I’ll review the enquiry and get back to you to discuss whether the work is a good fit.",
        guidance:
            "Scope, availability and delivery arrangements are agreed individually. Please do not include passwords or private credentials.",
    },
};

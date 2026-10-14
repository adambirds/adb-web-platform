import { websitePolicies } from "./policies";
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
                        "Once the site is recovered, I’ll help you put updates, backups and safer access in place. Ongoing maintenance is available to keep the website looked after.",
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
                "Give your website a reliable home. I offer hosting for business websites and help move existing sites, with a setup that suits the platform and the way your website is used.",
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
                        "I can move your website files and database, configure its domain and SSL certificate, and check the new hosting before switching over. I’ll also check whether the move affects your email or other connected services.",
                    ],
                },
                {
                    heading: "Know what is included",
                    paragraphs: [
                        "Hosting keeps the website running; maintenance keeps its software up to date. I can help with both, including backups and updates for your particular website.",
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
                        "Make it easy for customers to find a product and complete their order. I build product pages, navigation, baskets and checkout, and work with you to set up payments, shipping and tax settings for your shop.",
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
                "Help customers find your business through search. I work on technical SEO and local SEO: fixing problems that hold your website back and making your services and location easier for search engines to understand.",
            sections: [
                {
                    heading: "Review the technical foundations",
                    paragraphs: [
                        "I check how search engines access your pages, look for indexing and redirect problems, and review page titles, descriptions, structured data and performance. You’ll get a clear explanation of what needs fixing and why.",
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
                        "The focus is your website and local search presence. I can improve its technical foundations and help customers find accurate information about your business.",
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
                        "I’m Adam, a freelance web designer and developer based in Manchester. You’ll speak to me about your ideas, review the designs with me and have me build the finished website. I work on new business websites, online shops and sites that need a redesign or repair.",
                    ],
                },
                {
                    heading: "Local services need clear pages",
                    paragraphs: [
                        "When someone searches for a business in Manchester, your website should help them understand what you offer and get in touch. I build clear service pages, make them easy to use on a phone and take care of the technical SEO that helps search engines find and understand them.",
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
                        "Your customers should be able to find what you do, see your work and contact you without hunting around. I design websites for Wigan businesses with clear navigation, readable pages and an enquiry process that’s easy to use on mobile.",
                    ],
                },
                {
                    heading: "Keep website ownership practical",
                    paragraphs: [
                        "You should be able to update your own website after launch. I can build with WordPress, Shopify or Squarespace, or use Next.js for a custom build. Hosting and maintenance are available too, so there’s someone to turn to when the website needs looking after.",
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
                        "I work with Lancashire businesses from my base in Manchester. We can get started with a video call and review the website online, so you can see the design develop without travelling for every conversation.",
                    ],
                },
                {
                    heading: "Choose what the website needs to support",
                    paragraphs: [
                        "A service business needs to explain its work and bring in enquiries. An online shop needs to make browsing and buying easy. I’ll help you choose the right platform for your business and build the pages, forms and features your customers need.",
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
                        "From Salford and Wigan to the wider Greater Manchester area, I help businesses launch new websites and improve existing ones. Your website will be designed around your business: the work you do, the customers you want to reach and the way you want it to look.",
                    ],
                },
                {
                    heading: "One project, related technical work",
                    paragraphs: [
                        "I can look after the website build, hosting and maintenance. If you also need custom software or more involved infrastructure work, my related businesses, ADB Software Solutions and ADB Technology, cover those services.",
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
                        "I work with businesses throughout the UK. We’ll talk through what you need, review the designs together and keep in touch during the build. You’ll deal directly with the person designing and developing your website.",
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
                        "I’m based in Manchester, UK, and already work with Australian clients. You can work with me on a new website, an online shop or an existing site that needs attention, with video calls and online design reviews that fit both our time zones.",
                    ],
                },
                {
                    heading: "Keep in touch throughout the build",
                    paragraphs: [
                        "You can look through designs and leave feedback when it suits you. I’ll keep you updated on the build and explain how to manage the finished website, so the time difference doesn’t mean losing track of your project.",
                    ],
                },
                {
                    heading: "Websites, shops and rescue work",
                    paragraphs: [
                        "I build business websites and online shops, and recover sites affected by hacks or malware. That recovery work is how I first worked with Australian travel business Welcome to Travel. Hosting and maintenance are also available for the website after launch.",
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
                        "I’m a UK-based freelance developer working with clients in the US as well as at home. We can discuss your website on a video call and review the design online, with calls planned around the time difference.",
                    ],
                },
                {
                    heading: "Build around your business requirements",
                    paragraphs: [
                        "Whether you sell products, offer services or need to replace an outdated website, I’ll help you choose a platform that fits. I build with Next.js, WordPress, Shopify and Squarespace, and can connect your website to the tools your business uses.",
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
                "Meet Adam Birds, the Manchester-based freelance designer and developer behind ADB Web Designs. Business websites, ecommerce, website rescue and ongoing care.",
            introduction:
                "I’m Adam Birds. I design, build and look after business websites from my base in Manchester, working with clients across the UK and overseas.",
            sections: [
                {
                    heading:
                        "One person, from the first conversation to launch",
                    paragraphs: [
                        "ADB Web Designs is my freelance web design and development business. When you get in touch, you’ll speak to me. I’ll work through your ideas with you, design the pages and build the website.",
                        "That means you can ask the person doing the work why something has been designed a particular way, how a feature will work or what you’ll need to manage after launch. You don’t need to turn up with a technical specification; a conversation about your business is a good place to start.",
                    ],
                },
                {
                    heading: "A website you can use, not just look at",
                    paragraphs: [
                        "The design matters, but so does everything around it. Customers need to find their way through the pages, forms need to work, and the website needs to be comfortable to use on a phone. Search engines need to be able to read it, too.",
                        "I build with Next.js, WordPress, Shopify and Squarespace. I’ll help you choose a platform based on what you need the website to do and how you want to update it. A custom build can make sense for one business; an established platform can be a better fit for another.",
                    ],
                },
                {
                    heading: "New builds, fresh starts and website rescue",
                    paragraphs: [
                        "You might be starting a business, replacing a website you’ve outgrown or adding an online shop. I can help with the design and build, move content from your existing site and get the new version ready for launch.",
                        "I also help when things have gone wrong. My work with Australian travel business Welcome to Travel began with a hacked, malware-infected website. Recovering compromised sites is part of what I offer, alongside new websites and redesigns.",
                        "Once a website is live, hosting and maintenance are available to keep it looked after. I also work on technical and local SEO, helping address the website problems that can make it harder for customers to find you.",
                    ],
                },
                {
                    heading: "Manchester-based, with clients further afield",
                    paragraphs: [
                        "I work with businesses in Manchester, Salford, Wigan and Lancashire, as well as clients elsewhere in the UK, Australia and the US.",
                        "For remote projects, we can talk on video calls, share designs online and review the build together. You’ll still work directly with me throughout, wherever your business is based.",
                    ],
                },
                {
                    heading: "The other sides of ADB",
                    paragraphs: [
                        "ADB Web Designs focuses on websites. I also run ADB Software Solutions for bespoke software, mobile apps and integrations, and ADB Technology for cloud infrastructure, migrations and deployment pipelines.",
                        "If your website needs something beyond the usual pages and forms, we can talk about that too. The three businesses cover different types of work, with the same person behind them.",
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
                        "I’ll talk through the options with you and put together a proposal covering the work, cost and timeline. You’ll know what’s included before the build starts.",
                    ],
                },
                {
                    heading: "Review as the work takes shape",
                    paragraphs: [
                        "You’ll see the designs before they become a finished website, with time to give feedback and ask questions. As the build develops, we’ll check the pages and features together.",
                    ],
                },
                {
                    heading: "Check and hand over",
                    paragraphs: [
                        "Before launch, I’ll check the website across screen sizes and test its forms and key features. Then I’ll show you how to use it. If you’d like ongoing help, I also offer hosting and maintenance.",
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
                        "I’m based in Manchester and build websites for businesses across Salford, Wigan, Greater Manchester and Lancashire. Whether you need your first website, an online shop or a fresh start for an existing site, you’ll work directly with me from the first conversation through to launch.",
                    ],
                },
                {
                    heading: "Working remotely",
                    paragraphs: [
                        "You don’t need to be nearby to work with me. I also work with businesses across the UK, Australia and the US. We can talk through your ideas on a video call, review the designs online and keep in touch as the website takes shape.",
                    ],
                },
            ],
        },
        ...websitePolicies,
    ],
    contact: {
        title: "Discuss your website",
        introduction:
            "Tell me what you would like to build, improve or fix. I’ll review the enquiry and get back to you to discuss whether the work is a good fit.",
        guidance:
            "Tell me what you’d like to build, improve or fix. Please keep passwords and private credentials out of your message.",
    },
};

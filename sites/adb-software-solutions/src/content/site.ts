import type { PublicSite } from "@adb/ui/public/types";

/** Edit marketing copy here. Editorial content lives in the brand-scoped CMS. */
export const site: PublicSite = {
    brand: "adb-software-solutions",
    name: "ADB Software Solutions",
    shortName: "Software Solutions",
    domain: "https://adbsoftwaresolutions.co.uk",
    description:
        "Freelance software development from Manchester: applications, APIs, automation, mobile apps and code reviews for AI-built projects.",
    kind: "software",
    services: [
        {
            slug: "web-applications",
            title: "Web applications & business software",
            description:
                "Bespoke web applications, internal tools and scoped SaaS development from a freelance Manchester software developer.",
            introduction:
                "When an existing tool no longer fits the business, a custom application may be the right next step. I build web applications and internal software around the people using them and the process they need to support.",
            sections: [
                {
                    heading: "Define the useful first version",
                    paragraphs: [
                        "We start with the current workflow, users and information involved. That helps distinguish essential functionality from ideas that can wait. Scope, responsibilities and delivery dates are agreed for the project rather than inferred from a long feature list.",
                    ],
                },
                {
                    heading: "Build the application and its boundaries",
                    paragraphs: [
                        "The work can include the user interface, backend, database and agreed integrations. Permissions, data validation and failure handling need to be considered as part of the design, alongside the normal route through the application.",
                    ],
                },
                {
                    heading: "Plan beyond the demonstration",
                    paragraphs: [
                        "An application needs an environment, deployment process and ongoing ownership. We discuss those arrangements before handover. Infrastructure and delivery work can be supported through ADB Technology when the project needs that separate scope.",
                    ],
                },
            ],
            included: [
                "Business web applications and internal tools",
                "Scoped SaaS application development",
                "Frontend, backend and database work",
                "Authentication and application permissions",
                "Integration, deployment and handover planning",
            ],
            related: [
                {
                    title: "API integrations",
                    href: "/services/api-integrations/",
                },
                {
                    title: "Mobile applications",
                    href: "/services/mobile-applications/",
                },
                {
                    title: "App deployment",
                    href: "https://adbtechnology.co.uk/services/app-deployment/",
                },
            ],
        },
        {
            slug: "api-integrations",
            title: "APIs & integrations",
            description:
                "Connect business systems with APIs and custom integrations. Freelance development for practical data flows and maintainable interfaces.",
            introduction:
                "If information is being copied between tools, or two systems need to work together, an integration can help. I build APIs and connections around the actual data, permissions and behavior of the systems involved.",
            sections: [
                {
                    heading: "Understand both sides",
                    paragraphs: [
                        "An integration begins with what each system exposes and what the business needs to happen. We review available APIs, authentication methods, data structures and any limits. That avoids designing a workflow the tools cannot support.",
                    ],
                },
                {
                    heading: "Handle the awkward cases",
                    paragraphs: [
                        "Failures, repeated events, missing data and rate limits are part of integration work. We agree how to recognise duplicates, recover from interruptions and make issues visible to the people responsible for the process.",
                    ],
                },
                {
                    heading: "Leave a maintainable connection",
                    paragraphs: [
                        "Configuration, credential handling and documentation matter after the first successful request. The handover should explain what the integration does, where it runs and how changes to either system will be managed.",
                    ],
                },
            ],
            included: [
                "API design and implementation",
                "Connections between existing platforms",
                "Data mapping and synchronisation",
                "Webhooks and background processing",
                "Error handling and integration documentation",
            ],
            related: [
                {
                    title: "Business automation",
                    href: "/services/automation/",
                },
                {
                    title: "Web applications",
                    href: "/services/web-applications/",
                },
                {
                    title: "Deployment pipelines",
                    href: "https://adbtechnology.co.uk/services/deployment-pipelines/",
                },
            ],
        },
        {
            slug: "automation",
            title: "Automation & bots",
            description:
                "Automate repetitive business work with maintainable workflows, scripts and bots. Freelance software development with an agreed scope.",
            introduction:
                "Re-entering information, repeating the same checks or moving files between tools can take up a lot of a working day. I help identify suitable automation and build the workflow around what should happen when something goes wrong as well as when it works.",
            sections: [
                {
                    heading: "Choose a process worth automating",
                    paragraphs: [
                        "We look at the current steps, the exceptions and the cost of a mistake. Some workflows need a person to approve a decision; others can run on a schedule or respond to an event. The design should preserve the control the business actually needs.",
                    ],
                },
                {
                    heading: "Connect the available tools",
                    paragraphs: [
                        "Automation can use APIs, scheduled tasks, scripts or bots, depending on the environment. The scope includes the systems involved, the information being handled and any permissions needed. It should not rely on secrets being pasted into ordinary code.",
                    ],
                },
                {
                    heading: "Make it observable",
                    paragraphs: [
                        "A process that fails silently is difficult to trust. We agree logging, notifications and recovery behavior appropriate to the work. Documentation and ownership help the automation remain useful when the surrounding process changes.",
                    ],
                },
            ],
            included: [
                "Business workflow automation",
                "Scheduled tasks and background jobs",
                "API-driven scripts and bots",
                "Human approval steps where needed",
                "Logging and practical handover",
            ],
            related: [
                {
                    title: "API integrations",
                    href: "/services/api-integrations/",
                },
                {
                    title: "Web applications",
                    href: "/services/web-applications/",
                },
                {
                    title: "Cloud & infrastructure",
                    href: "https://adbtechnology.co.uk/services/cloud-infrastructure/",
                },
            ],
        },
        {
            slug: "mobile-applications",
            title: "Mobile application development",
            description:
                "Mobile application development with backend and business-system integration. Freelance project work scoped around the product.",
            introduction:
                "A mobile application should fit the product and its users, not exist simply because the business could have an app. I help plan and build mobile applications, including the backend and integrations they need.",
            sections: [
                {
                    heading: "Start with the mobile use case",
                    paragraphs: [
                        "We discuss who will use the app, which devices matter and what someone needs to do away from a desktop. Notifications, device features and offline behavior can affect the design. Those requirements help define the initial scope.",
                    ],
                },
                {
                    heading: "Build the connected product",
                    paragraphs: [
                        "Many mobile apps depend on accounts, APIs and stored data. The application and backend need a consistent approach to permissions, validation and failure handling. Where there is an existing system, we first establish what can be reused.",
                    ],
                },
                {
                    heading: "Plan testing and release",
                    paragraphs: [
                        "Device testing, distribution and store arrangements need to be agreed alongside development. Accounts and ongoing product ownership remain clear. Delivery dates and post-release work are scoped around the actual application.",
                    ],
                },
            ],
            included: [
                "Mobile product planning and development",
                "Backend and API integration",
                "Accounts and application permissions",
                "Device-appropriate interaction",
                "Agreed testing, release and handover",
            ],
            related: [
                {
                    title: "API integrations",
                    href: "/services/api-integrations/",
                },
                {
                    title: "Web applications",
                    href: "/services/web-applications/",
                },
                {
                    title: "Code reviews",
                    href: "/services/ai-code-review/",
                },
            ],
        },
        {
            slug: "ai-code-review",
            title: "Code reviews for AI-built apps",
            description:
                "Code reviews for AI-built and vibe-coded projects. Understand security issues, maintainability and deployment blockers with prioritised practical findings.",
            introduction:
                "Built an application with AI tools and want another pair of eyes on it? I review the project, explain the issues that matter and help turn a working prototype into a clearer plan for the next stage.",
            sections: [
                {
                    heading: "Review the project you actually have",
                    paragraphs: [
                        "You do not need to pretend the code was written a different way. We agree the application, important user journeys and review scope. The work can look at structure, data handling, authentication, permissions, dependencies and how errors are dealt with.",
                    ],
                },
                {
                    heading: "Get findings you can act on",
                    paragraphs: [
                        "A useful review distinguishes an immediate risk or broken behavior from improvements that can wait. The deliverable is a prioritised set of findings, practical recommendations and a discussion of next steps. Fixes can be agreed as separate implementation work.",
                    ],
                },
                {
                    heading: "Look beyond the local demo",
                    paragraphs: [
                        "An app that runs on a laptop still needs deployment arrangements, secrets management and operational ownership. We identify relevant blockers and can connect the review to ADB Technology for infrastructure and deployment preparation.",
                    ],
                },
                {
                    heading: "Understand the review boundaries",
                    paragraphs: [
                        "The findings relate to the code and scope reviewed. A code review does not certify that every possible vulnerability has been eliminated. The aim is to make the important issues understandable and establish an agreed route forward.",
                    ],
                },
            ],
            included: [
                "Scoped review of AI-built or vibe-coded projects",
                "Architecture and maintainability findings",
                "Authentication, permission and data-handling checks",
                "Prioritised practical recommendations",
                "Separately agreed fixes and deployment preparation",
            ],
            related: [
                {
                    title: "App deployment & hardening",
                    href: "https://adbtechnology.co.uk/services/app-deployment/",
                },
                {
                    title: "Web applications",
                    href: "/services/web-applications/",
                },
                {
                    title: "API integrations",
                    href: "/services/api-integrations/",
                },
            ],
        },
    ],
    areas: [
        {
            slug: "manchester-software-development",
            title: "Software development in Manchester",
            description:
                "Freelance software development from Manchester: business applications, integrations, automation, mobile apps and AI-built project reviews.",
            introduction:
                "Freelance software development from Manchester: business applications, integrations, automation, mobile apps and AI-built project reviews.",
            sections: [
                {
                    heading: "Start with the business process",
                    paragraphs: [
                        "A useful software project starts with who needs it and what is happening today. We can discuss an internal tool, an integration or a mobile product and agree a scope for development.",
                    ],
                },
                {
                    heading: "Work directly with the developer",
                    paragraphs: [
                        "The work is delivered as a freelance project, with agreed responsibilities and dates. Delivery is arranged around the agreed project rather than an embedded team role.",
                    ],
                },
            ],
            services: [
                "web-applications",
                "api-integrations",
                "ai-code-review",
            ],
        },
        {
            slug: "uk-software-development",
            title: "Software development for UK businesses",
            description:
                "Remote, scoped software projects for UK businesses, delivered by a freelance developer based in Manchester.",
            introduction:
                "Remote, scoped software projects for UK businesses, delivered by a freelance developer based in Manchester.",
            sections: [
                {
                    heading:
                        "A clear project without a local office requirement",
                    paragraphs: [
                        "Requirements, demonstrations and reviews can be organised remotely. Written decisions and a defined scope help keep the implementation aligned with the people using it.",
                    ],
                },
                {
                    heading: "Include the systems around the application",
                    paragraphs: [
                        "An application may need APIs, automation and deployment work. We establish those dependencies before implementation and agree the relevant handover and ownership.",
                    ],
                },
            ],
            services: ["web-applications", "automation", "mobile-applications"],
        },
        {
            slug: "australia-software-development",
            title: "Software development for Australian businesses",
            description:
                "Discuss remote software development for an Australian business with a freelance developer based in Manchester, UK.",
            introduction:
                "Discuss remote software development for an Australian business with a freelance developer based in Manchester, UK.",
            sections: [
                {
                    heading: "Remote delivery across time zones",
                    paragraphs: [
                        "The business is based in Manchester. For Australian projects, meeting times, review arrangements and written handovers are agreed around the time difference; no Australian office is implied.",
                    ],
                },
                {
                    heading: "Scope the software and its integrations",
                    paragraphs: [
                        "Bring the process you want to improve and the systems already involved. We can assess an application, an API connection or an AI-built prototype, then agree what development or review is appropriate.",
                    ],
                },
            ],
            services: [
                "api-integrations",
                "web-applications",
                "ai-code-review",
            ],
        },
        {
            slug: "usa-software-development",
            title: "Software development for US businesses",
            description:
                "Remote business software, integrations and code reviews for US projects, delivered by a Manchester-based freelance developer.",
            introduction:
                "Remote business software, integrations and code reviews for US projects, delivered by a Manchester-based freelance developer.",
            sections: [
                {
                    heading: "Agree the working relationship first",
                    paragraphs: [
                        "Different US time zones need different meeting arrangements. The project can use written requirements and review notes alongside agreed calls, with availability and dates settled for the actual scope.",
                    ],
                },
                {
                    heading: "Build and hand over a maintainable system",
                    paragraphs: [
                        "The review includes the application’s users, data and dependencies. Hosting and deployment responsibilities need to be clear so the result is useful beyond a demonstration.",
                    ],
                },
            ],
            services: [
                "web-applications",
                "api-integrations",
                "mobile-applications",
            ],
        },
    ],
    pages: [
        {
            slug: "about",
            title: "About ADB Software Solutions",
            description:
                "Freelance software development from Manchester: applications, APIs, automation, mobile apps and code reviews for AI-built projects.",
            introduction:
                "ADB Software Solutions is a freelance business run by Adam Birds, based in Manchester.",
            sections: [
                {
                    heading: "Work directly with me",
                    paragraphs: [
                        "I build applications, integrations, automation and mobile software, and review projects created with AI tools. The starting point is the process or product you need to improve.",
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
                "How an enquiry becomes an agreed software project: scope, delivery, reviews and handover.",
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
                "Manchester-based ADB Software Solutions services, with local coverage and remote working across the UK and internationally.",
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
                "Information about contact enquiries and personal data handled through ADB Software Solutions.",
            noindex: true,
            introduction:
                "This page explains the information used when you contact ADB Software Solutions through this website.",
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
                "Cookies and browser storage used by ADB Software Solutions, including the optional dark/light theme preference.",
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
                "Website-use information for ADB Software Solutions. Project and service agreements are arranged separately.",
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
        title: "Discuss your software",
        introduction:
            "Tell me what you would like to build, improve or fix. I’ll review the enquiry and get back to you to discuss whether the work is a good fit.",
        guidance:
            "Scope, availability and delivery arrangements are agreed individually. Please do not include passwords or private credentials.",
    },
};

import { websitePolicies } from "./policies";
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
                "Business applications, integrations and code reviews from a freelance developer based in Manchester.",
            introduction:
                "Business applications, integrations and code reviews from a freelance developer based in Manchester.",
            sections: [
                {
                    heading: "Software that supports your team.",
                    paragraphs: [
                        "An internal application, a mobile product or an integration between existing tools can remove the work your team keeps repeating. I can help build it, or review an application you have already started.",
                    ],
                },
                {
                    heading: "Working directly with me.",
                    paragraphs: [
                        "I’m based in Manchester. You work directly with me on the application, its requirements and the technical decisions behind it.",
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
                "Software for the way your business works, delivered remotely across the UK.",
            introduction:
                "Software for the way your business works, delivered remotely across the UK.",
            sections: [
                {
                    heading: "Software that supports your team.",
                    paragraphs: [
                        "An internal application, a mobile product or an integration between existing tools can remove the work your team keeps repeating. I can help build it, or review an application you have already started.",
                    ],
                },
                {
                    heading: "Working directly with me.",
                    paragraphs: [
                        "The project can be reviewed through calls, demonstrations and written notes. You can see the work as it takes shape and ask questions about the decisions behind it.",
                    ],
                },
            ],
            services: ["web-applications", "automation", "mobile-applications"],
        },
        {
            slug: "australia-software-development",
            title: "Software development for Australian businesses",
            description:
                "Applications, integrations and code reviews for Australian projects, delivered from Manchester, UK.",
            introduction:
                "Applications, integrations and code reviews for Australian projects, delivered from Manchester, UK.",
            sections: [
                {
                    heading: "Software that supports your team.",
                    paragraphs: [
                        "An internal application, a mobile product or an integration between existing tools can remove the work your team keeps repeating. I can help build it, or review an application you have already started.",
                    ],
                },
                {
                    heading: "Working directly with me.",
                    paragraphs: [
                        "I work from Manchester, UK. Calls are arranged around the time difference, with demonstrations and written updates so decisions do not have to wait for the next meeting.",
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
                "Business software and application development for US projects, delivered from Manchester, UK.",
            introduction:
                "Business software and application development for US projects, delivered from Manchester, UK.",
            sections: [
                {
                    heading: "Software that supports your team.",
                    paragraphs: [
                        "An internal application, a mobile product or an integration between existing tools can remove the work your team keeps repeating. I can help build it, or review an application you have already started.",
                    ],
                },
                {
                    heading: "Working directly with me.",
                    paragraphs: [
                        "I work from Manchester, UK. Calls are arranged around the time difference, with demonstrations and written updates so decisions do not have to wait for the next meeting.",
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
                "Business software, built by the developer you speak to.",
            introduction:
                "Business software, built by the developer you speak to.",
            sections: [
                {
                    heading: "Hello, I’m Adam.",
                    paragraphs: [
                        "I’m Adam Birds, a freelance software developer based in Manchester. I build business applications, connect existing systems, automate repetitive work and develop mobile apps. I also review applications built with AI tools.",
                    ],
                },
                {
                    heading: "The work starts with what you have.",
                    paragraphs: [
                        "A spreadsheet that has become an application in all but name. Two systems that need the same information. A prototype that needs another pair of eyes. Bring the process or product you’re working on; I’ll help work out the next useful step.",
                    ],
                },
                {
                    heading: "You work directly with me.",
                    paragraphs: [
                        "I handle the technical work and the conversations about it. You can ask why a decision has been made, see the work as it develops and agree what needs to happen next. There is no account manager between you and the person building it.",
                    ],
                },
                {
                    heading: "Built to be understood.",
                    paragraphs: [
                        "Software needs to make sense to the people using it and the people looking after it. I consider permissions, data, failure handling and handover alongside the main features. Code reviews leave you with prioritised findings and practical next steps.",
                    ],
                },
                {
                    heading: "Part of the ADB businesses.",
                    paragraphs: [
                        "ADB Software Solutions covers applications and integrations. ADB Web Designs covers business websites. ADB Technology covers infrastructure and deployment. I run all three, so a project can draw on the relevant services without losing its context.",
                    ],
                },
            ],
        },
        {
            slug: "working-together",
            title: "Working together",
            description:
                "From the first conversation to a useful handover. Here’s how a project takes shape.",
            introduction:
                "From the first conversation to a useful handover. Here’s how a project takes shape.",
            sections: [
                {
                    heading: "Tell me where you are starting.",
                    paragraphs: [
                        "Describe the process, product or application you want to change. Existing screenshots, examples of the repetitive work and the systems involved are useful. You do not need to arrive with a finished specification.",
                    ],
                },
                {
                    heading: "Decide what the work needs to do.",
                    paragraphs: [
                        "We discuss the result you need, the current setup and any real deadline. I’ll put together a scope covering the work, price, responsibilities and timing. New ideas can be discussed without quietly turning the project into something else.",
                    ],
                },
                {
                    heading: "Review the important steps.",
                    paragraphs: [
                        "You’ll have opportunities to review the application and its workflows while there is still time to adjust them. I’ll explain decisions that affect the people using the software, its data or the systems connected to it.",
                    ],
                },
                {
                    heading: "Leave a setup you can use.",
                    paragraphs: [
                        "The handover includes the agreed checks, documentation and access arrangements. Further development or infrastructure work can be discussed through the relevant ADB business.",
                    ],
                },
            ],
        },
        {
            slug: "areas-served",
            title: "Manchester-based. Working further afield.",
            description:
                "Freelance software development from Manchester, for businesses across the UK and international projects.",
            introduction:
                "Freelance software development from Manchester, for businesses across the UK and international projects.",
            sections: [
                {
                    heading: "Manchester and the surrounding area.",
                    paragraphs: [
                        "I’m based in Manchester and work with businesses nearby. If your team has outgrown its tools, needs an integration or wants to turn an idea into an application, we can discuss the work directly.",
                    ],
                },
                {
                    heading: "Across the UK.",
                    paragraphs: [
                        "Most of the work can be delivered remotely. Walkthroughs, prototypes and working software make it easy to review progress from wherever your team is based.",
                    ],
                },
                {
                    heading: "Australia and the United States.",
                    paragraphs: [
                        "I’m happy to discuss projects with businesses in Australia and the US. I work from Manchester; we arrange calls around the time difference and keep decisions and progress easy to follow between meetings.",
                    ],
                },
            ],
        },
        ...websitePolicies,
    ],
    contact: {
        title: "Discuss your software",
        introduction:
            "Tell me what you would like to build, improve or fix. I’ll review the enquiry and get back to you to discuss whether the work is a good fit.",
        guidance:
            "Scope, availability and delivery arrangements are agreed individually. Please do not include passwords or private credentials.",
    },
};

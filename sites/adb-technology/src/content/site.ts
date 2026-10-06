import type { PublicSite } from "@adb/ui/public/types";

/** Edit marketing copy here. Editorial content lives in the brand-scoped CMS. */
export const site: PublicSite = {
    brand: "adb-technology",
    name: "ADB Technology",
    shortName: "Technology",
    domain: "https://adbtechnology.co.uk",
    description:
        "Freelance cloud, infrastructure and DevOps services from Manchester: migrations, pipelines, server management and app deployment.",
    kind: "technology",
    services: [
        {
            slug: "cloud-infrastructure",
            title: "Cloud & infrastructure",
            description:
                "Freelance cloud and infrastructure engineering from Manchester. Plan, build and improve the systems behind your application.",
            introduction:
                "Cloud infrastructure should fit the application and the people responsible for running it. I help plan new environments, improve existing setups and make their dependencies and ownership easier to understand.",
            sections: [
                {
                    heading: "Understand the requirements",
                    paragraphs: [
                        "We start with the application, its data, integrations and current environment. The discussion includes access, deployment, backups and operational responsibilities. Provider choice follows the requirements rather than being the starting point.",
                    ],
                },
                {
                    heading: "Build a coherent setup",
                    paragraphs: [
                        "The scope can include compute, networking, storage, databases and the configuration connecting them. Infrastructure automation can help make the setup repeatable. Access and secrets handling need clear boundaries from the beginning.",
                    ],
                },
                {
                    heading: "Document the resulting environment",
                    paragraphs: [
                        "A handover should explain the components, configuration and agreed management tasks. Monitoring and recovery arrangements are chosen for the application. Ongoing work is agreed separately, without an assumed core-hours support service.",
                    ],
                },
            ],
            included: [
                "Infrastructure planning and setup",
                "Cloud environment improvements",
                "Networking, storage and related configuration",
                "Infrastructure automation",
                "Documented access and operational ownership",
            ],
            related: [
                {
                    title: "Cloud migrations",
                    href: "/services/cloud-migrations/",
                },
                {
                    title: "Server management",
                    href: "/services/server-management/",
                },
                {
                    title: "App deployment",
                    href: "/services/app-deployment/",
                },
            ],
        },
        {
            slug: "cloud-migrations",
            title: "Cloud & infrastructure migrations",
            description:
                "Plan and carry out cloud, hosting and infrastructure migrations with dependency checks, cutover arrangements and documented handover.",
            introduction:
                "A migration involves more than moving files to a different server. I help work through the application, data and surrounding services, then plan and carry out the agreed move.",
            sections: [
                {
                    heading: "Inventory what needs to move",
                    paragraphs: [
                        "The starting point is the current environment and its dependencies: databases, scheduled jobs, external integrations, domain configuration and access. We identify what can be moved, what needs changing and what is outside the project.",
                    ],
                },
                {
                    heading: "Agree the migration and cutover",
                    paragraphs: [
                        "The plan covers the target setup, data movement, verification and the transition between environments. Any disruption, timing constraints and rollback arrangements need explicit agreement. They should not be discovered during the cutover.",
                    ],
                },
                {
                    heading: "Verify and hand over",
                    paragraphs: [
                        "After the move, checks should reflect the application’s important behavior and dependencies. The handover documents the new setup and its management responsibilities. Further improvements can be scoped once the migration is understood.",
                    ],
                },
            ],
            included: [
                "Current-environment and dependency review",
                "Target environment planning",
                "Application and database migration work",
                "Agreed cutover, verification and rollback arrangements",
                "Migration documentation and handover",
            ],
            related: [
                {
                    title: "Cloud & infrastructure",
                    href: "/services/cloud-infrastructure/",
                },
                {
                    title: "Server rebuilds",
                    href: "/services/server-rebuilds/",
                },
                {
                    title: "Deployment pipelines",
                    href: "/services/deployment-pipelines/",
                },
            ],
        },
        {
            slug: "devops",
            title: "DevOps & delivery improvements",
            description:
                "Freelance DevOps project work: infrastructure automation, repeatable deployments and practical delivery improvements, delivered as scoped freelance project work.",
            introduction:
                "If releases rely on undocumented steps or the environment is difficult to reproduce, there is usually useful work to do around delivery. I help improve the route from application code to a running service.",
            sections: [
                {
                    heading: "Review the existing workflow",
                    paragraphs: [
                        "We look at how changes are built, tested, released and operated today. That includes repositories, environments, configuration and the decisions people make manually. The first improvement should address a real delivery problem.",
                    ],
                },
                {
                    heading: "Make agreed steps repeatable",
                    paragraphs: [
                        "The work can include infrastructure automation, environment configuration and deployment improvements. Building a pipeline is one part of the process; the checks and permissions around it matter too. The tools should suit the team and application.",
                    ],
                },
                {
                    heading: "Leave the process usable",
                    paragraphs: [
                        "Delivery documentation should explain how to release, identify a failure and recover from an unsuccessful change. Responsibilities and follow-up work are agreed clearly. This is scoped technical work, not an offer to join a team as a contractor.",
                    ],
                },
            ],
            included: [
                "Delivery workflow reviews",
                "Infrastructure and environment automation",
                "Repeatable release processes",
                "Agreed validation and recovery steps",
                "Team-usable documentation",
            ],
            related: [
                {
                    title: "Deployment pipelines",
                    href: "/services/deployment-pipelines/",
                },
                {
                    title: "App deployment",
                    href: "/services/app-deployment/",
                },
                {
                    title: "Cloud & infrastructure",
                    href: "/services/cloud-infrastructure/",
                },
            ],
        },
        {
            slug: "deployment-pipelines",
            title: "Deployment pipelines & CI/CD",
            description:
                "Build and improve deployment pipelines with appropriate testing, secrets handling, environment separation and documented release steps.",
            introduction:
                "A deployment pipeline should make releases easier to understand and repeat. I build or improve CI/CD pipelines around the repository, application and environments you actually use.",
            sections: [
                {
                    heading: "Decide what a release needs",
                    paragraphs: [
                        "We review the build, useful checks, required artefacts and the target environment. Some releases need approvals or a controlled rollout. Those decisions shape the pipeline rather than being added after automation is already in place.",
                    ],
                },
                {
                    heading: "Handle environments and access",
                    paragraphs: [
                        "Pipeline credentials, deployment permissions and configuration need to be managed carefully. The scope can include separation between environments and an appropriate way to supply secrets. Workflow permissions should match the jobs being carried out.",
                    ],
                },
                {
                    heading: "Make failures understandable",
                    paragraphs: [
                        "The pipeline should leave useful output and an agreed recovery path. Documentation explains how to start a release, investigate a failed run and restore an earlier version where that is supported. Database changes need their own considered approach.",
                    ],
                },
            ],
            included: [
                "Build, test and release workflow configuration",
                "Suitable CI/CD tooling and GitHub Actions integration",
                "Secrets and deployment permission setup",
                "Agreed approval and environment boundaries",
                "Release and recovery documentation",
            ],
            related: [
                {
                    title: "DevOps improvements",
                    href: "/services/devops/",
                },
                {
                    title: "App deployment",
                    href: "/services/app-deployment/",
                },
                {
                    title: "Code reviews",
                    href: "https://adbsoftwaresolutions.co.uk/services/ai-code-review/",
                },
            ],
        },
        {
            slug: "server-management",
            title: "Server management",
            description:
                "Agreed server administration, configuration and upkeep from a freelance engineer. Clear responsibilities and agreed response arrangements.",
            introduction:
                "Servers need understood configuration and someone responsible for the agreed management tasks. I help administer and improve server environments, with the work and ongoing arrangements defined for the setup.",
            sections: [
                {
                    heading: "Establish the current condition",
                    paragraphs: [
                        "We review the server roles, installed services, access and dependencies. Existing problems may need a separate repair or rebuild before ordinary upkeep is appropriate. Documentation provides a starting point for changes.",
                    ],
                },
                {
                    heading: "Agree management responsibilities",
                    paragraphs: [
                        "The scope may include configuration, updates, service administration and agreed backup or monitoring arrangements. The platform and workload determine the tasks. Application maintenance and infrastructure management should have clear ownership.",
                    ],
                },
                {
                    heading: "Plan changes and follow-up",
                    paragraphs: [
                        "Changes need appropriate checks and a record of what was done. Availability and response arrangements are discussed directly. Server management does not automatically include a core-hours helpdesk, emergency response or round-the-clock cover.",
                    ],
                },
            ],
            included: [
                "Server configuration and administration",
                "Agreed operating-system and service updates",
                "Access and configuration improvements",
                "Scoped monitoring and backup arrangements",
                "Documented ongoing responsibilities",
            ],
            related: [
                {
                    title: "Server rebuilds",
                    href: "/services/server-rebuilds/",
                },
                {
                    title: "Cloud & infrastructure",
                    href: "/services/cloud-infrastructure/",
                },
                {
                    title: "Deployment pipelines",
                    href: "/services/deployment-pipelines/",
                },
            ],
        },
        {
            slug: "server-rebuilds",
            title: "Server rebuilds",
            description:
                "Rebuild servers and redeploy their required services with dependency review, configuration planning and documented verification.",
            introduction:
                "When a server is no longer a sensible foundation, a rebuild can be better than continuing to patch an unclear setup. I help establish what needs to be restored or redeployed and carry out the agreed rebuild.",
            sections: [
                {
                    heading: "Identify the required services",
                    paragraphs: [
                        "The work starts with the server roles, application data, configuration, access and external dependencies. Available backups and documentation affect the recovery options. We agree what is required before replacing the environment.",
                    ],
                },
                {
                    heading: "Rebuild with an understood configuration",
                    paragraphs: [
                        "The new setup can include a clean operating system, required services, access configuration and deployment arrangements. Where useful, repeatable configuration avoids recreating another undocumented server.",
                    ],
                },
                {
                    heading: "Check the result and ownership",
                    paragraphs: [
                        "Verification should cover the services and application behavior the business depends on. The handover explains the resulting setup, important configuration and management responsibilities. Scheduling and any interruption are agreed as part of the project.",
                    ],
                },
            ],
            included: [
                "Server-role and dependency inventory",
                "Agreed rebuild and service redeployment",
                "Configuration and access setup",
                "Application/data restoration arrangements",
                "Verification and documentation",
            ],
            related: [
                {
                    title: "Server management",
                    href: "/services/server-management/",
                },
                {
                    title: "Cloud migrations",
                    href: "/services/cloud-migrations/",
                },
                {
                    title: "App deployment",
                    href: "/services/app-deployment/",
                },
            ],
        },
        {
            slug: "app-deployment",
            title: "App deployment & security hardening",
            description:
                "Prepare and deploy existing apps, including AI-built projects, with agreed infrastructure, secrets, delivery, monitoring and security hardening.",
            introduction:
                "You have an app that works locally. Now it needs an environment, configuration and a deployment process. I help prepare and deploy existing applications, including projects built with AI tools.",
            sections: [
                {
                    heading: "Check what the application needs",
                    paragraphs: [
                        "We review the runtime, database, background work, uploads and external integrations. Application code or permission issues may need a review and fixes through ADB Software Solutions before the operational setup is ready.",
                    ],
                },
                {
                    heading: "Prepare the production environment",
                    paragraphs: [
                        "The agreed work can include hosting, environment and secret configuration, domains and TLS, access controls and deployment pipelines. The scope should fit the application with the tools and environments chosen for its actual requirements.",
                    ],
                },
                {
                    heading: "Agree the operational arrangements",
                    paragraphs: [
                        "Logging, monitoring, backups and recovery need ownership. The handover explains how the app is deployed and what needs maintaining afterwards. Ongoing service arrangements are agreed separately; launch work does not imply core-hours support.",
                    ],
                },
                {
                    heading: "Be clear about hardening",
                    paragraphs: [
                        "Hardening addresses the configuration and issues within the agreed scope. Findings, changes and any remaining work are documented clearly so the next steps are understood.",
                    ],
                },
            ],
            included: [
                "Application deployment-readiness review",
                "Hosting, domains/TLS and environment setup",
                "Secrets and infrastructure access configuration",
                "Agreed pipelines, monitoring, backups and recovery",
                "Documented deployment and handover",
            ],
            related: [
                {
                    title: "Code reviews for AI-built apps",
                    href: "https://adbsoftwaresolutions.co.uk/services/ai-code-review/",
                },
                {
                    title: "Deployment pipelines",
                    href: "/services/deployment-pipelines/",
                },
                {
                    title: "Cloud & infrastructure",
                    href: "/services/cloud-infrastructure/",
                },
            ],
        },
    ],
    areas: [
        {
            slug: "manchester-cloud-devops",
            title: "Cloud & DevOps services in Manchester",
            description:
                "Freelance cloud, infrastructure and DevOps project work from Manchester, including migrations, pipelines and server management.",
            introduction:
                "Freelance cloud, infrastructure and DevOps project work from Manchester, including migrations, pipelines and server management.",
            sections: [
                {
                    heading: "A technical project with a defined outcome",
                    paragraphs: [
                        "A new environment, an unclear release process or a server rebuild can be scoped around the setup you actually have. We first identify the application and infrastructure dependencies.",
                    ],
                },
                {
                    heading: "Clear operational ownership",
                    paragraphs: [
                        "The work includes agreed documentation and handover. Ongoing administration can be discussed, without assuming core-hours technical support or an embedded contractor role.",
                    ],
                },
            ],
            services: [
                "cloud-infrastructure",
                "deployment-pipelines",
                "server-rebuilds",
            ],
        },
        {
            slug: "uk-cloud-devops",
            title: "Cloud & DevOps services for UK businesses",
            description:
                "Remote infrastructure, migrations and deployment project work for UK businesses from a freelance engineer based in Manchester.",
            introduction:
                "Remote infrastructure, migrations and deployment project work for UK businesses from a freelance engineer based in Manchester.",
            sections: [
                {
                    heading: "Work through the environment remotely",
                    paragraphs: [
                        "Infrastructure work can be planned around a review of the existing setup, agreed access and a documented change plan. The scope should explain what changes and how the result will be checked.",
                    ],
                },
                {
                    heading: "Plan the cutover and recovery",
                    paragraphs: [
                        "Migrations and deployments may need a specific schedule. Timing constraints, verification and recovery arrangements are agreed directly rather than inferred from a service page.",
                    ],
                },
            ],
            services: ["cloud-migrations", "devops", "server-management"],
        },
        {
            slug: "australia-cloud-devops",
            title: "Cloud & DevOps work for Australian businesses",
            description:
                "Discuss remote infrastructure and deployment work for an Australian business with a freelance engineer based in Manchester, UK.",
            introduction:
                "Discuss remote infrastructure and deployment work for an Australian business with a freelance engineer based in Manchester, UK.",
            sections: [
                {
                    heading: "Coordinate the technical work across time zones",
                    paragraphs: [
                        "The business operates from Manchester, not an Australian office. Access, change windows and handover arrangements must be agreed for the project, particularly where a migration affects a running application.",
                    ],
                },
                {
                    heading: "Prepare an application for its environment",
                    paragraphs: [
                        "The work can include cloud setup, deployment pipelines and agreed security hardening. Existing code issues can be reviewed through ADB Software Solutions before the deployment is carried out.",
                    ],
                },
            ],
            services: [
                "app-deployment",
                "deployment-pipelines",
                "cloud-migrations",
            ],
        },
        {
            slug: "usa-cloud-devops",
            title: "Cloud & DevOps work for US businesses",
            description:
                "Remote infrastructure, server and deployment projects for US businesses, delivered by a freelance engineer based in Manchester.",
            introduction:
                "Remote infrastructure, server and deployment projects for US businesses, delivered by a freelance engineer based in Manchester.",
            sections: [
                {
                    heading: "Agree the operational boundaries",
                    paragraphs: [
                        "We define the environment, permissions and change responsibilities before starting work. Meeting times and any change windows are arranged around the project and time difference.",
                    ],
                },
                {
                    heading: "Leave a documented setup",
                    paragraphs: [
                        "The resulting environment and release process should be understandable to its owner. The scope can include migration, server rebuilding or application deployment, with ongoing responsibilities agreed separately.",
                    ],
                },
            ],
            services: [
                "cloud-infrastructure",
                "server-rebuilds",
                "app-deployment",
            ],
        },
    ],
    pages: [
        {
            slug: "about",
            title: "About ADB Technology",
            description:
                "Freelance cloud, infrastructure and DevOps services from Manchester: migrations, pipelines, server management and app deployment.",
            introduction:
                "ADB Technology is a freelance business run by Adam Birds, based in Manchester.",
            sections: [
                {
                    heading: "Work directly with me",
                    paragraphs: [
                        "I work on cloud infrastructure, migrations, deployment pipelines, server management and rebuilds. Projects include agreed documentation and operational ownership rather than an implied core-hours helpdesk.",
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
                "How an enquiry becomes an agreed technical setup project: scope, delivery, reviews and handover.",
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
                "Manchester-based ADB Technology services, with local coverage and remote working across the UK and internationally.",
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
                "Information about contact enquiries and personal data handled through ADB Technology.",
            noindex: true,
            introduction:
                "This page explains the information used when you contact ADB Technology through this website.",
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
                "Cookies and browser storage used by ADB Technology, including the optional dark/light theme preference.",
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
                "Website-use information for ADB Technology. Project and service agreements are arranged separately.",
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
        title: "Discuss your technical setup",
        introduction:
            "Tell me what you would like to build, improve or fix. I’ll review the enquiry and get back to you to discuss whether the work is a good fit.",
        guidance:
            "Scope, availability and delivery arrangements are agreed individually. Please do not include passwords or private credentials.",
    },
};

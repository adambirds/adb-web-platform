import { websitePolicies } from "./policies";
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
            title: "Cloud & DevOps in Manchester",
            description:
                "Cloud environments, migrations and deployment pipelines from a freelance engineer based in Manchester.",
            introduction:
                "Cloud environments, migrations and deployment pipelines from a freelance engineer based in Manchester.",
            sections: [
                {
                    heading: "Work on the environment you actually run.",
                    paragraphs: [
                        "The work can cover a new cloud environment, a migration, a release pipeline or an existing server that needs attention. We look at the application, its dependencies and how it is managed before deciding what to change.",
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
                "cloud-infrastructure",
                "deployment-pipelines",
                "server-management",
            ],
        },
        {
            slug: "uk-cloud-devops",
            title: "Cloud & DevOps for UK businesses",
            description:
                "Infrastructure and DevOps projects for UK businesses: build, migrate, deploy and manage.",
            introduction:
                "Infrastructure and DevOps projects for UK businesses: build, migrate, deploy and manage.",
            sections: [
                {
                    heading: "Work on the environment you actually run.",
                    paragraphs: [
                        "The work can cover a new cloud environment, a migration, a release pipeline or an existing server that needs attention. We look at the application, its dependencies and how it is managed before deciding what to change.",
                    ],
                },
                {
                    heading: "Working directly with me.",
                    paragraphs: [
                        "The project can be reviewed through calls, demonstrations and written notes. You can see the work as it takes shape and ask questions about the decisions behind it.",
                    ],
                },
            ],
            services: ["cloud-migrations", "server-rebuilds", "app-deployment"],
        },
        {
            slug: "australia-cloud-devops",
            title: "Cloud & DevOps for Australian businesses",
            description:
                "Cloud infrastructure and DevOps work for Australian projects, delivered from Manchester, UK.",
            introduction:
                "Cloud infrastructure and DevOps work for Australian projects, delivered from Manchester, UK.",
            sections: [
                {
                    heading: "Work on the environment you actually run.",
                    paragraphs: [
                        "The work can cover a new cloud environment, a migration, a release pipeline or an existing server that needs attention. We look at the application, its dependencies and how it is managed before deciding what to change.",
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
                "cloud-infrastructure",
                "cloud-migrations",
                "deployment-pipelines",
            ],
        },
        {
            slug: "usa-cloud-devops",
            title: "Cloud & DevOps for US businesses",
            description:
                "Infrastructure, deployment and server projects for US businesses, delivered from Manchester, UK.",
            introduction:
                "Infrastructure, deployment and server projects for US businesses, delivered from Manchester, UK.",
            sections: [
                {
                    heading: "Work on the environment you actually run.",
                    paragraphs: [
                        "The work can cover a new cloud environment, a migration, a release pipeline or an existing server that needs attention. We look at the application, its dependencies and how it is managed before deciding what to change.",
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
                "app-deployment",
                "deployment-pipelines",
                "server-management",
            ],
        },
    ],
    pages: [
        {
            slug: "about",
            title: "About ADB Technology",
            description:
                "Infrastructure work, with the engineer who builds it.",
            introduction:
                "Infrastructure work, with the engineer who builds it.",
            sections: [
                {
                    heading: "Hello, I’m Adam.",
                    paragraphs: [
                        "I’m Adam Birds, a freelance infrastructure and DevOps engineer based in Manchester. I work on cloud environments, deployment pipelines, migrations and servers. That can mean building a new environment, moving an application or putting an existing setup into better shape.",
                    ],
                },
                {
                    heading: "The work starts with what you have.",
                    paragraphs: [
                        "An application waiting to go live. A server that needs rebuilding. A release process that still depends on someone remembering every step. We can start with the setup you have and the part you want to change.",
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
                        "You should be able to understand how an application is released, where its configuration lives and what to do when something goes wrong. Documentation, rollback and ownership are part of the work, rather than details left until after deployment.",
                    ],
                },
                {
                    heading: "Part of the ADB businesses.",
                    paragraphs: [
                        "ADB Technology covers infrastructure and deployment. ADB Software Solutions covers applications and integrations. ADB Web Designs covers business websites. I run all three, so a project can draw on the relevant services without losing its context.",
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
                        "Tell me what runs today, where it runs and what you want to change. A deployment problem, a move to another host or a server rebuild are all useful starting points. Keep passwords and access tokens out of the enquiry form.",
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
                        "We agree changes before they are applied, including downtime, backups and rollback where relevant. For migrations and releases, the plan includes checks before and after the change, not just the command that starts it.",
                    ],
                },
                {
                    heading: "Leave a setup you can use.",
                    paragraphs: [
                        "The handover explains the environment, the release process and who looks after each part. Server management can be agreed separately. These are scheduled freelance services, not a core-hours helpdesk or a promise of round-the-clock response.",
                    ],
                },
            ],
        },
        {
            slug: "areas-served",
            title: "Manchester-based. Working further afield.",
            description:
                "Freelance infrastructure and DevOps from Manchester, for businesses across the UK and international projects.",
            introduction:
                "Freelance infrastructure and DevOps from Manchester, for businesses across the UK and international projects.",
            sections: [
                {
                    heading: "Manchester and the surrounding area.",
                    paragraphs: [
                        "I’m based in Manchester and work with businesses nearby. If you need a cloud environment, a more dependable release process or help moving and rebuilding servers, we can discuss the setup directly.",
                    ],
                },
                {
                    heading: "Across the UK.",
                    paragraphs: [
                        "Most of the work can be delivered remotely. Planning, configuration, release checks and handover can all be organised remotely. The important part is understanding the environment and the people responsible for it.",
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
        title: "Discuss your technical setup",
        introduction:
            "Tell me what you would like to build, improve or fix. I’ll review the enquiry and get back to you to discuss whether the work is a good fit.",
        guidance:
            "Scope, availability and delivery arrangements are agreed individually. Please do not include passwords or private credentials.",
    },
};

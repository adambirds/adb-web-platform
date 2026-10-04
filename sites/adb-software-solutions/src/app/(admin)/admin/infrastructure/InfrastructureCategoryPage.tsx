import { Container } from "@/components/ui";
import { InfrastructureResourcesWorkspace } from "./resources/InfrastructureResourcesWorkspace";

export const INFRASTRUCTURE_CATEGORIES = {
    "provider-accounts": {
        title: "Provider Accounts",
        resourceType: "provider_account",
        description:
            "Vendor accounts, tenants and projects linked to your infrastructure.",
    },
    servers: {
        title: "Servers",
        resourceType: "server",
        description:
            "Compute hosts, operating systems and infrastructure relationships.",
    },
    databases: {
        title: "Databases",
        resourceType: "database_instance",
        description: "Database services, versions and related resources.",
    },
    websites: {
        title: "Websites",
        resourceType: "website",
        description:
            "Managed web properties, endpoints and hosting relationships.",
    },
    domains: {
        title: "Domains",
        resourceType: "domain",
        description:
            "Domain registrations, expiry dates and DNS relationships.",
    },
    "ssl-certificates": {
        title: "SSL Certificates",
        resourceType: "tls_certificate",
        description:
            "Certificate validity, expiry dates and deployment relationships.",
    },
    applications: {
        title: "Applications",
        resourceType: "application",
        description:
            "Application workspaces, environments and source repositories.",
    },
    licences: {
        title: "Licences",
        resourceType: "licence",
        description: "Software licences and subscription resources.",
    },
    "mobile-apps": {
        title: "Mobile Apps",
        resourceType: "mobile_app",
        description:
            "Mobile application resources and technical relationships.",
    },
    apis: {
        title: "APIs",
        resourceType: "api",
        description: "API resources and service dependencies.",
    },
    bots: {
        title: "Bots",
        resourceType: "bot",
        description: "Automation resources and their technical dependencies.",
    },
    "email-systems": {
        title: "Email Systems",
        resourceType: "email_system",
        description: "Email service resources and configuration relationships.",
    },
} as const;

export type InfrastructureCategory = keyof typeof INFRASTRUCTURE_CATEGORIES;

export function InfrastructureCategoryPage({
    category,
}: {
    category: InfrastructureCategory;
}) {
    const configuration = INFRASTRUCTURE_CATEGORIES[category];
    return (
        <Container className="py-8">
            <InfrastructureResourcesWorkspace
                resourceTypeFilter={configuration.resourceType}
                title={configuration.title}
                description={configuration.description}
            />
        </Container>
    );
}

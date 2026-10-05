import { Container } from "@/components/ui";
import { InfrastructureResourcesWorkspace } from "./resources/InfrastructureResourcesWorkspace";

export const INFRASTRUCTURE_CATEGORIES = {
    "other-resources": {
        title: "Other resources",
        resourceType: "other",
        description:
            "Browse, create and manage other resources in your Client/Internal scope.",
    },
    "network-devices": {
        title: "Network devices",
        resourceType: "network_device",
        description:
            "Browse, create and manage network devices in your Client/Internal scope.",
    },
    "scheduled-jobs": {
        title: "Scheduled jobs",
        resourceType: "scheduled_job",
        description:
            "Browse, create and manage scheduled jobs in your Client/Internal scope.",
    },
    "system-services": {
        title: "System services",
        resourceType: "system_service",
        description:
            "Browse, create and manage system services in your Client/Internal scope.",
    },
    "kubernetes-workloads": {
        title: "Kubernetes workloads",
        resourceType: "kubernetes_workload",
        description:
            "Browse, create and manage kubernetes workloads in your Client/Internal scope.",
    },
    "kubernetes-namespaces": {
        title: "Kubernetes namespaces",
        resourceType: "kubernetes_namespace",
        description:
            "Browse, create and manage kubernetes namespaces in your Client/Internal scope.",
    },
    "kubernetes-clusters": {
        title: "Kubernetes clusters",
        resourceType: "kubernetes_cluster",
        description:
            "Browse, create and manage kubernetes clusters in your Client/Internal scope.",
    },
    "container-stacks": {
        title: "Container stacks",
        resourceType: "container_stack",
        description:
            "Browse, create and manage container stacks in your Client/Internal scope.",
    },
    "backup-plans": {
        title: "Backup plans",
        resourceType: "backup_plan",
        description:
            "Browse, create and manage backup plans in your Client/Internal scope.",
    },
    storage: {
        title: "Storage",
        resourceType: "storage",
        description:
            "Browse, create and manage storage in your Client/Internal scope.",
    },
    "dns-zones": {
        title: "DNS zones",
        resourceType: "dns_zone",
        description:
            "Browse, create and manage dns zones in your Client/Internal scope.",
    },
    "website-endpoints": {
        title: "Website endpoints",
        resourceType: "website_endpoint",
        description:
            "Browse, create and manage website endpoints in your Client/Internal scope.",
    },
    "application-environments": {
        title: "Application environments",
        resourceType: "application_environment",
        description:
            "Browse, create and manage application environments in your Client/Internal scope.",
    },
    "logical-databases": {
        title: "Logical databases",
        resourceType: "logical_database",
        description:
            "Browse, create and manage logical databases in your Client/Internal scope.",
    },
    repositories: {
        title: "Source repositories",
        resourceType: "source_repository",
        description:
            "Browse, create and manage source repositories in your Client/Internal scope.",
    },
    subnets: {
        title: "Subnets",
        resourceType: "subnet",
        description:
            "Browse, create and manage subnets in your Client/Internal scope.",
    },
    networks: {
        title: "Networks",
        resourceType: "network",
        description:
            "Browse, create and manage networks in your Client/Internal scope.",
    },
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

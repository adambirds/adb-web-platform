export const RESOURCE_CREATION = {
    server: {
        label: "Server",
        family: "compute",
        permission: "add_serverprofile",
    },
    network: { label: "Network", family: "compute", permission: "add_network" },
    subnet: { label: "Subnet", family: "compute", permission: "add_subnet" },
    database_instance: {
        label: "Database instance",
        family: "data",
        permission: "add_databaseinstance",
    },
    logical_database: {
        label: "Logical database",
        family: "data",
        permission: "add_logicaldatabase",
    },
    application: {
        label: "Application",
        family: "data",
        permission: "add_applicationprofile",
    },
    application_environment: {
        label: "Application environment",
        family: "data",
        permission: "add_applicationenvironment",
    },
    source_repository: {
        label: "Source repository",
        family: "data",
        permission: "add_sourcerepository",
    },
    website: {
        label: "Website",
        family: "web",
        permission: "add_websiteprofile",
    },
    website_endpoint: {
        label: "Website endpoint",
        family: "web",
        permission: "add_websiteendpoint",
    },
    domain: { label: "Domain", family: "web", permission: "add_domainprofile" },
    dns_zone: { label: "DNS zone", family: "web", permission: "add_dnszone" },
    tls_certificate: {
        label: "TLS certificate",
        family: "web",
        permission: "add_tlscertificate",
    },
    provider_account: {
        label: "Provider account",
        family: "catalogue",
        permission: "add_provideraccount",
    },
    storage: {
        label: "Storage",
        family: "operational",
        permission: "add_storageprofile",
    },
    backup_plan: {
        label: "Backup plan",
        family: "operational",
        permission: "add_backupplanprofile",
    },
    container_stack: {
        label: "Container stack",
        family: "operational",
        permission: "add_containerstackprofile",
    },
    kubernetes_cluster: {
        label: "Kubernetes cluster",
        family: "operational",
        permission: "add_kubernetesclusterprofile",
    },
    kubernetes_namespace: {
        label: "Kubernetes namespace",
        family: "operational",
        permission: "add_kubernetesnamespaceprofile",
    },
    kubernetes_workload: {
        label: "Kubernetes workload",
        family: "operational",
        permission: "add_kubernetesworkloadprofile",
    },
    system_service: {
        label: "System service",
        family: "operational",
        permission: "add_systemserviceprofile",
    },
    scheduled_job: {
        label: "Scheduled job",
        family: "operational",
        permission: "add_scheduledjobprofile",
    },
    api: { label: "API", family: "catalogue", permission: null },
    bot: { label: "Bot", family: "catalogue", permission: null },
    mobile_app: { label: "Mobile app", family: "catalogue", permission: null },
    licence: { label: "Licence", family: "catalogue", permission: null },
    email_system: {
        label: "Email system",
        family: "catalogue",
        permission: null,
    },
    network_device: {
        label: "Network device",
        family: "catalogue",
        permission: null,
    },
    other: { label: "Other", family: "catalogue", permission: null },
} as const;

export type CreatableResourceType = keyof typeof RESOURCE_CREATION;
export const RESOURCE_TYPES = Object.keys(
    RESOURCE_CREATION,
) as CreatableResourceType[];
export const BASIC_RESOURCE_TYPES = [
    "api",
    "bot",
    "mobile_app",
    "licence",
    "email_system",
    "network_device",
    "other",
] as const;
export type CatalogueResourceType =
    (typeof BASIC_RESOURCE_TYPES)[number] | "provider_account";
export function isCatalogueResourceType(
    value: string,
): value is CatalogueResourceType {
    return (
        value === "provider_account" ||
        BASIC_RESOURCE_TYPES.some((type) => type === value)
    );
}

export function canCreateResource(
    type: CreatableResourceType,
    hasPermission: (permission: string) => boolean,
): boolean {
    const permission = RESOURCE_CREATION[type].permission;
    return (
        hasPermission("infrastructure.view_infrastructureresource") &&
        hasPermission("infrastructure.add_infrastructureresource") &&
        (!permission || hasPermission(`infrastructure.${permission}`)) &&
        (type !== "provider_account" ||
            hasPermission("infrastructure.view_serviceprovider"))
    );
}

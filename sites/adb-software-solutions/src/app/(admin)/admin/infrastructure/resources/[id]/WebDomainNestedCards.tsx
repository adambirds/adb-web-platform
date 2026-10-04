"use client";

import { Button, Card, Input, Select } from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

interface ScopedOption {
    resource_id: number;
    name: string;
    ownership_type: string;
    client_id: number | null;
    client_name: string | null;
}

interface ApplicationEnvironmentOption extends ScopedOption {
    application_name: string;
    environment: string;
}

interface DomainOption extends ScopedOption {
    domain_name: string;
}

interface TLSCertificateOption extends ScopedOption {
    subject_common_name: string;
}

interface WebDomainOptions {
    application_environments: ApplicationEnvironmentOption[];
    domains: DomainOption[];
    tls_certificates: TLSCertificateOption[];
}

interface WebsiteEndpoint {
    resource_id: number;
    name: string;
    application_environment_resource_id: number | null;
    application_environment_name: string | null;
    domain_resource_id: number | null;
    domain_name: string | null;
    tls_certificate_resource_id: number | null;
    tls_certificate_name: string | null;
    url: string;
    role: string;
    is_primary: boolean;
    redirects_to: string;
}

interface DNSRecord {
    id: number;
    name: string;
    record_type: string;
    value: string;
    ttl: number;
    priority: number | null;
    weight: number | null;
    port: number | null;
    proxied: boolean | null;
    provider_record_id: string;
}

interface TLSCertificateDomain {
    id: number;
    domain_resource_id: number;
    domain_name: string;
    is_primary: boolean;
}

interface OwnedNestedCardProps {
    resourceId: number;
    ownershipType: string;
    clientId: number | null;
}

interface WebsiteEndpointsCardProps extends OwnedNestedCardProps {
    environment: string;
    criticality: string;
}

function label(value: string): string {
    const special: Record<string, string> = {
        api: "API",
        dns_zone: "DNS zone",
        tls_certificate: "TLS certificate",
    };
    return (
        special[value] ??
        `${value.charAt(0).toUpperCase()}${value.slice(1).replaceAll("_", " ")}`
    );
}

function optionAllowed(
    option: ScopedOption,
    ownershipType: string,
    clientId: number | null,
): boolean {
    if (ownershipType === "internal")
        return option.ownership_type === "internal";
    return (
        option.ownership_type === "internal" || option.client_id === clientId
    );
}

function numberOrNull(value: string): number | null {
    const trimmed = value.trim();
    return trimmed ? Number(trimmed) : null;
}

function triStatePayload(value: string): boolean | null {
    return value === "true" ? true : value === "false" ? false : null;
}

export function WebsiteEndpointsCard({
    resourceId,
    ownershipType,
    clientId,
    environment,
    criticality,
}: WebsiteEndpointsCardProps) {
    const { hasPermission } = useAuth();
    const canView =
        hasPermission("infrastructure.view_websiteprofile") &&
        hasPermission("infrastructure.view_websiteendpoint");
    const canAdd =
        hasPermission("infrastructure.add_infrastructureresource") &&
        hasPermission("infrastructure.add_websiteendpoint");
    const canArchive =
        hasPermission("infrastructure.change_infrastructureresource") &&
        hasPermission("infrastructure.change_websiteendpoint");

    const [endpoints, setEndpoints] = useState<WebsiteEndpoint[]>([]);
    const [options, setOptions] = useState<WebDomainOptions | null>(null);
    const [showForm, setShowForm] = useState(false);
    const [name, setName] = useState("");
    const [url, setUrl] = useState("");
    const [role, setRole] = useState("primary");
    const [applicationEnvironmentId, setApplicationEnvironmentId] =
        useState("");
    const [domainId, setDomainId] = useState("");
    const [certificateId, setCertificateId] = useState("");
    const [redirectsTo, setRedirectsTo] = useState("");
    const [isPrimary, setIsPrimary] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [archivingId, setArchivingId] = useState<number | null>(null);

    const load = useCallback(async () => {
        if (!canView) return;
        try {
            setError(null);
            setEndpoints(
                (await fetchAPI(
                    `${API_URL}/api/admin/infrastructure/websites/${resourceId}/endpoints`,
                )) as WebsiteEndpoint[],
            );
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "Unable to load website endpoints.",
            );
        }
    }, [canView, resourceId]);

    useEffect(() => {
        void load();
    }, [load]);

    useEffect(() => {
        setShowForm(false);
        setOptions(null);
        setName("");
        setUrl("");
        setRole("primary");
        setApplicationEnvironmentId("");
        setDomainId("");
        setCertificateId("");
        setRedirectsTo("");
        setIsPrimary(false);
        setError(null);
    }, [resourceId]);

    const applicationEnvironments = useMemo(
        () =>
            options?.application_environments.filter((option) =>
                optionAllowed(option, ownershipType, clientId),
            ) ?? [],
        [clientId, options, ownershipType],
    );
    const domains = useMemo(
        () =>
            options?.domains.filter((option) =>
                optionAllowed(option, ownershipType, clientId),
            ) ?? [],
        [clientId, options, ownershipType],
    );
    const certificates = useMemo(
        () =>
            options?.tls_certificates.filter((option) =>
                optionAllowed(option, ownershipType, clientId),
            ) ?? [],
        [clientId, options, ownershipType],
    );

    async function openForm() {
        setShowForm(true);
        setError(null);
        if (options) return;
        try {
            setOptions(
                (await fetchAPI(
                    `${API_URL}/api/admin/infrastructure/web-domain-options`,
                )) as WebDomainOptions,
            );
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "Unable to load website endpoint options.",
            );
        }
    }

    function resetForm() {
        setShowForm(false);
        setName("");
        setUrl("");
        setRole("primary");
        setApplicationEnvironmentId("");
        setDomainId("");
        setCertificateId("");
        setRedirectsTo("");
        setIsPrimary(false);
    }

    async function createEndpoint() {
        if (!name.trim() || !url.trim()) {
            setError("Enter an endpoint name and URL.");
            return;
        }
        try {
            setIsSaving(true);
            setError(null);
            await fetchAPI(
                `${API_URL}/api/admin/infrastructure/website-endpoints`,
                {
                    method: "POST",
                    body: JSON.stringify({
                        ownership_type: ownershipType,
                        client_id: ownershipType === "client" ? clientId : null,
                        name: name.trim(),
                        lifecycle_status: "active",
                        environment,
                        criticality,
                        description: "",
                        website_resource_id: resourceId,
                        application_environment_resource_id: numberOrNull(
                            applicationEnvironmentId,
                        ),
                        domain_resource_id: numberOrNull(domainId),
                        tls_certificate_resource_id:
                            numberOrNull(certificateId),
                        url: url.trim(),
                        role,
                        is_primary: isPrimary,
                        redirects_to: redirectsTo.trim(),
                    }),
                },
            );
            resetForm();
            await load();
        } catch (saveError) {
            setError(
                saveError instanceof Error
                    ? saveError.message
                    : "Unable to create this website endpoint.",
            );
        } finally {
            setIsSaving(false);
        }
    }

    async function archiveEndpoint(endpoint: WebsiteEndpoint) {
        if (!window.confirm(`Archive ${endpoint.name}?`)) return;
        try {
            setArchivingId(endpoint.resource_id);
            setError(null);
            await fetchAPI(
                `${API_URL}/api/admin/infrastructure/website-endpoints/${endpoint.resource_id}/archive`,
                { method: "POST" },
            );
            await load();
        } catch (archiveError) {
            setError(
                archiveError instanceof Error
                    ? archiveError.message
                    : "Unable to archive this website endpoint.",
            );
        } finally {
            setArchivingId(null);
        }
    }

    if (!canView) return null;

    return (
        <Card className="p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                    <h2 className="text-sm font-semibold text-white">
                        Website endpoints
                    </h2>
                    <p className="mt-1 text-xs leading-5 text-slate-500">
                        Concrete URLs for this web property, linked to the
                        application environment, Domain and TLS certificate that
                        serve each endpoint.
                    </p>
                </div>
                {canAdd ? (
                    <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        onClick={() => void openForm()}
                    >
                        Add endpoint
                    </Button>
                ) : null}
            </div>

            {showForm ? (
                <div className="mt-5 space-y-4 rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                    <div className="grid gap-3 md:grid-cols-2">
                        <label className="space-y-2 text-xs text-slate-400">
                            Endpoint name
                            <Input
                                value={name}
                                onChange={(event) =>
                                    setName(event.target.value)
                                }
                                placeholder="Production website"
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            URL
                            <Input
                                type="url"
                                value={url}
                                onChange={(event) => setUrl(event.target.value)}
                                placeholder="https://www.example.com"
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Role
                            <Select
                                value={role}
                                onChange={(event) =>
                                    setRole(event.target.value)
                                }
                                disabled={isSaving}
                            >
                                {[
                                    "primary",
                                    "alias",
                                    "staging",
                                    "development",
                                    "admin",
                                    "api",
                                    "health",
                                    "other",
                                ].map((value) => (
                                    <option key={value} value={value}>
                                        {label(value)}
                                    </option>
                                ))}
                            </Select>
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Application environment
                            <Select
                                value={applicationEnvironmentId}
                                onChange={(event) =>
                                    setApplicationEnvironmentId(
                                        event.target.value,
                                    )
                                }
                                disabled={isSaving || !options}
                            >
                                <option value="">Not linked</option>
                                {applicationEnvironments.map((option) => (
                                    <option
                                        key={option.resource_id}
                                        value={option.resource_id}
                                    >
                                        {option.application_name} ·{" "}
                                        {option.name}
                                    </option>
                                ))}
                            </Select>
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Domain
                            <Select
                                value={domainId}
                                onChange={(event) =>
                                    setDomainId(event.target.value)
                                }
                                disabled={isSaving || !options}
                            >
                                <option value="">Not linked</option>
                                {domains.map((option) => (
                                    <option
                                        key={option.resource_id}
                                        value={option.resource_id}
                                    >
                                        {option.domain_name}
                                    </option>
                                ))}
                            </Select>
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            TLS certificate
                            <Select
                                value={certificateId}
                                onChange={(event) =>
                                    setCertificateId(event.target.value)
                                }
                                disabled={isSaving || !options}
                            >
                                <option value="">Not linked</option>
                                {certificates.map((option) => (
                                    <option
                                        key={option.resource_id}
                                        value={option.resource_id}
                                    >
                                        {option.name}
                                        {option.subject_common_name
                                            ? ` · ${option.subject_common_name}`
                                            : ""}
                                    </option>
                                ))}
                            </Select>
                        </label>
                        <label className="space-y-2 text-xs text-slate-400 md:col-span-2">
                            Redirect target
                            <Input
                                type="url"
                                value={redirectsTo}
                                onChange={(event) =>
                                    setRedirectsTo(event.target.value)
                                }
                                placeholder="Optional redirect destination"
                                disabled={isSaving}
                            />
                        </label>
                        <label className="flex items-center gap-2 text-xs text-slate-400 md:col-span-2">
                            <input
                                type="checkbox"
                                checked={isPrimary}
                                onChange={(event) =>
                                    setIsPrimary(event.target.checked)
                                }
                                disabled={isSaving}
                            />
                            Primary endpoint for this Website
                        </label>
                    </div>
                    <div className="flex justify-end gap-2">
                        <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={resetForm}
                            disabled={isSaving}
                        >
                            Cancel
                        </Button>
                        <Button
                            type="button"
                            size="sm"
                            onClick={() => void createEndpoint()}
                            disabled={isSaving || !name.trim() || !url.trim()}
                        >
                            {isSaving ? "Creating..." : "Create endpoint"}
                        </Button>
                    </div>
                </div>
            ) : null}

            {error ? (
                <p className="mt-4 text-sm text-red-300">{error}</p>
            ) : null}

            {endpoints.length === 0 ? (
                <p className="mt-5 text-sm text-slate-500">
                    No current endpoints are attached to this Website yet.
                </p>
            ) : (
                <div className="mt-4 divide-y divide-slate-800">
                    {endpoints.map((endpoint) => (
                        <div
                            key={endpoint.resource_id}
                            className="flex flex-col gap-3 py-3 sm:flex-row sm:items-center sm:justify-between"
                        >
                            <div className="min-w-0 flex-1">
                                <Link
                                    href={`/admin/infrastructure/resources/${endpoint.resource_id}`}
                                    className="hover:text-adb-cyan-300 text-sm font-medium text-slate-200"
                                >
                                    {endpoint.name}
                                </Link>
                                <a
                                    href={endpoint.url}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="text-adb-cyan-300 mt-1 block text-xs break-all hover:underline"
                                >
                                    {endpoint.url}
                                </a>
                                <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-500">
                                    <span>{label(endpoint.role)}</span>
                                    {endpoint.is_primary ? (
                                        <span>Primary</span>
                                    ) : null}
                                    {endpoint.application_environment_name ? (
                                        <span>
                                            {
                                                endpoint.application_environment_name
                                            }
                                        </span>
                                    ) : null}
                                    {endpoint.domain_name ? (
                                        <span>{endpoint.domain_name}</span>
                                    ) : null}
                                    {endpoint.tls_certificate_name ? (
                                        <span>
                                            {endpoint.tls_certificate_name}
                                        </span>
                                    ) : null}
                                </div>
                                {endpoint.redirects_to ? (
                                    <div className="mt-1 text-xs text-slate-600">
                                        Redirects to {endpoint.redirects_to}
                                    </div>
                                ) : null}
                            </div>
                            {canArchive ? (
                                <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() =>
                                        void archiveEndpoint(endpoint)
                                    }
                                    disabled={
                                        archivingId === endpoint.resource_id
                                    }
                                >
                                    {archivingId === endpoint.resource_id
                                        ? "Archiving..."
                                        : "Archive"}
                                </Button>
                            ) : null}
                        </div>
                    ))}
                </div>
            )}
        </Card>
    );
}

export function DNSRecordsCard({ resourceId }: { resourceId: number }) {
    const { hasPermission } = useAuth();
    const canView =
        hasPermission("infrastructure.view_dnszone") &&
        hasPermission("infrastructure.view_dnsrecord");
    const canAdd = hasPermission("infrastructure.add_dnsrecord");
    const canChange = hasPermission("infrastructure.change_dnsrecord");
    const canDelete = hasPermission("infrastructure.delete_dnsrecord");

    const [records, setRecords] = useState<DNSRecord[]>([]);
    const [showForm, setShowForm] = useState(false);
    const [editingId, setEditingId] = useState<number | null>(null);
    const [name, setName] = useState("@");
    const [recordType, setRecordType] = useState("A");
    const [value, setValue] = useState("");
    const [ttl, setTtl] = useState("300");
    const [priority, setPriority] = useState("");
    const [weight, setWeight] = useState("");
    const [port, setPort] = useState("");
    const [proxied, setProxied] = useState("");
    const [providerRecordId, setProviderRecordId] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [deletingId, setDeletingId] = useState<number | null>(null);

    const load = useCallback(async () => {
        if (!canView) return;
        try {
            setError(null);
            setRecords(
                (await fetchAPI(
                    `${API_URL}/api/admin/infrastructure/dns-zones/${resourceId}/records`,
                )) as DNSRecord[],
            );
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "Unable to load DNS records.",
            );
        }
    }, [canView, resourceId]);

    useEffect(() => {
        void load();
    }, [load]);

    function resetForm() {
        setShowForm(false);
        setEditingId(null);
        setName("@");
        setRecordType("A");
        setValue("");
        setTtl("300");
        setPriority("");
        setWeight("");
        setPort("");
        setProxied("");
        setProviderRecordId("");
    }

    function editRecord(record: DNSRecord) {
        setShowForm(true);
        setEditingId(record.id);
        setName(record.name);
        setRecordType(record.record_type);
        setValue(record.value);
        setTtl(String(record.ttl));
        setPriority(record.priority === null ? "" : String(record.priority));
        setWeight(record.weight === null ? "" : String(record.weight));
        setPort(record.port === null ? "" : String(record.port));
        setProxied(record.proxied === null ? "" : String(record.proxied));
        setProviderRecordId(record.provider_record_id);
        setError(null);
    }

    async function saveRecord() {
        if (!name.trim() || !value.trim()) {
            setError("Enter a DNS record name and value.");
            return;
        }
        const parsedTtl = Number(ttl);
        if (!Number.isInteger(parsedTtl) || parsedTtl < 1) {
            setError("TTL must be a positive whole number.");
            return;
        }
        try {
            setIsSaving(true);
            setError(null);
            await fetchAPI(
                editingId === null
                    ? `${API_URL}/api/admin/infrastructure/dns-zones/${resourceId}/records`
                    : `${API_URL}/api/admin/infrastructure/dns-zones/${resourceId}/records/${editingId}`,
                {
                    method: editingId === null ? "POST" : "PUT",
                    body: JSON.stringify({
                        name: name.trim(),
                        record_type: recordType,
                        value: value.trim(),
                        ttl: parsedTtl,
                        priority: numberOrNull(priority),
                        weight: numberOrNull(weight),
                        port: numberOrNull(port),
                        proxied: triStatePayload(proxied),
                        provider_record_id: providerRecordId.trim(),
                    }),
                },
            );
            resetForm();
            await load();
        } catch (saveError) {
            setError(
                saveError instanceof Error
                    ? saveError.message
                    : "Unable to save this DNS record.",
            );
        } finally {
            setIsSaving(false);
        }
    }

    async function deleteRecord(record: DNSRecord) {
        if (!window.confirm(`Delete ${record.name} ${record.record_type}?`))
            return;
        try {
            setDeletingId(record.id);
            setError(null);
            await fetchAPI(
                `${API_URL}/api/admin/infrastructure/dns-zones/${resourceId}/records/${record.id}`,
                { method: "DELETE" },
            );
            await load();
        } catch (deleteError) {
            setError(
                deleteError instanceof Error
                    ? deleteError.message
                    : "Unable to delete this DNS record.",
            );
        } finally {
            setDeletingId(null);
        }
    }

    if (!canView) return null;

    return (
        <Card className="p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                    <h2 className="text-sm font-semibold text-white">
                        DNS records
                    </h2>
                    <p className="mt-1 text-xs leading-5 text-slate-500">
                        Structured authoritative records for this DNS Zone.
                        Provider record IDs are operational metadata only;
                        credentials remain in the Vault.
                    </p>
                </div>
                {canAdd ? (
                    <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        onClick={() => {
                            resetForm();
                            setShowForm(true);
                        }}
                    >
                        Add record
                    </Button>
                ) : null}
            </div>

            {showForm ? (
                <div className="mt-5 space-y-4 rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                    <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
                        <label className="space-y-2 text-xs text-slate-400">
                            Name
                            <Input
                                value={name}
                                onChange={(event) =>
                                    setName(event.target.value)
                                }
                                placeholder="@ or www"
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Type
                            <Select
                                value={recordType}
                                onChange={(event) =>
                                    setRecordType(event.target.value)
                                }
                                disabled={isSaving}
                            >
                                {[
                                    "A",
                                    "AAAA",
                                    "CNAME",
                                    "MX",
                                    "TXT",
                                    "NS",
                                    "SRV",
                                    "CAA",
                                    "PTR",
                                    "ALIAS",
                                    "OTHER",
                                ].map((type) => (
                                    <option key={type} value={type}>
                                        {type}
                                    </option>
                                ))}
                            </Select>
                        </label>
                        <label className="space-y-2 text-xs text-slate-400 md:col-span-2">
                            Value
                            <Input
                                value={value}
                                onChange={(event) =>
                                    setValue(event.target.value)
                                }
                                placeholder="203.0.113.10, target host, or record value"
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            TTL
                            <Input
                                type="number"
                                min="1"
                                value={ttl}
                                onChange={(event) => setTtl(event.target.value)}
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Priority
                            <Input
                                type="number"
                                min="0"
                                value={priority}
                                onChange={(event) =>
                                    setPriority(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Weight
                            <Input
                                type="number"
                                min="0"
                                value={weight}
                                onChange={(event) =>
                                    setWeight(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Port
                            <Input
                                type="number"
                                min="1"
                                max="65535"
                                value={port}
                                onChange={(event) =>
                                    setPort(event.target.value)
                                }
                                disabled={isSaving}
                            />
                        </label>
                        <label className="space-y-2 text-xs text-slate-400">
                            Proxy state
                            <Select
                                value={proxied}
                                onChange={(event) =>
                                    setProxied(event.target.value)
                                }
                                disabled={isSaving}
                            >
                                <option value="">Not specified</option>
                                <option value="true">Proxied</option>
                                <option value="false">DNS only</option>
                            </Select>
                        </label>
                        <label className="space-y-2 text-xs text-slate-400 md:col-span-2 lg:col-span-3">
                            Provider record ID
                            <Input
                                value={providerRecordId}
                                onChange={(event) =>
                                    setProviderRecordId(event.target.value)
                                }
                                placeholder="Optional provider-side identifier"
                                disabled={isSaving}
                            />
                        </label>
                    </div>
                    <div className="flex justify-end gap-2">
                        <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={resetForm}
                            disabled={isSaving}
                        >
                            Cancel
                        </Button>
                        <Button
                            type="button"
                            size="sm"
                            onClick={() => void saveRecord()}
                            disabled={isSaving || !name.trim() || !value.trim()}
                        >
                            {isSaving
                                ? "Saving..."
                                : editingId === null
                                  ? "Create record"
                                  : "Save record"}
                        </Button>
                    </div>
                </div>
            ) : null}

            {error ? (
                <p className="mt-4 text-sm text-red-300">{error}</p>
            ) : null}

            {records.length === 0 ? (
                <p className="mt-5 text-sm text-slate-500">
                    No DNS records have been recorded yet.
                </p>
            ) : (
                <div className="mt-4 overflow-x-auto">
                    <table className="min-w-full divide-y divide-slate-800 text-sm">
                        <thead className="text-left text-[11px] font-semibold tracking-wide text-slate-600 uppercase">
                            <tr>
                                <th className="py-2 pr-4">Name</th>
                                <th className="py-2 pr-4">Type</th>
                                <th className="py-2 pr-4">Value</th>
                                <th className="py-2 pr-4">TTL</th>
                                <th className="py-2">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/80">
                            {records.map((record) => (
                                <tr key={record.id}>
                                    <td className="py-3 pr-4 font-mono text-xs text-slate-300">
                                        {record.name}
                                    </td>
                                    <td className="py-3 pr-4 text-slate-400">
                                        {record.record_type}
                                    </td>
                                    <td className="max-w-xl py-3 pr-4">
                                        <code className="text-xs break-all text-slate-300">
                                            {record.value}
                                        </code>
                                        {record.priority !== null ? (
                                            <div className="mt-1 text-[11px] text-slate-600">
                                                Priority {record.priority}
                                                {record.weight !== null
                                                    ? ` · Weight ${record.weight}`
                                                    : ""}
                                                {record.port !== null
                                                    ? ` · Port ${record.port}`
                                                    : ""}
                                            </div>
                                        ) : null}
                                    </td>
                                    <td className="py-3 pr-4 text-slate-500">
                                        {record.ttl}s
                                    </td>
                                    <td className="py-3">
                                        <div className="flex gap-1">
                                            {canChange ? (
                                                <Button
                                                    type="button"
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() =>
                                                        editRecord(record)
                                                    }
                                                >
                                                    Edit
                                                </Button>
                                            ) : null}
                                            {canDelete ? (
                                                <Button
                                                    type="button"
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() =>
                                                        void deleteRecord(
                                                            record,
                                                        )
                                                    }
                                                    disabled={
                                                        deletingId === record.id
                                                    }
                                                >
                                                    {deletingId === record.id
                                                        ? "Deleting..."
                                                        : "Delete"}
                                                </Button>
                                            ) : null}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </Card>
    );
}

export function TLSCertificateDomainsCard({
    resourceId,
    ownershipType,
    clientId,
}: OwnedNestedCardProps) {
    const { hasPermission } = useAuth();
    const canView =
        hasPermission("infrastructure.view_tlscertificate") &&
        hasPermission("infrastructure.view_domainprofile") &&
        hasPermission("infrastructure.view_tlscertificatedomain");
    const canAdd = hasPermission("infrastructure.add_tlscertificatedomain");
    const canDelete = hasPermission(
        "infrastructure.delete_tlscertificatedomain",
    );

    const [links, setLinks] = useState<TLSCertificateDomain[]>([]);
    const [options, setOptions] = useState<WebDomainOptions | null>(null);
    const [editingId, setEditingId] = useState<number | null>(null);
    const [showForm, setShowForm] = useState(false);
    const [domainId, setDomainId] = useState("");
    const [isPrimary, setIsPrimary] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [deletingId, setDeletingId] = useState<number | null>(null);

    const load = useCallback(async () => {
        if (!canView) return;
        try {
            setError(null);
            setLinks(
                (await fetchAPI(
                    `${API_URL}/api/admin/infrastructure/tls-certificates/${resourceId}/domains`,
                )) as TLSCertificateDomain[],
            );
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "Unable to load TLS certificate domain coverage.",
            );
        }
    }, [canView, resourceId]);

    useEffect(() => {
        void load();
    }, [load]);

    useEffect(() => {
        setShowForm(false);
        setOptions(null);
        setDomainId("");
        setIsPrimary(false);
        setError(null);
    }, [resourceId]);

    const domains = useMemo(
        () =>
            options?.domains.filter(
                (option) =>
                    optionAllowed(option, ownershipType, clientId) &&
                    !links.some(
                        (link) =>
                            link.id !== editingId &&
                            link.domain_resource_id === option.resource_id,
                    ),
            ) ?? [],
        [clientId, editingId, links, options, ownershipType],
    );

    async function openForm(link?: TLSCertificateDomain) {
        setEditingId(link?.id ?? null);
        setDomainId(link ? String(link.domain_resource_id) : "");
        setIsPrimary(link?.is_primary ?? false);
        setShowForm(true);
        setError(null);
        if (options) return;
        try {
            setOptions(
                (await fetchAPI(
                    `${API_URL}/api/admin/infrastructure/web-domain-options`,
                )) as WebDomainOptions,
            );
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "Unable to load Domain options.",
            );
        }
    }

    async function addDomain() {
        if (!domainId) {
            setError("Choose a Domain.");
            return;
        }
        try {
            setIsSaving(true);
            setError(null);
            await fetchAPI(
                `${API_URL}/api/admin/infrastructure/tls-certificates/${resourceId}/domains${editingId === null ? "" : `/${editingId}`}`,
                {
                    method: editingId === null ? "POST" : "PUT",
                    body: JSON.stringify({
                        domain_resource_id: Number(domainId),
                        is_primary: isPrimary,
                    }),
                },
            );
            setShowForm(false);
            setDomainId("");
            setIsPrimary(false);
            await load();
        } catch (saveError) {
            setError(
                saveError instanceof Error
                    ? saveError.message
                    : "Unable to add this Domain to the certificate.",
            );
        } finally {
            setIsSaving(false);
        }
    }

    async function removeDomain(link: TLSCertificateDomain) {
        if (
            !window.confirm(`Remove ${link.domain_name} from this certificate?`)
        )
            return;
        try {
            setDeletingId(link.id);
            setError(null);
            await fetchAPI(
                `${API_URL}/api/admin/infrastructure/tls-certificates/${resourceId}/domains/${link.id}`,
                { method: "DELETE" },
            );
            await load();
        } catch (deleteError) {
            setError(
                deleteError instanceof Error
                    ? deleteError.message
                    : "Unable to remove this certificate Domain.",
            );
        } finally {
            setDeletingId(null);
        }
    }

    if (!canView) return null;

    return (
        <Card className="p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                    <h2 className="text-sm font-semibold text-white">
                        Domain coverage
                    </h2>
                    <p className="mt-1 text-xs leading-5 text-slate-500">
                        Domains covered by this TLS certificate. This tracks
                        certificate metadata only; private keys and certificate
                        bundles belong in the Credential Vault.
                    </p>
                </div>
                {canAdd ? (
                    <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        onClick={() => void openForm()}
                    >
                        Add Domain
                    </Button>
                ) : null}
            </div>

            {showForm ? (
                <div className="mt-5 space-y-4 rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                    <label className="block space-y-2 text-xs text-slate-400">
                        Domain
                        <Select
                            value={domainId}
                            onChange={(event) =>
                                setDomainId(event.target.value)
                            }
                            disabled={isSaving || !options}
                        >
                            <option value="">Choose Domain</option>
                            {domains.map((domain) => (
                                <option
                                    key={domain.resource_id}
                                    value={domain.resource_id}
                                >
                                    {domain.domain_name}
                                </option>
                            ))}
                        </Select>
                    </label>
                    <label className="flex items-center gap-2 text-xs text-slate-400">
                        <input
                            type="checkbox"
                            checked={isPrimary}
                            onChange={(event) =>
                                setIsPrimary(event.target.checked)
                            }
                            disabled={isSaving}
                        />
                        Primary certificate name
                    </label>
                    <div className="flex justify-end gap-2">
                        <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => setShowForm(false)}
                            disabled={isSaving}
                        >
                            Cancel
                        </Button>
                        <Button
                            type="button"
                            size="sm"
                            onClick={() => void addDomain()}
                            disabled={isSaving || !domainId}
                        >
                            {isSaving
                                ? "Saving..."
                                : editingId === null
                                  ? "Add Domain"
                                  : "Save domain coverage"}
                        </Button>
                    </div>
                </div>
            ) : null}

            {error ? (
                <p className="mt-4 text-sm text-red-300">{error}</p>
            ) : null}

            {links.length === 0 ? (
                <p className="mt-5 text-sm text-slate-500">
                    No Domain coverage has been attached to this certificate
                    yet.
                </p>
            ) : (
                <div className="mt-4 divide-y divide-slate-800">
                    {links.map((link) => (
                        <div
                            key={link.id}
                            className="flex items-center justify-between gap-3 py-3"
                        >
                            <Link
                                href={`/admin/infrastructure/resources/${link.domain_resource_id}`}
                                className="hover:text-adb-cyan-300 min-w-0 flex-1 text-sm font-medium text-slate-200"
                            >
                                {link.domain_name}
                                {link.is_primary ? (
                                    <span className="ml-2 text-xs font-normal text-slate-500">
                                        Primary
                                    </span>
                                ) : null}
                            </Link>
                            {hasPermission(
                                "infrastructure.change_tlscertificatedomain",
                            ) ? (
                                <Button
                                    type="button"
                                    variant="secondary"
                                    size="sm"
                                    onClick={() => void openForm(link)}
                                >
                                    Edit
                                </Button>
                            ) : null}
                            {canDelete ? (
                                <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => void removeDomain(link)}
                                    disabled={deletingId === link.id}
                                >
                                    {deletingId === link.id
                                        ? "Removing..."
                                        : "Remove"}
                                </Button>
                            ) : null}
                        </div>
                    ))}
                </div>
            )}
        </Card>
    );
}

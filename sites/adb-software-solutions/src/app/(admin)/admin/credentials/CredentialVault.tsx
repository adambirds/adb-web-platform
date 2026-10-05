"use client";

import { useLiveRefresh } from "@/contexts/LiveEventsContext";

import { RecordDrawer } from "@/components/admin/RecordDrawer";
import {
    Badge,
    Button,
    Card,
    DataError,
    DataLoading,
    EmptyState,
    Input,
    PageHeader,
    Pagination,
    Select,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeaderCell,
    TableRow,
} from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAPI } from "@/lib/api/fetch";
import {
    CredentialDetail,
    CredentialOptions,
    CredentialPage,
    CredentialSummary,
    CredentialVaultAPI,
} from "@/lib/api/credentialVault";
import { useCallback, useEffect, useMemo, useState } from "react";
import { CredentialForm } from "./CredentialForm";
import { CredentialWorkspace } from "./CredentialWorkspace";

const PAGE_SIZE = 25;

function dateTime(value: string | null): string {
    if (!value) return "—";
    return new Intl.DateTimeFormat("en-GB", {
        dateStyle: "medium",
        timeStyle: "short",
    }).format(new Date(value));
}

function expiryClass(value: string | null): string {
    if (!value) return "text-slate-500";
    const remaining = new Date(value).getTime() - Date.now();
    if (remaining < 0) return "text-red-300";
    if (remaining < 30 * 24 * 60 * 60 * 1000) return "text-amber-300";
    return "text-slate-400";
}

export function CredentialVault({
    initialClientId,
    initialResourceId,
    compact = false,
}: {
    initialClientId?: number;
    initialResourceId?: number;
    compact?: boolean;
}) {
    const { hasPermission } = useAuth();
    const canCreate = hasPermission("credentials.add_storedcredential");

    const [options, setOptions] = useState<CredentialOptions | null>(null);
    const [pageData, setPageData] = useState<CredentialPage | null>(null);
    const [page, setPage] = useState(1);
    const [status, setStatus] = useState("active");
    const [ownership, setOwnership] = useState("all");
    const [clientId, setClientId] = useState(initialClientId ? String(initialClientId) : "");
    const [credentialTypeId, setCredentialTypeId] = useState("");
    const [search, setSearch] = useState("");
    const [debouncedSearch, setDebouncedSearch] = useState("");
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedCredential, setSelectedCredential] = useState<CredentialSummary | null>(null);
    const [showCreate, setShowCreate] = useState(false);

    useEffect(() => {
        const handle = window.setTimeout(() => setDebouncedSearch(search.trim()), 250);
        return () => window.clearTimeout(handle);
    }, [search]);

    const query = useMemo(() => {
        const params = new URLSearchParams({
            page: String(page),
            page_size: String(compact ? 10 : PAGE_SIZE),
            status,
            ownership,
        });
        if (clientId) params.set("client_id", clientId);
        if (credentialTypeId) params.set("credential_type_id", credentialTypeId);
        if (initialResourceId) params.set("resource_id", String(initialResourceId));
        if (debouncedSearch) params.set("search", debouncedSearch);
        return params.toString();
    }, [clientId, compact, credentialTypeId, debouncedSearch, initialResourceId, ownership, page, status]);

    const loadOptions = useCallback(async () => {
        try {
            setOptions((await fetchAPI(CredentialVaultAPI.options())) as CredentialOptions);
        } catch {
            // The list request will surface the authoritative permission/error state.
        }
    }, []);

    const load = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            setPageData((await fetchAPI(CredentialVaultAPI.list(query))) as CredentialPage);
        } catch (loadError) {
            setError(loadError instanceof Error ? loadError.message : "Unable to load the credential vault.");
        } finally {
            setIsLoading(false);
        }
    }, [query]);

    useEffect(() => {
        void loadOptions();
    }, [loadOptions]);

    useEffect(() => {
        void load();
    }, [load]);
    useLiveRefresh(["credentials"], load);

    useEffect(() => {
        setPage(1);
    }, [status, ownership, clientId, credentialTypeId, debouncedSearch, initialResourceId]);

    const title = initialClientId
        ? "Credentials"
        : initialResourceId
          ? "Credentials"
          : "Credential Vault";

    const description = initialClientId
        ? "Active credentials owned by this client. Archived and inactive records stay out of the way unless selected."
        : initialResourceId
          ? "Credentials linked to this infrastructure resource."
          : "Encrypted operational credentials, SSH keys, API tokens, service accounts, certificates and recovery material.";

    return (
        <div className="space-y-6">
            <PageHeader
                eyebrow={compact ? undefined : "Operations"}
                title={title}
                description={description}
                actions={
                    canCreate ? (
                        <Button type="button" onClick={() => setShowCreate(true)}>
                            Add credential
                        </Button>
                    ) : undefined
                }
            />

            {!compact ? (
                <Card className="p-4">
                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
                        <Input
                            value={search}
                            onChange={(event) => setSearch(event.target.value)}
                            placeholder="Search credentials, users, clients or resources..."
                        />
                        <Select value={status} onChange={(event) => setStatus(event.target.value)}>
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                            <option value="archived">Archived</option>
                            <option value="all">All statuses</option>
                        </Select>
                        <Select value={ownership} onChange={(event) => setOwnership(event.target.value)}>
                            <option value="all">All ownership</option>
                            <option value="internal">ADB Internal</option>
                            <option value="client">Client-owned</option>
                        </Select>
                        <Select value={clientId} onChange={(event) => setClientId(event.target.value)}>
                            <option value="">All clients</option>
                            {options?.clients.map((client) => (
                                <option key={client.id} value={client.id}>{client.name}</option>
                            ))}
                        </Select>
                        <Select value={credentialTypeId} onChange={(event) => setCredentialTypeId(event.target.value)}>
                            <option value="">All credential types</option>
                            {options?.types.map((type) => (
                                <option key={type.id} value={type.id}>{type.name}</option>
                            ))}
                        </Select>
                    </div>
                    {status !== "active" ? (
                        <p className="mt-3 text-xs text-amber-300/80">
                            You are explicitly viewing non-current credential history. Active credentials are the default operational view.
                        </p>
                    ) : null}
                </Card>
            ) : null}

            {error ? (
                <DataError message={error} onRetry={() => void load()} />
            ) : isLoading && !pageData ? (
                <DataLoading label="Loading credential vault..." />
            ) : !pageData || pageData.items.length === 0 ? (
                <EmptyState
                    title="No credentials in this view"
                    description="Change the filters or add the first credential for this scope."
                />
            ) : (
                <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40">
                    <Table className="min-w-[920px]">
                        <TableHead>
                            <tr>
                                <TableHeaderCell>Credential</TableHeaderCell>
                                <TableHeaderCell>Scope</TableHeaderCell>
                                <TableHeaderCell>Type</TableHeaderCell>
                                <TableHeaderCell>Username</TableHeaderCell>
                                <TableHeaderCell>Resources</TableHeaderCell>
                                <TableHeaderCell>Expires</TableHeaderCell>
                                <TableHeaderCell>Updated</TableHeaderCell>
                            </tr>
                        </TableHead>
                        <TableBody>
                            {pageData.items.map((credential) => (
                                <TableRow
                                    key={credential.id}
                                    className="cursor-pointer"
                                    onClick={() => setSelectedCredential(credential)}
                                >
                                    <TableCell>
                                        <div className="flex items-center gap-2">
                                            <span className="font-medium text-slate-100">{credential.name}</span>
                                            {credential.has_legacy_plaintext ? (
                                                <Badge className="border-amber-900 bg-amber-950/50 text-amber-300">Legacy</Badge>
                                            ) : null}
                                        </div>
                                        {credential.url ? (
                                            <div className="mt-1 max-w-64 truncate text-xs text-slate-600">{credential.url}</div>
                                        ) : null}
                                    </TableCell>
                                    <TableCell>
                                        <span className="text-slate-300">{credential.client_name || "ADB Internal"}</span>
                                    </TableCell>
                                    <TableCell className="text-slate-400">{credential.credential_type_name || "Unclassified"}</TableCell>
                                    <TableCell className="font-mono text-xs text-slate-400">{credential.username || "—"}</TableCell>
                                    <TableCell className="text-slate-400">{credential.resource_count}</TableCell>
                                    <TableCell className={expiryClass(credential.expires_at)}>{dateTime(credential.expires_at)}</TableCell>
                                    <TableCell className="text-slate-500">{dateTime(credential.updated_at)}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                    <Pagination
                        page={pageData.page}
                        pageSize={pageData.page_size}
                        totalItems={pageData.total}
                        onPageChange={setPage}
                        disabled={isLoading}
                    />
                </div>
            )}

            {selectedCredential ? (
                <RecordDrawer
                    onClose={() => setSelectedCredential(null)}
                    fullPageHref={`/admin/credentials/${selectedCredential.id}`}
                >
                    <CredentialWorkspace
                        credentialId={selectedCredential.id}
                        presentation="drawer"
                        onChanged={() => void load()}
                    />
                </RecordDrawer>
            ) : null}

            {showCreate ? (
                <RecordDrawer onClose={() => setShowCreate(false)}>
                    <div className="space-y-5">
                        <PageHeader
                            eyebrow="Credential Vault"
                            title="Add credential"
                            description="Choose a typed template. Secret fields are encrypted and never returned by the normal credential API."
                        />
                        <CredentialForm
                            initialClientId={initialClientId}
                            initialResourceId={initialResourceId}
                            onCancel={() => setShowCreate(false)}
                            onSaved={(saved: CredentialDetail) => {
                                setShowCreate(false);
                                setSelectedCredential(saved);
                                void load();
                            }}
                        />
                    </div>
                </RecordDrawer>
            ) : null}
        </div>
    );
}

"use client";

import { RecordDrawer } from "@/components/admin/RecordDrawer";
import {
    Button,
    ButtonLink,
    Card,
    DataError,
    DataLoading,
    EmptyState,
    Input,
    PageHeader,
    Pagination,
} from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";
import { useCallback, useEffect, useState } from "react";
import {
    ServiceProviderForm,
    type ServiceProviderOption,
} from "../resources/ServiceProviderForm";

interface ProviderPage {
    items: ServiceProviderOption[];
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
}

export function ServiceProvidersWorkspace() {
    const { hasPermission } = useAuth();
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState("");
    const [data, setData] = useState<ProviderPage | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [editing, setEditing] = useState<ServiceProviderOption | null>(null);
    const [creating, setCreating] = useState(false);
    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            setData(
                (await fetchAPI(
                    `${API_URL}/api/admin/infrastructure/service-providers?${new URLSearchParams({ page: String(page), page_size: "25", search })}`,
                )) as ProviderPage,
            );
        } catch (failure) {
            setError(
                failure instanceof Error
                    ? failure.message
                    : "Unable to load service providers.",
            );
        } finally {
            setLoading(false);
        }
    }, [page, search]);
    useEffect(() => {
        void load();
    }, [load]);
    return (
        <div className="space-y-5">
            <PageHeader
                title="Service Providers"
                description="The shared vendor catalogue for cloud, hosting, domain and other infrastructure accounts."
                actions={
                    <>
                        <ButtonLink
                            href="/admin/infrastructure/provider-accounts"
                            variant="secondary"
                        >
                            Provider accounts
                        </ButtonLink>
                        {hasPermission("infrastructure.add_serviceprovider") ? (
                            <Button onClick={() => setCreating(true)}>
                                Add service provider
                            </Button>
                        ) : null}
                    </>
                }
            />
            <Input
                aria-label="Search service providers"
                placeholder="Search vendor or category..."
                value={search}
                onChange={(event) => {
                    setSearch(event.target.value);
                    setPage(1);
                }}
            />
            {error ? (
                <DataError message={error} onRetry={() => void load()} />
            ) : null}
            {loading && !data ? (
                <DataLoading label="Loading service providers..." />
            ) : null}
            {data?.items.length ? (
                <Card className="overflow-x-auto">
                    <table className="min-w-full text-left text-sm">
                        <thead>
                            <tr>
                                {[
                                    "Provider",
                                    "Category",
                                    "Website",
                                    "Status",
                                    "Actions",
                                ].map((name) => (
                                    <th
                                        key={name}
                                        className="px-4 py-3 text-slate-400"
                                    >
                                        {name}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {data.items.map((provider) => (
                                <tr
                                    key={provider.id}
                                    className="border-t border-slate-800"
                                >
                                    <td className="px-4 py-3 text-slate-100">
                                        {provider.name}
                                    </td>
                                    <td className="px-4 py-3">
                                        {provider.category.replaceAll("_", " ")}
                                    </td>
                                    <td className="px-4 py-3">
                                        {provider.website_url ? (
                                            <a
                                                href={provider.website_url}
                                                target="_blank"
                                                rel="noreferrer"
                                            >
                                                {provider.website_url}
                                            </a>
                                        ) : (
                                            "Unknown"
                                        )}
                                    </td>
                                    <td className="px-4 py-3">
                                        {provider.is_active
                                            ? "Active"
                                            : "Inactive"}
                                    </td>
                                    <td className="px-4 py-3">
                                        {hasPermission(
                                            "infrastructure.change_serviceprovider",
                                        ) ? (
                                            <Button
                                                variant="secondary"
                                                size="sm"
                                                onClick={() =>
                                                    setEditing(provider)
                                                }
                                                aria-label={`Edit ${provider.name}`}
                                            >
                                                Edit
                                            </Button>
                                        ) : null}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    <Pagination
                        page={data.page}
                        pageSize={data.page_size}
                        totalItems={data.total}
                        onPageChange={setPage}
                        disabled={loading}
                    />
                </Card>
            ) : !loading && data ? (
                <EmptyState
                    title="No service providers recorded"
                    description="Add a vendor here or while creating a Provider Account."
                />
            ) : null}
            {creating || editing ? (
                <RecordDrawer
                    onClose={() => {
                        setCreating(false);
                        setEditing(null);
                    }}
                >
                    <ServiceProviderForm
                        key={editing?.id ?? "new"}
                        provider={editing ?? undefined}
                        onCancel={() => {
                            setCreating(false);
                            setEditing(null);
                        }}
                        onCreated={() => {
                            setCreating(false);
                            setEditing(null);
                            void load();
                        }}
                    />
                </RecordDrawer>
            ) : null}
        </div>
    );
}

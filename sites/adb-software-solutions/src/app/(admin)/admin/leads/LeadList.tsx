"use client";

import { RecordDrawer } from "@/components/admin/RecordDrawer";
import {
    Badge,
    Card,
    DataError,
    DataLoading,
    EmptyState,
    Input,
    Pagination,
    Select,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeaderCell,
    TableRow,
} from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import { OverviewAPI } from "@/lib/api/overview";
import { useCallback, useEffect, useMemo, useState } from "react";
import { LeadWorkspace } from "./[id]/LeadWorkspace";
import { LeadEmailPanel } from "./LeadEmailPanel";

interface Lookup {
    id: number;
    name: string;
}

interface Assignee {
    id: string;
    name: string;
    email: string;
}

interface LeadOptions {
    statuses: Lookup[];
    sources: Lookup[];
    assignees: Assignee[];
}

interface Brand {
    id: number;
    name: string;
    is_active: boolean;
}

type LeadView = "my" | "unassigned" | "active" | "won" | "lost" | "all";

interface LeadOverviewItem {
    id: number;
    name: string;
    company: string;
    email: string;
    status: string;
    outcome: string;
    source: string;
    brand: string;
    assigned_to_name: string | null;
    converted_at: string | null;
    created_at: string;
}

interface LeadStats {
    active: number;
    mine: number;
    unassigned: number;
    new_last_30_days: number;
}

interface LeadOverviewResponse {
    items: LeadOverviewItem[];
    stats: LeadStats;
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
}

const workViews: Array<{
    value: LeadView;
    label: string;
    description: string;
}> = [
    {
        value: "my",
        label: "My leads",
        description: "Active opportunities assigned to you",
    },
    {
        value: "unassigned",
        label: "Unassigned",
        description: "Active leads needing an owner",
    },
    {
        value: "active",
        label: "All active",
        description: "Every open opportunity in your scope",
    },
];

const historyViews: Array<{
    value: LeadView;
    label: string;
    description: string;
}> = [
    { value: "won", label: "Won", description: "Successful opportunities" },
    { value: "lost", label: "Lost", description: "Closed-lost opportunities" },
    { value: "all", label: "All leads", description: "Full CRM history" },
];

function statusClasses(lead: LeadOverviewItem) {
    if (lead.outcome === "won") {
        return "border-emerald-900/70 bg-emerald-950/50 text-emerald-300";
    }
    if (lead.outcome === "lost") {
        return "border-red-950 bg-red-950/30 text-red-300";
    }
    const normalised = lead.status.toLowerCase();
    if (normalised === "proposal" || normalised === "qualified") {
        return "border-cyan-900/70 bg-cyan-950/40 text-cyan-300";
    }
    return "border-amber-900/70 bg-amber-950/40 text-amber-300";
}

function formatDate(value: string) {
    return new Intl.DateTimeFormat("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    }).format(new Date(value));
}

function SidebarLink({
    active,
    label,
    description,
    count,
    onClick,
    quiet = false,
}: {
    active: boolean;
    label: string;
    description: string;
    count?: number;
    onClick: () => void;
    quiet?: boolean;
}) {
    return (
        <button
            type="button"
            onClick={onClick}
            className={`w-full rounded-lg border px-3 py-2.5 text-left transition ${
                active
                    ? "border-adb-cyan-500/50 bg-adb-cyan-500/10"
                    : quiet
                      ? "border-transparent text-slate-500 hover:border-slate-800 hover:bg-slate-900/50 hover:text-slate-300"
                      : "border-transparent text-slate-400 hover:border-slate-800 hover:bg-slate-900/60 hover:text-slate-200"
            }`}
        >
            <div className="flex items-center justify-between gap-3">
                <span
                    className={
                        active
                            ? "text-sm font-semibold text-white"
                            : "text-sm font-medium"
                    }
                >
                    {label}
                </span>
                {count !== undefined ? (
                    <span className="rounded-full bg-slate-950 px-2 py-0.5 text-xs text-slate-500 tabular-nums">
                        {count}
                    </span>
                ) : null}
            </div>
            <div className="mt-1 text-xs text-slate-600">{description}</div>
        </button>
    );
}

function StatCard({
    label,
    value,
    detail,
}: {
    label: string;
    value: number;
    detail: string;
}) {
    return (
        <Card className="p-4">
            <div className="text-xs font-semibold tracking-[0.14em] text-slate-500 uppercase">
                {label}
            </div>
            <div className="mt-2 text-2xl font-semibold text-white tabular-nums">
                {value}
            </div>
            <div className="mt-1 text-xs text-slate-500">{detail}</div>
        </Card>
    );
}

export function LeadList() {
    const [data, setData] = useState<LeadOverviewResponse | null>(null);
    const [options, setOptions] = useState<LeadOptions>({
        statuses: [],
        sources: [],
        assignees: [],
    });
    const [brands, setBrands] = useState<Brand[]>([]);
    const [view, setView] = useState<LeadView>("my");
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState("");
    const [statusId, setStatusId] = useState("");
    const [sourceId, setSourceId] = useState("");
    const [brandId, setBrandId] = useState("");
    const [assignedToId, setAssignedToId] = useState("");
    const [selectedLeadId, setSelectedLeadId] = useState<number | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const query = useMemo(() => {
        const params = new URLSearchParams({
            view,
            page: String(page),
            page_size: "25",
        });
        if (search.trim()) params.set("search", search.trim());
        if (statusId) params.set("status_id", statusId);
        if (sourceId) params.set("source_id", sourceId);
        if (brandId) params.set("brand_id", brandId);
        if (assignedToId) params.set("assigned_to_id", assignedToId);
        return params.toString();
    }, [assignedToId, brandId, page, search, sourceId, statusId, view]);

    const loadLeads = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            const [overview, leadOptions, brandRows] = await Promise.all([
                fetchAPI(
                    OverviewAPI.leads(query),
                ) as Promise<LeadOverviewResponse>,
                fetchAPI(AdminAPI.leads.options()) as Promise<LeadOptions>,
                fetchAPI(AdminAPI.brands.list()) as Promise<Brand[]>,
            ]);
            setData(overview);
            setOptions(leadOptions);
            setBrands(brandRows.filter((brand) => brand.is_active));
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "An unexpected error occurred while loading leads.",
            );
        } finally {
            setIsLoading(false);
        }
    }, [query]);

    useEffect(() => {
        const timeout = window.setTimeout(() => void loadLeads(), 180);
        return () => window.clearTimeout(timeout);
    }, [loadLeads]);

    useEffect(() => {
        setPage(1);
    }, [assignedToId, brandId, search, sourceId, statusId, view]);

    function selectView(nextView: LeadView) {
        setView(nextView);
        setAssignedToId("");
    }

    if (isLoading && !data)
        return <DataLoading label="Loading sales pipeline..." />;
    if (error && !data)
        return <DataError message={error} onRetry={() => void loadLeads()} />;

    const leads = data?.items ?? [];
    const stats = data?.stats;
    const activeView = [...workViews, ...historyViews].find(
        (item) => item.value === view,
    );

    return (
        <div className="grid gap-6 xl:grid-cols-[240px_minmax(0,1fr)]">
            <aside className="space-y-5 xl:sticky xl:top-6 xl:self-start">
                <div>
                    <div className="px-2 text-xs font-semibold tracking-[0.14em] text-slate-600 uppercase">
                        Work queue
                    </div>
                    <div className="mt-2 space-y-1">
                        {workViews.map((item) => (
                            <SidebarLink
                                key={item.value}
                                active={view === item.value}
                                label={item.label}
                                description={item.description}
                                count={
                                    item.value === "my"
                                        ? stats?.mine
                                        : item.value === "unassigned"
                                          ? stats?.unassigned
                                          : stats?.active
                                }
                                onClick={() => selectView(item.value)}
                            />
                        ))}
                    </div>
                </div>

                <div className="border-t border-slate-800 pt-4">
                    <div className="px-2 text-xs font-semibold tracking-[0.14em] text-slate-700 uppercase">
                        History
                    </div>
                    <div className="mt-2 space-y-1">
                        {historyViews.map((item) => (
                            <SidebarLink
                                key={item.value}
                                active={view === item.value}
                                label={item.label}
                                description={item.description}
                                quiet
                                onClick={() => selectView(item.value)}
                            />
                        ))}
                    </div>
                </div>
            </aside>

            <div className="min-w-0 space-y-5">
                <div>
                    <h2 className="text-xl font-semibold text-white">
                        {activeView?.label || "My leads"}
                    </h2>
                    <p className="mt-1 text-sm text-slate-500">
                        {activeView?.description ||
                            "Active opportunities assigned to you"}
                    </p>
                </div>

                {stats ? (
                    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                        <StatCard
                            label="My leads"
                            value={stats.mine}
                            detail="Active and assigned to you"
                        />
                        <StatCard
                            label="Active pipeline"
                            value={stats.active}
                            detail="Not won, lost or converted"
                        />
                        <StatCard
                            label="Unassigned"
                            value={stats.unassigned}
                            detail="Active leads needing an owner"
                        />
                        <StatCard
                            label="New · 30 days"
                            value={stats.new_last_30_days}
                            detail="Fresh active opportunities"
                        />
                    </div>
                ) : null}

                <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-950/60">
                    <div className="grid gap-3 border-b border-slate-800 p-4 xl:grid-cols-[minmax(240px,1.5fr)_repeat(4,minmax(150px,1fr))]">
                        <Input
                            value={search}
                            onChange={(event) => setSearch(event.target.value)}
                            placeholder="Search name, company, email or enquiry..."
                            aria-label="Search leads"
                        />
                        <Select
                            value={statusId}
                            onChange={(event) =>
                                setStatusId(event.target.value)
                            }
                        >
                            <option value="">All statuses in this view</option>
                            {options.statuses.map((status) => (
                                <option key={status.id} value={status.id}>
                                    {status.name}
                                </option>
                            ))}
                        </Select>
                        <Select
                            value={sourceId}
                            onChange={(event) =>
                                setSourceId(event.target.value)
                            }
                        >
                            <option value="">All sources</option>
                            {options.sources.map((source) => (
                                <option key={source.id} value={source.id}>
                                    {source.name}
                                </option>
                            ))}
                        </Select>
                        <Select
                            value={brandId}
                            onChange={(event) => setBrandId(event.target.value)}
                        >
                            <option value="">All active brands</option>
                            {brands.map((brand) => (
                                <option key={brand.id} value={brand.id}>
                                    {brand.name}
                                </option>
                            ))}
                        </Select>
                        <Select
                            value={assignedToId}
                            onChange={(event) => {
                                const nextOwner = event.target.value;
                                setAssignedToId(nextOwner);
                                if (nextOwner && view === "my")
                                    setView("active");
                            }}
                        >
                            <option value="">Any owner in this view</option>
                            {options.assignees.map((assignee) => (
                                <option key={assignee.id} value={assignee.id}>
                                    {assignee.name}
                                </option>
                            ))}
                        </Select>
                    </div>

                    {view === "won" || view === "lost" || view === "all" ? (
                        <div className="border-b border-slate-800 bg-slate-900/40 px-4 py-2 text-xs text-slate-500">
                            This is a historical CRM view. Day-to-day work stays
                            in My leads, Unassigned and All active.
                        </div>
                    ) : null}

                    {error ? (
                        <div className="border-b border-slate-800 p-4">
                            <DataError
                                message={error}
                                onRetry={() => void loadLeads()}
                            />
                        </div>
                    ) : null}

                    {leads.length === 0 ? (
                        <EmptyState
                            title="No leads match this view"
                            description="Try changing the work queue or filters."
                        />
                    ) : (
                        <Table>
                            <TableHead>
                                <tr>
                                    <TableHeaderCell>Lead</TableHeaderCell>
                                    <TableHeaderCell>
                                        Sales stage
                                    </TableHeaderCell>
                                    <TableHeaderCell>Owner</TableHeaderCell>
                                    <TableHeaderCell>Brand</TableHeaderCell>
                                    <TableHeaderCell>Source</TableHeaderCell>
                                    <TableHeaderCell>Received</TableHeaderCell>
                                </tr>
                            </TableHead>
                            <TableBody>
                                {leads.map((lead) => (
                                    <TableRow key={lead.id}>
                                        <TableCell>
                                            <button
                                                type="button"
                                                onClick={() =>
                                                    setSelectedLeadId(lead.id)
                                                }
                                                className="text-left font-medium text-slate-100 transition hover:text-cyan-300"
                                            >
                                                {lead.company || lead.name}
                                            </button>
                                            <div className="mt-1 text-xs text-slate-500">
                                                {lead.name} · {lead.email}
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <Badge
                                                className={statusClasses(lead)}
                                            >
                                                {lead.status}
                                            </Badge>
                                        </TableCell>
                                        <TableCell className="text-slate-400">
                                            {lead.assigned_to_name ||
                                                "Unassigned"}
                                        </TableCell>
                                        <TableCell className="text-slate-400">
                                            {lead.brand}
                                        </TableCell>
                                        <TableCell className="text-slate-400">
                                            {lead.source}
                                        </TableCell>
                                        <TableCell className="text-slate-400">
                                            {formatDate(lead.created_at)}
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}

                    <Pagination
                        page={data?.page ?? page}
                        pageSize={data?.page_size ?? 25}
                        totalItems={data?.total ?? 0}
                        onPageChange={setPage}
                        disabled={isLoading}
                    />
                </div>
            </div>

            {selectedLeadId ? (
                <RecordDrawer
                    fullPageHref={`/admin/leads/${selectedLeadId}`}
                    onClose={() => {
                        setSelectedLeadId(null);
                        void loadLeads();
                    }}
                >
                    <div className="space-y-6">
                        <LeadWorkspace
                            leadId={selectedLeadId}
                            presentation="drawer"
                            onChanged={() => void loadLeads()}
                        />
                        <LeadEmailPanel leadId={selectedLeadId} />
                    </div>
                </RecordDrawer>
            ) : null}
        </div>
    );
}

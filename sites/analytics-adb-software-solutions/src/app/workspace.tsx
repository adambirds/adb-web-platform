"use client";

import {useCallback, useEffect, useState} from "react";
import {GoogleOnboarding} from "./onboarding";
import {
    api,
    apiUrl,
    ApiError,
    initialDates,
    loginUrl,
    type Business,
    type Report,
    type Row,
    type Session,
    type Website,
} from "./client";
import {
    IntegrationSettings,
    TrackingSettings,
    WorkspaceSettings,
} from "./settings";

type Section =
    | "overview"
    | "realtime"
    | "acquisition"
    | "pages"
    | "audience"
    | "events"
    | "key-events"
    | "search"
    | "queries"
    | "search-pages"
    | "opportunities"
    | "integrations"
    | "tracking"
    | "settings";
const NAV: [Section, string][] = [
    ["overview", "Overview"],
    ["realtime", "Right now"],
    ["acquisition", "Traffic sources"],
    ["pages", "Pages & engagement"],
    ["audience", "Audience"],
    ["events", "Events"],
    ["key-events", "Key events"],
    ["search", "Search performance"],
    ["queries", "Search queries"],
    ["search-pages", "Search pages"],
    ["opportunities", "SEO opportunities"],
    ["integrations", "Integrations"],
    ["tracking", "Tracking configuration"],
    ["settings", "Business & website"],
];
const METRIC_LABELS: Record<string, string> = {
    screenPageViews: "Page views",
    totalUsers: "Total visitors",
    activeUsers: "Active visitors",
    newUsers: "New visitors",
    averageEngagementTime: "Average engagement time (seconds)",
    engagementRate: "Engagement rate",
};
export const titleCase = (value: string): string =>
    METRIC_LABELS[value] ??
    value
        .replace(/([A-Z])/g, " $1")
        .replace(/_/g, " ")
        .replace(/^./, (c) => c.toUpperCase());
export const format = (value: unknown, key = ""): string =>
    value === null || value === undefined
        ? "—"
        : typeof value === "number"
          ? new Intl.NumberFormat(
                "en-GB",
                key === "ctr" || key.toLowerCase().includes("rate")
                    ? {style: "percent", maximumFractionDigits: 1}
                    : {maximumFractionDigits: 1},
            ).format(value)
          : String(value);

export function DataTable({
    rows,
    onSelect,
}: {
    rows: Row[];
    onSelect?: (row: Row) => void;
}) {
    const [order, setOrder] = useState<{key: string; desc: boolean}>({
        key: "",
        desc: true,
    });
    if (!rows.length)
        return (
            <p className="empty">
                No results for this period. Try another date range or filter.
            </p>
        );
    const keys = Object.keys(rows[0]);
    const sorted = order.key
        ? [...rows].sort(
              (a, b) =>
                  (typeof a[order.key] === "number"
                      ? Number(a[order.key]) - Number(b[order.key])
                      : String(a[order.key]).localeCompare(
                            String(b[order.key]),
                        )) * (order.desc ? -1 : 1),
          )
        : rows;
    return (
        <div className="table-scroll">
            <table>
                <thead>
                    <tr>
                        {keys.map((key) => (
                            <th key={key} scope="col">
                                <button
                                    onClick={() =>
                                        setOrder({
                                            key,
                                            desc:
                                                order.key === key
                                                    ? !order.desc
                                                    : true,
                                        })
                                    }
                                >
                                    {titleCase(key)}{" "}
                                    {order.key === key
                                        ? order.desc
                                            ? "↓"
                                            : "↑"
                                        : ""}
                                </button>
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {sorted.map((row, i) => (
                        <tr key={i}>
                            {keys.map((key, k) => (
                                <td key={key} title={format(row[key], key)}>
                                    {k === 0 && onSelect ? (
                                        <button onClick={() => onSelect(row)}>
                                            {format(row[key], key)}
                                        </button>
                                    ) : (
                                        format(row[key], key)
                                    )}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export function compareRows(rows: Row[], previous: Row[]): Row[] {
    const identity = (row: Row) =>
        JSON.stringify(
            Object.entries(row).filter(
                ([, value]) => typeof value === "string",
            ),
        );
    const old = new Map(previous.map((row) => [identity(row), row]));
    return rows.map((row) => {
        const metric = [
            "clicks",
            "sessions",
            "screenPageViews",
            "eventCount",
            "activeUsers",
        ].find((key) => typeof row[key] === "number");
        const prior = old.get(identity(row));
        if (!metric) return row;
        const baseline = prior?.[metric];
        return {
            ...row,
            [`${metric} change rate`]:
                typeof baseline === "number" && baseline !== 0
                    ? (Number(row[metric]) - baseline) / baseline
                    : null,
        };
    });
}

export function Trend({rows, metric}: {rows: Row[]; metric: string}) {
    const daily = new Map<string, number>();
    for (const row of rows) {
        const day = String(row.date);
        daily.set(day, (daily.get(day) ?? 0) + Number(row[metric] ?? 0));
    }
    const ordered = [...daily.entries()]
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([date, total]) => ({date, [metric]: total}));
    const max = Math.max(1, ...ordered.map((r) => Number(r[metric] ?? 0)));
    const points = ordered
        .map(
            (row, i) =>
                `${(i * 1000) / Math.max(1, ordered.length - 1)},${180 - (Number(row[metric] ?? 0) / max) * 160}`,
        )
        .join(" ");
    if (!rows.length) return null;
    return (
        <figure>
            <svg
                className="chart"
                viewBox="0 0 1000 200"
                preserveAspectRatio="none"
                role="img"
                aria-label={`${titleCase(metric)} trend, ${ordered.length} reported dates`}
            >
                <line
                    x1="0"
                    y1="180"
                    x2="1000"
                    y2="180"
                    stroke="currentColor"
                    opacity=".2"
                />
                <polyline
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    points={points}
                    vectorEffect="non-scaling-stroke"
                />
            </svg>
            <figcaption className="chart-labels">
                <span>{String(ordered[0]?.date)}</span>
                <span>
                    {titleCase(metric)} · peak {format(max)}
                </span>
                <span>{String(ordered.at(-1)?.date)}</span>
            </figcaption>
        </figure>
    );
}

export function AnalyticsApp() {
    const [session, setSession] = useState<Session | null>(null);
    const [businessId, setBusinessId] = useState(0);
    const [websiteId, setWebsiteId] = useState(0);
    const [section, setSection] = useState<Section>("overview");
    const [dates, setDates] = useState(initialDates);
    const [comparison, setComparison] = useState(true);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(true);
    const [revision, setRevision] = useState(0);
    const [addingWebsites, setAddingWebsites] = useState(false);
    const [mobileOpen, setMobileOpen] = useState(false);
    useEffect(() => {
        if (
            new URLSearchParams(window.location.search).get("integration") ===
            "connected"
        )
            setAddingWebsites(true);
    }, []);
    const reload = useCallback(async () => {
        const value = await api<Session>("/session");
        setSession(value);
        const requestedBusiness = Number(
            new URLSearchParams(window.location.search).get("business"),
        );
        setBusinessId((previous) =>
            value.businesses.some((b) => b.id === requestedBusiness)
                ? requestedBusiness
                : value.businesses.some((b) => b.id === previous)
                  ? previous
                  : (value.businesses.find((b) =>
                        b.websites.some((w) => w.id === value.website_id),
                    )?.id ??
                    value.businesses[0]?.id ??
                    0),
        );
        setWebsiteId((previous) =>
            value.businesses.some((b) =>
                b.websites.some((w) => w.id === previous),
            )
                ? previous
                : (value.website_id ??
                  value.businesses[0]?.websites[0]?.id ??
                  0),
        );
    }, []);
    useEffect(() => {
        let active = true;
        reload()
            .catch((err: unknown) => {
                if (err instanceof ApiError && err.status === 401)
                    window.location.replace(
                        loginUrl(
                            new URL(
                                "/dashboard",
                                window.location.origin,
                            ).toString(),
                        ),
                    );
                else if (active)
                    setError(
                        err instanceof Error
                            ? err.message
                            : "Could not load your businesses.",
                    );
            })
            .finally(() => {
                if (active) setLoading(false);
            });
        return () => {
            active = false;
        };
    }, [reload]);
    const business = session?.businesses.find((b) => b.id === businessId);
    const website =
        business?.websites.find((w) => w.id === websiteId) ??
        business?.websites[0];
    const refresh = async () => {
        await reload();
        setRevision((v) => v + 1);
    };
    if (loading)
        return (
            <main className="welcome" aria-busy="true">
                <p className="eyebrow">ADB Analytics</p>
                <h1>Opening your workspace…</h1>
            </main>
        );
    if (!session)
        return (
            <main className="welcome">
                <h1>Unable to open analytics</h1>
                <p role="alert">{error}</p>
                <button onClick={() => window.location.reload()}>
                    Try again
                </button>
            </main>
        );
    if (!business)
        return (
            <main className="welcome">
                <GoogleOnboarding onComplete={refresh} />
            </main>
        );
    if (!business.websites.length && business.role !== "viewer")
        return (
            <main className="welcome">
                <GoogleOnboarding business={business} onComplete={refresh} />
                <p className="signed-in">Signed in as {session.email}</p>
            </main>
        );
    return (
        <div className="shell">
            <div className="mobile-bar">
                <span className="wordmark">
                    adb<span> / analytics</span>
                </span>
                <button
                    aria-label="Toggle navigation"
                    aria-expanded={mobileOpen}
                    onClick={() => setMobileOpen(!mobileOpen)}
                >
                    Menu
                </button>
            </div>
            <aside className={mobileOpen ? "mobile-open" : ""}>
                <div className="wordmark">
                    <span className="app-mark" aria-hidden="true">
                        A
                    </span>
                    <span>
                        ADB <strong>Analytics</strong>
                    </span>
                </div>
                <div className="selectors">
                    <label>
                        Business
                        <select
                            value={business.id}
                            onChange={(e) => {
                                const selected = session.businesses.find(
                                    (b) => b.id === Number(e.target.value),
                                );
                                setBusinessId(Number(e.target.value));
                                setWebsiteId(selected?.websites[0]?.id ?? 0);
                            }}
                        >
                            {session.businesses.map((b) => (
                                <option key={b.id} value={b.id}>
                                    {b.name}
                                </option>
                            ))}
                        </select>
                    </label>
                    <label>
                        Website
                        <select
                            value={website?.id ?? ""}
                            onChange={(e) => {
                                setWebsiteId(Number(e.target.value));
                                void api("/preferences", "PUT", {
                                    website_id: Number(e.target.value),
                                }).catch((err) => setError(String(err)));
                            }}
                        >
                            {!website && (
                                <option value="">Add your first website</option>
                            )}
                            {business.websites.map((w) => (
                                <option key={w.id} value={w.id}>
                                    {w.name}
                                </option>
                            ))}
                        </select>
                    </label>
                </div>
                <nav aria-label="Analytics">
                    {NAV.filter(
                        ([key]) =>
                            business.role !== "viewer" ||
                            !["integrations", "tracking", "settings"].includes(
                                key,
                            ),
                    ).map(([key, label]) => (
                        <button
                            key={key}
                            aria-current={section === key ? "page" : undefined}
                            onClick={() => {
                                setError("");
                                setSection(key);
                                setAddingWebsites(false);
                                setMobileOpen(false);
                            }}
                        >
                            {label}
                        </button>
                    ))}
                </nav>
                {business.role !== "viewer" && (
                    <button
                        className="add-websites"
                        onClick={() => {
                            setAddingWebsites(true);
                            setMobileOpen(false);
                        }}
                    >
                        + Add websites
                    </button>
                )}
                <p className="account-summary">
                    <small>
                        {session.email}
                        <br />
                        {titleCase(business.role)}
                    </small>
                </p>
            </aside>
            <main>
                <header>
                    <div>
                        <p className="eyebrow">
                            {website?.domain ?? business.name}
                        </p>
                        <h1>
                            {addingWebsites
                                ? "Add websites"
                                : NAV.find(([key]) => key === section)?.[1]}
                        </h1>
                        <p className="muted">
                            {website
                                ? `Website performance · ${website.timezone}`
                                : "Connect your account to get started"}
                        </p>
                    </div>
                    {!addingWebsites && website && (
                        <div className="controls">
                            <label>
                                From
                                <input
                                    type="date"
                                    value={dates.start}
                                    max={dates.end}
                                    onChange={(e) =>
                                        setDates({
                                            ...dates,
                                            start: e.target.value,
                                        })
                                    }
                                />
                            </label>
                            <label>
                                To
                                <input
                                    type="date"
                                    value={dates.end}
                                    min={dates.start}
                                    max={new Date().toISOString().slice(0, 10)}
                                    onChange={(e) =>
                                        setDates({
                                            ...dates,
                                            end: e.target.value,
                                        })
                                    }
                                />
                            </label>
                            <label className="check">
                                <input
                                    type="checkbox"
                                    checked={comparison}
                                    onChange={(e) =>
                                        setComparison(e.target.checked)
                                    }
                                />
                                Previous period
                            </label>
                        </div>
                    )}
                </header>
                {error && (
                    <p className="notice error" role="alert">
                        {error}
                    </p>
                )}
                {addingWebsites ||
                !website ||
                (!website.providers.length && business.role !== "viewer") ? (
                    business.role === "viewer" ? (
                        <section className="panel empty">
                            <h2>No websites yet</h2>
                            <p>
                                Your workspace administrator can connect Google
                                and add websites.
                            </p>
                        </section>
                    ) : (
                        <GoogleOnboarding
                            key={business.id}
                            business={business}
                            onComplete={async () => {
                                await refresh();
                                setAddingWebsites(false);
                                setSection("overview");
                            }}
                            onCancel={
                                website?.providers.length
                                    ? () => setAddingWebsites(false)
                                    : undefined
                            }
                        />
                    )
                ) : section === "settings" ? (
                    <WorkspaceSettings
                        business={business}
                        website={website}
                        refresh={refresh}
                    />
                ) : section === "integrations" ? (
                    <IntegrationSettings
                        business={business}
                        website={website}
                        refresh={refresh}
                    />
                ) : section === "tracking" ? (
                    <TrackingSettings website={website} />
                ) : (
                    <Reports
                        key={`${website.id}:${section}`}
                        website={website}
                        section={section}
                        dates={dates}
                        comparison={comparison}
                        canManage={business.role !== "viewer"}
                        revision={revision}
                        refresh={() => setRevision((v) => v + 1)}
                        onIntegrations={() => setSection("integrations")}
                    />
                )}
                <footer>
                    <small>
                        ADB Analytics · Google Analytics and Search Console
                        measure different parts of your audience. Reports show
                        aggregate data, never individual visitor journeys.
                    </small>
                </footer>
            </main>
        </div>
    );
}

export function CreateBusiness({refresh}: {refresh: () => Promise<void>}) {
    const [error, setError] = useState("");
    return (
        <form
            onSubmit={async (e) => {
                e.preventDefault();
                const data = new FormData(e.currentTarget);
                try {
                    await api("/businesses", "POST", {name: data.get("name")});
                    await refresh();
                } catch (err) {
                    setError(String(err));
                }
            }}
        >
            <label>
                Business name
                <input name="name" required maxLength={255} />
            </label>
            <button className="primary">Create business</button>
            {error && <p role="alert">{error}</p>}
        </form>
    );
}

export function WebsiteForm({
    business,
    website,
    refresh,
}: {
    business: Business;
    website?: Website;
    refresh: () => Promise<void>;
}) {
    const [error, setError] = useState("");
    return (
        <form
            onSubmit={async (e) => {
                e.preventDefault();
                const data = new FormData(e.currentTarget);
                try {
                    await api(
                        website
                            ? `/websites/${website.id}`
                            : `/businesses/${business.id}/websites`,
                        website ? "PUT" : "POST",
                        {
                            name: data.get("name"),
                            domain: data.get("domain"),
                            timezone:
                                website?.timezone ??
                                Intl.DateTimeFormat().resolvedOptions()
                                    .timeZone,
                            is_active: data.get("active") === "on",
                        },
                    );
                    await refresh();
                } catch (err) {
                    setError(String(err));
                }
            }}
        >
            <label>
                Website name
                <input
                    name="name"
                    defaultValue={website?.name}
                    required
                    maxLength={255}
                />
            </label>
            <label>
                Domain
                <input
                    name="domain"
                    defaultValue={website?.domain}
                    placeholder="example.co.uk"
                    required
                />
            </label>
            <p className="muted">
                <small>
                    Timezone is detected from the linked Google Analytics
                    property{website ? ` · ${website.timezone}` : ""}.
                </small>
            </p>
            <label className="check">
                <input
                    type="checkbox"
                    name="active"
                    defaultChecked={website?.is_active ?? true}
                />
                Active
            </label>
            <button className="primary">
                {website ? "Save website" : "Add website"}
            </button>
            {error && <p role="alert">{error}</p>}
        </form>
    );
}

function Reports({
    website,
    section,
    dates,
    comparison,
    canManage,
    revision,
    refresh,
    onIntegrations,
}: {
    website: Website;
    section: Section;
    dates: {start: string; end: string};
    comparison: boolean;
    canManage: boolean;
    revision: number;
    refresh: () => void;
    onIntegrations: () => void;
}) {
    const provider = [
        "search",
        "queries",
        "search-pages",
        "opportunities",
    ].includes(section)
        ? "gsc"
        : "ga4";
    const reportName =
        (
            {
                overview: "overview",
                search: "overview",
                "search-pages": "pages",
                audience: "devices",
                "key-events": "events",
            } as Record<string, string>
        )[section] ?? section;
    const linked = website.providers.some((p) => p.provider === provider);
    const [report, setReport] = useState<Report | null>(null);
    const [extra, setExtra] = useState<Row[]>([]);
    const [notice, setNotice] = useState("");
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const [filter, setFilter] = useState("");
    const [page, setPage] = useState(1);
    const [breakdown, setBreakdown] = useState("devices");
    const [searchBreakdown, setSearchBreakdown] = useState("overview");
    const [table, setTable] = useState(false);
    const [selected, setSelected] = useState<Row | null>(null);
    const [parameter, setParameter] = useState("");
    const [configuredEvents, setConfiguredEvents] = useState<
        {eventName: string}[]
    >([]);
    const [parameterRows, setParameterRows] = useState<Row[] | null>(null);
    const [syncRevision, setSyncRevision] = useState(0);
    const [jobs, setJobs] = useState<
        {id: number; status: string; progress: number; error_code: string}[]
    >([]);
    const query = new URLSearchParams({
        ...dates,
        search: filter,
        page: String(page),
    }).toString();
    const name =
        section === "audience"
            ? breakdown
            : section === "search"
              ? searchBreakdown
              : reportName;
    useEffect(() => {
        if (!linked) return;
        let active = true;
        setBusy(true);
        setError("");
        setSelected(null);
        setExtra([]);
        setParameterRows(null);
        const fetchData = async () => {
            if (section === "realtime") {
                const value = await api<{
                    rows: Row[];
                    totals: Row[];
                    limitations: string;
                }>(`/websites/${website.id}/realtime`);
                if (active) {
                    setExtra(value.rows);
                    setNotice(value.limitations);
                    setReport({
                        current: {
                            rows: value.totals,
                            complete: true,
                            measurement: "Last 30 minutes",
                            updated_at: new Date().toISOString(),
                        },
                        previous: null,
                        total: value.rows.length,
                        status: "available",
                        last_synced_at: null,
                        error_code: "",
                    });
                }
            } else if (section === "opportunities") {
                const value = await api<{
                    items: {subject: string; reasons: string[]}[];
                }>(`/websites/${website.id}/opportunities?${query}`);
                if (active) {
                    setExtra(
                        value.items.map((item) => ({
                            subject: item.subject,
                            opportunity: item.reasons.join(" "),
                        })),
                    );
                    setNotice(
                        "Heuristic suggestions, using at least 100 impressions. Review alongside the full context.",
                    );
                }
            } else {
                const value = await api<Report>(
                    `/websites/${website.id}/reports/${provider}/${name}?${query}`,
                );
                if (active) {
                    setReport(value);
                    setNotice(value.current?.limitations ?? "");
                }
                if (section === "key-events") {
                    const configured = await api<{
                        items: {eventName: string}[];
                    }>(`/websites/${website.id}/key-events`);
                    if (active) setConfiguredEvents(configured.items);
                }
                if (
                    ["overview", "search", "events"].includes(section) &&
                    (section !== "search" || name === "overview")
                ) {
                    const trend = await api<Report>(
                        `/websites/${website.id}/reports/${provider}/trend?${query}&page_size=400`,
                    );
                    if (active) setExtra(trend.current?.rows ?? []);
                }
            }
        };
        void fetchData()
            .catch((err) => {
                if (active) setError(String(err));
            })
            .finally(() => {
                if (active) setBusy(false);
            });
        return () => {
            active = false;
        };
    }, [
        website.id,
        linked,
        section,
        provider,
        name,
        query,
        revision,
        syncRevision,
    ]);
    useEffect(() => {
        let active = true;
        let completed = "";
        const poll = async () => {
            try {
                const value = await api<typeof jobs>(
                    `/websites/${website.id}/sync`,
                );
                if (active) {
                    setJobs(value);
                    const signature = value
                        .filter((job) => job.status === "complete")
                        .map((job) => job.id)
                        .sort()
                        .join(",");
                    if (signature && signature !== completed)
                        setSyncRevision((previous) => previous + 1);
                    completed = signature;
                }
            } catch {
                /* Report requests surface session/network errors. */
            }
        };
        void poll();
        const timer = window.setInterval(poll, 10000);
        return () => {
            active = false;
            window.clearInterval(timer);
        };
    }, [website.id, revision]);
    if (!linked)
        return (
            <section className="panel empty">
                <h2>
                    Connect{" "}
                    {provider === "ga4" ? "Google Analytics" : "Search Console"}
                </h2>
                <p>
                    Connect a Google account and select a property to start
                    seeing your website’s performance.
                </p>
                {canManage && (
                    <button className="primary" onClick={onIntegrations}>
                        Set up integration
                    </button>
                )}
            </section>
        );
    const sync = async () => {
        setBusy(true);
        try {
            await api(`/websites/${website.id}/sync`, "POST", dates);
            setNotice(
                "Synchronization queued for this range and the previous period. Refresh reports once it completes.",
            );
            refresh();
        } catch (err) {
            setError(String(err));
        } finally {
            setBusy(false);
        }
    };
    const summary = report?.current?.rows[0];
    const rows = (report?.current?.rows ?? []).filter(
        (row) => section !== "key-events" || Number(row.keyEvents) > 0,
    );
    const activeJobs = jobs.filter((job) =>
        ["queued", "running", "retrying"].includes(job.status),
    );
    return (
        <>
            <div className="actions">
                {canManage && section !== "realtime" && (
                    <button
                        disabled={busy || activeJobs.length > 0}
                        onClick={sync}
                    >
                        Synchronize date range
                    </button>
                )}
                <button disabled={busy} onClick={refresh}>
                    Refresh reports
                </button>
                {report?.current && section !== "realtime" && (
                    <a
                        className="button"
                        href={apiUrl(
                            `/websites/${website.id}/reports/${provider}/${name}?${query}&export=true`,
                        )}
                    >
                        Export CSV
                    </a>
                )}
                {section === "audience" && (
                    <label>
                        Breakdown
                        <select
                            value={breakdown}
                            onChange={(e) => setBreakdown(e.target.value)}
                        >
                            <option value="devices">Devices</option>
                            <option value="browsers">Browsers</option>
                            <option value="countries">Countries</option>
                        </select>
                    </label>
                )}
                {section === "search" && (
                    <label>
                        Search breakdown
                        <select
                            value={searchBreakdown}
                            onChange={(e) => {
                                setSearchBreakdown(e.target.value);
                                setPage(1);
                            }}
                        >
                            <option value="overview">Overview</option>
                            <option value="countries">Countries</option>
                            <option value="devices">Devices</option>
                        </select>
                    </label>
                )}
                <label>
                    Filter results
                    <input
                        value={filter}
                        onChange={(e) => {
                            setFilter(e.target.value);
                            setPage(1);
                        }}
                        placeholder="Find a page, event or source"
                    />
                </label>
            </div>
            {activeJobs.map((job) => (
                <div className="notice" key={job.id}>
                    Sync {job.status} · {job.progress}%
                    <progress value={job.progress} max={100} />
                </div>
            ))}
            {error && (
                <p className="notice error" role="alert">
                    {error}
                </p>
            )}
            {notice && <p className="notice">{notice}</p>}
            {report?.error_code && (
                <p className="notice error" role="alert">
                    Integration needs attention: {report.error_code}. Check
                    Integrations and retry synchronization.
                </p>
            )}
            {jobs[0]?.status === "failed" && (
                <p className="notice error" role="alert">
                    Latest synchronization failed: {jobs[0].error_code}. Retry
                    or reconnect Google in Integrations.
                </p>
            )}
            {section === "key-events" && (
                <section className="panel">
                    <h2>Configured key events</h2>
                    {configuredEvents.length ? (
                        configuredEvents.map((event) => (
                            <p key={event.eventName}>{event.eventName}</p>
                        ))
                    ) : (
                        <p>
                            No configured key events have been synchronized yet.
                        </p>
                    )}
                    <p>
                        <small>
                            The report below shows key event activity during the
                            selected period.
                        </small>
                    </p>
                </section>
            )}
            {busy ? (
                <p aria-busy="true" className="empty">
                    Loading report…
                </p>
            ) : section === "opportunities" ? (
                <DataTable rows={extra} />
            ) : !report?.current ? (
                <section className="panel empty">
                    <h2>
                        {activeJobs.length
                            ? "Preparing your reports"
                            : "This date range hasn’t been synchronized yet."}
                    </h2>
                    <p>
                        {activeJobs.length
                            ? "Your Google data is syncing in the background. Reports appear here automatically when ready."
                            : canManage
                              ? "Choose Synchronize date range above to prepare this report and its comparison."
                              : "Ask a business administrator to synchronize this date range."}
                    </p>
                </section>
            ) : (
                <>
                    {["overview", "search", "realtime"].includes(section) &&
                        (section !== "search" || name === "overview") &&
                        summary && (
                            <div className="hero">
                                {Object.entries(summary)
                                    .filter(
                                        ([key]) =>
                                            ![
                                                "engagedSessions",
                                                "userEngagementDuration",
                                            ].includes(key),
                                    )
                                    .map(([key, value]) => {
                                        const prior =
                                            report.previous?.rows[0]?.[key];
                                        const delta =
                                            typeof value === "number" &&
                                            typeof prior === "number" &&
                                            prior !== 0
                                                ? (value - prior) / prior
                                                : null;
                                        return (
                                            <div className="metric" key={key}>
                                                <small>{titleCase(key)}</small>
                                                <strong>
                                                    {format(value, key)}
                                                </strong>
                                                {comparison &&
                                                    section !== "realtime" && (
                                                        <small>
                                                            {delta === null
                                                                ? "Previous period unavailable"
                                                                : `${delta >= 0 ? "+" : ""}${format(delta, "rate")} vs previous period`}
                                                        </small>
                                                    )}
                                            </div>
                                        );
                                    })}
                            </div>
                        )}
                    {extra.length > 0 && section !== "realtime" && (
                        <section className="panel">
                            <div className="actions">
                                <h2>Performance over time</h2>
                                <button onClick={() => setTable(!table)}>
                                    {table ? "Show chart" : "Show data table"}
                                </button>
                            </div>
                            {table ? (
                                <DataTable rows={extra} />
                            ) : (
                                <Trend
                                    rows={extra}
                                    metric={
                                        provider === "gsc"
                                            ? "clicks"
                                            : section === "events"
                                              ? "eventCount"
                                              : "sessions"
                                    }
                                />
                            )}
                        </section>
                    )}
                    {section === "realtime" ? (
                        <DataTable rows={extra} />
                    ) : (
                        (!["overview", "search"].includes(section) ||
                            (section === "search" && name !== "overview")) && (
                            <DataTable
                                rows={
                                    comparison && report.previous
                                        ? compareRows(
                                              rows,
                                              report.previous.rows,
                                          )
                                        : rows
                                }
                                onSelect={
                                    [
                                        "pages",
                                        "events",
                                        "search-pages",
                                    ].includes(section)
                                        ? setSelected
                                        : undefined
                                }
                            />
                        )
                    )}
                    <div className="actions">
                        {page > 1 && (
                            <button onClick={() => setPage((p) => p - 1)}>
                                Previous page
                            </button>
                        )}
                        {report.total > page * 100 && (
                            <button onClick={() => setPage((p) => p + 1)}>
                                Next page
                            </button>
                        )}
                    </div>
                    {selected && (
                        <section className="panel">
                            <h2>
                                Selected{" "}
                                {section === "events" ? "event" : "page"}
                            </h2>
                            <DataTable rows={[selected]} />
                            {section === "events" ? (
                                <>
                                    <EventTrend
                                        website={website}
                                        dates={dates}
                                        event={String(selected.eventName)}
                                    />
                                    <p>
                                        Only registered custom dimensions can
                                        provide parameter breakdowns. Ask an
                                        administrator to refresh tracking
                                        definitions if a registered parameter is
                                        missing.
                                    </p>
                                    <div className="actions">
                                        <label>
                                            Parameter name
                                            <input
                                                value={parameter}
                                                onChange={(e) =>
                                                    setParameter(e.target.value)
                                                }
                                                placeholder="button_id"
                                            />
                                        </label>
                                        <button
                                            onClick={async () => {
                                                try {
                                                    const value = await api<{
                                                        rows: Row[];
                                                    }>(
                                                        `/websites/${website.id}/events/${encodeURIComponent(String(selected.eventName))}/parameters?${new URLSearchParams({...dates, parameter})}`,
                                                    );
                                                    setParameterRows(
                                                        value.rows,
                                                    );
                                                } catch (err) {
                                                    setError(String(err));
                                                }
                                            }}
                                        >
                                            Inspect parameter
                                        </button>
                                    </div>
                                    {parameterRows && (
                                        <DataTable rows={parameterRows} />
                                    )}
                                </>
                            ) : (
                                <CombinedPage
                                    website={website}
                                    dates={dates}
                                    page={String(
                                        selected.page ??
                                            selected.pageLocation ??
                                            `https://${selected.hostName}${selected.pagePathPlusQueryString}`,
                                    )}
                                />
                            )}
                        </section>
                    )}
                    <p>
                        <small>
                            {report.current.measurement} · Updated{" "}
                            {new Date(report.current.updated_at).toLocaleString(
                                "en-GB",
                            )}
                            {!report.current.complete &&
                                " · Truncated at the configured provider row limit"}
                        </small>
                    </p>
                </>
            )}
        </>
    );
}

function CombinedPage({
    website,
    dates,
    page,
}: {
    website: Website;
    dates: {start: string; end: string};
    page: string;
}) {
    const [value, setValue] = useState<{
        rows: {
            url: string;
            ga4?: Row;
            gsc?: Row;
            ga4_page_trend?: Row[];
            gsc_page_trend?: Row[];
            ga4_page_events?: Row[];
        }[];
        notice: string;
    } | null>(null);
    const [error, setError] = useState("");
    useEffect(() => {
        let active = true;
        void api<NonNullable<typeof value>>(
            `/websites/${website.id}/combined?${new URLSearchParams({...dates, page})}`,
        )
            .then((result) => {
                if (active) setValue(result);
            })
            .catch((err) => {
                if (active) setError(String(err));
            });
        return () => {
            active = false;
        };
    }, [website.id, dates.start, dates.end, page]);
    return (
        <>
            {error && <p role="alert">{error}</p>}
            {value?.rows.map((row) => (
                <div key={row.url}>
                    <h3>Google Analytics</h3>
                    {row.ga4 ? (
                        <DataTable rows={[row.ga4]} />
                    ) : (
                        <p>No matching GA4 page data.</p>
                    )}
                    {row.ga4_page_trend && (
                        <Trend rows={row.ga4_page_trend} metric="sessions" />
                    )}
                    {row.ga4_page_events && (
                        <>
                            <h3>Events on this page</h3>
                            <DataTable rows={row.ga4_page_events} />
                        </>
                    )}
                    <h3>Search Console</h3>
                    {row.gsc ? (
                        <DataTable rows={[row.gsc]} />
                    ) : (
                        <p>No matching Search Console canonical URL.</p>
                    )}
                    {row.gsc_page_trend && (
                        <Trend rows={row.gsc_page_trend} metric="clicks" />
                    )}
                </div>
            ))}
            <p className="muted">{value?.notice}</p>
        </>
    );
}

function EventTrend({
    website,
    dates,
    event,
}: {
    website: Website;
    dates: {start: string; end: string};
    event: string;
}) {
    const [rows, setRows] = useState<Row[]>([]);
    const [error, setError] = useState("");
    useEffect(() => {
        let active = true;
        void api<{rows: Row[]}>(
            `/websites/${website.id}/events/${encodeURIComponent(event)}/trend?${new URLSearchParams(dates)}`,
        )
            .then((value) => {
                if (active) setRows(value.rows);
            })
            .catch((err) => {
                if (active) setError(String(err));
            });
        return () => {
            active = false;
        };
    }, [website.id, dates.start, dates.end, event]);
    return (
        <>
            {error && <p role="alert">{error}</p>}
            <Trend rows={rows} metric="eventCount" />
        </>
    );
}

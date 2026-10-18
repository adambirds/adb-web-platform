"use client";
import {useEffect, useState} from "react";
import {
    api,
    apiUrl,
    type Report,
    type Row,
    type Website,
} from "../../app/client";
import {format, titleCase} from "../../lib/format";
import {DataTable, compareRows} from "./ReportTable";
import {Trend} from "../experience/ActivityChart";
import {CombinedPage, EventTrend} from "./ReportDetails";
export type Section =
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
export function Reports({
    website,
    section,
    dates,
    comparison,
    canManage,
    revision,
    refresh,
    onIntegrations,
    initialSearch = "",
}: {
    website: Website;
    section: Section;
    dates: {start: string; end: string};
    comparison: boolean;
    canManage: boolean;
    revision: number;
    refresh: () => void;
    onIntegrations: () => void;
    initialSearch?: string;
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
    const [filter, setFilter] = useState(initialSearch);
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

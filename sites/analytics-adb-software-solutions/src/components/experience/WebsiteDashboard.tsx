"use client";
import {useEffect, useState} from "react";
import Link from "next/link";
import {
    ArrowLeftIcon,
    ArrowRightIcon,
    ArrowPathIcon,
    ArrowUpRightIcon,
    BoltIcon,
    CursorArrowRaysIcon,
    MagnifyingGlassIcon,
    UsersIcon,
} from "@heroicons/react/24/outline";
import {api, type Row} from "../../app/client";
import {
    change,
    compact,
    exploreHref,
    number,
    series,
    siteHref,
    type DashboardData,
} from "../../lib/experience";
import {ActivityChart} from "./ActivityChart";
import {
    ErrorState,
    LoadingExperience,
    useExperience,
} from "./ExperienceProvider";
import {Insights} from "./Insights";
import {MetricCard} from "./MetricCard";
import {PeriodControls} from "./PeriodControls";
import {RankedList} from "./RankedList";
import {DetailDrawer, type Selection} from "./DetailDrawer";
import {useResource} from "./useResource";
import {Tabs} from "./Tabs";

const metrics = [
    {key: "totalUsers", label: "Visitors", provider: "ga4", icon: UsersIcon},
    {
        key: "sessions",
        label: "Visits",
        provider: "ga4",
        icon: CursorArrowRaysIcon,
    },
    {
        key: "clicks",
        label: "Search clicks",
        provider: "gsc",
        icon: MagnifyingGlassIcon,
    },
    {key: "keyEvents", label: "Key events", provider: "ga4", icon: BoltIcon},
];
export function WebsiteDashboard({websiteId}: {websiteId: number}) {
    const {session, period, comparison} = useExperience();
    const website = session.businesses
        .flatMap((business) => business.websites)
        .find((site) => site.id === websiteId);
    const business = session.businesses.find(
        (item) => item.id === website?.business_id,
    );
    const {data, error, loading, reload} = useResource<DashboardData>(
        website
            ? `/websites/${websiteId}/dashboard?${new URLSearchParams(period)}`
            : null,
    );
    const [metric, setMetric] = useState("totalUsers"),
        [sourceTab, setSourceTab] = useState("channels"),
        [pageTab, setPageTab] = useState("pages"),
        [audienceTab, setAudienceTab] = useState("countries");
    const [selection, setSelection] = useState<Selection | null>(null),
        [syncError, setSyncError] = useState(""),
        [syncing, setSyncing] = useState(false);
    useEffect(() => {
        if (!data?.site.syncing) return;
        const timer = window.setInterval(reload, 10000);
        return () => window.clearInterval(timer);
    }, [data?.site.syncing, reload]);
    if (!website)
        return (
            <main className="experience-page">
                <ErrorState
                    message="This website is not available in your workspace."
                    retry={reload}
                />
                <Link className="text-link" href="/dashboard">
                    Back to portfolio
                </Link>
            </main>
        );
    if (!data && loading) return <LoadingExperience />;
    if (!data)
        return (
            <main className="experience-page">
                <ErrorState
                    message={error || "Website reports are not available."}
                    retry={reload}
                />
            </main>
        );
    const report = (provider: string, name: string) =>
        data.reports[provider]?.[name];
    const ga = report("ga4", "overview")?.current?.rows[0],
        priorGa = report("ga4", "overview")?.previous?.rows[0],
        search = report("gsc", "overview")?.current?.rows[0],
        priorSearch = report("gsc", "overview")?.previous?.rows[0];
    const activeMetric = metrics.find((item) => item.key === metric)!;
    const trend = report(activeMetric.provider, "trend");
    const activity = series(
        trend?.current?.rows ?? null,
        trend?.previous?.rows ?? null,
        metric,
        period,
    );
    const available = Boolean(ga || search);
    const sourceRows = report("ga4", sourceTab)?.current?.rows ?? [];
    const pages = report("ga4", pageTab)?.current?.rows ?? [];
    const events = report("ga4", "events")?.current?.rows ?? [];
    const queries = report("gsc", "queries")?.current?.rows ?? [];
    const audience = report("ga4", audienceTab)?.current?.rows ?? [];
    const open = (
        type: Selection["type"],
        label: string,
        row: Row,
        reportName: string,
    ) => setSelection({type, label, row, report: reportName});
    const sourceDimension =
        sourceTab === "channels"
            ? "sessionDefaultChannelGroup"
            : "sessionSourceMedium";
    const pageDimension =
        pageTab === "pages" ? "pageLocation" : "landingPagePlusQueryString";
    const audienceDimension =
        audienceTab === "countries"
            ? "country"
            : audienceTab === "devices"
              ? "deviceCategory"
              : "browser";
    return (
        <main className="experience-page website-page">
            <Link
                className="back-link"
                href={"/dashboard?" + new URLSearchParams(period)}
            >
                <ArrowLeftIcon />
                All websites
            </Link>
            <div className="page-heading">
                <div className="site-heading">
                    <span className="site-avatar large">
                        {website.domain
                            .replace(/^www\./, "")
                            .slice(0, 1)
                            .toUpperCase()}
                    </span>
                    <div>
                        <h1>{website.domain}</h1>
                        <p className="page-description">
                            <span
                                className={`status-dot ${data.site.syncing ? "working" : ""}`}
                            />
                            {data.site.syncing
                                ? "Reports are updating"
                                : data.site.updated_at
                                  ? `Last synced ${new Date(data.site.updated_at).toLocaleDateString("en-GB", {day: "numeric", month: "short"})}`
                                  : "Waiting for your first reports"}
                            <span className="separator">·</span>
                            {website.timezone}
                        </p>
                    </div>
                </div>
                <PeriodControls />
            </div>
            <div className="site-toolbar">
                <nav aria-label="Website views">
                    <span className="active-view">Overview</span>
                    <Link href={exploreHref(website.id, "events", period)}>
                        Explore
                        <ArrowUpRightIcon />
                    </Link>
                    {business?.role !== "viewer" && (
                        <Link href={siteHref(website.id, period, "/settings")}>
                            Manage website
                        </Link>
                    )}
                </nav>
                <div>
                    {business?.role !== "viewer" && (
                        <button
                            className="text-link"
                            disabled={syncing || data.site.syncing}
                            onClick={async () => {
                                setSyncing(true);
                                setSyncError("");
                                try {
                                    await api(
                                        `/websites/${websiteId}/sync`,
                                        "POST",
                                        period,
                                    );
                                    reload();
                                } catch (err) {
                                    setSyncError(String(err));
                                } finally {
                                    setSyncing(false);
                                }
                            }}
                        >
                            <ArrowPathIcon />
                            {data.site.syncing ? "Syncing…" : "Sync date range"}
                        </button>
                    )}
                    <button className="text-link" onClick={reload}>
                        Refresh
                    </button>
                </div>
            </div>
            {(error || syncError) && (
                <ErrorState message={error || syncError} retry={reload} />
            )}
            {data.site.issues.length > 0 && (
                <div className="data-notice warning">
                    A Google connection needs attention:{" "}
                    {data.site.issues.join(", ")}.{" "}
                    <Link href={siteHref(websiteId, period, "/settings")}>
                        Review connection
                    </Link>
                </div>
            )}
            {data.site.shared_providers?.length > 0 && (
                <div className="data-notice">
                    This website shares a reporting property with another linked
                    website. Figures cover the whole Google property; they are
                    not domain-filtered. Portfolio totals count shared
                    properties once.
                </div>
            )}
            {!available && (
                <div className="data-notice">
                    {data.site.syncing
                        ? "We’re preparing your Google reports. This page updates automatically when they’re ready."
                        : "No snapshot covers this date range yet. Sync this period to load real reports; missing data is not zero activity."}
                </div>
            )}
            <div className="metric-grid">
                {metrics.map((item) => (
                    <MetricCard
                        key={item.key}
                        label={item.label}
                        value={
                            item.provider === "ga4"
                                ? ga?.[item.key]
                                : search?.[item.key]
                        }
                        delta={change(
                            item.provider === "ga4"
                                ? ga?.[item.key]
                                : search?.[item.key],
                            item.provider === "ga4"
                                ? priorGa?.[item.key]
                                : priorSearch?.[item.key],
                        )}
                        icon={<item.icon />}
                        selected={metric === item.key}
                        onClick={() => setMetric(item.key)}
                        comparison={comparison}
                    />
                ))}
            </div>
            <section className="activity-card site-activity">
                <div className="report-card-heading">
                    <div>
                        <h2>{activeMetric.label} over time</h2>
                        <p>
                            {metric === "clicks"
                                ? "Discovery in Google Search"
                                : "The rhythm of your website"}{" "}
                            · click a point to inspect that day
                        </p>
                    </div>
                    <div className="chart-legend">
                        <span>
                            <i />
                            This period
                        </span>
                        {comparison && (
                            <span>
                                <i />
                                Previous
                            </span>
                        )}
                    </div>
                </div>
                <ActivityChart
                    data={activity}
                    label={activeMetric.label}
                    comparison={comparison}
                    onDay={(day) => {
                        const point = activity.find((row) => row.date === day);
                        if (point) open("day", day, point, "overview");
                    }}
                />
                <div className="engagement-strip">
                    <div>
                        <span>Engagement rate</span>
                        <strong>
                            {compact(ga?.engagementRate, "engagementRate")}
                        </strong>
                    </div>
                    <div>
                        <span>Avg. engagement</span>
                        <strong>
                            {compact(
                                ga?.averageEngagementTime,
                                "averageEngagementTime",
                            )}
                        </strong>
                    </div>
                    <div>
                        <span>Page views</span>
                        <strong>{compact(ga?.screenPageViews)}</strong>
                    </div>
                    <div>
                        <span>Search impressions</span>
                        <strong>{compact(search?.impressions)}</strong>
                    </div>
                    <div>
                        <span>Search click rate</span>
                        <strong>{compact(search?.ctr, "ctr")}</strong>
                    </div>
                </div>
            </section>
            <div className="section-heading dashboard-section-title">
                <div>
                    <p className="eyebrow">THE STORY BEHIND THE NUMBERS</p>
                    <h2>What brings people in. What they do next.</h2>
                </div>
                <span className="section-help">
                    Click any row to investigate
                </span>
            </div>
            {Object.values(data.reports).some((provider) =>
                Object.values(provider).some(
                    (pair) => pair.current?.complete === false,
                ),
            ) && (
                <p className="data-notice warning">
                    Some provider reports are truncated. These rankings show
                    available rows, not guaranteed complete totals.
                </p>
            )}
            <div className="report-grid">
                <RankedList
                    title="Traffic sources"
                    subtitle="Where your visits begin"
                    metric="Visits"
                    tone="blue"
                    href={exploreHref(websiteId, "acquisition", period)}
                    tabs={
                        <Tabs
                            values={[
                                ["channels", "Channels"],
                                ["referrals", "Sources & referrals"],
                            ]}
                            value={sourceTab}
                            onChange={setSourceTab}
                        />
                    }
                    items={sourceRows.slice(0, 7).map((row) => ({
                        label: String(row[sourceDimension] ?? "Unknown"),
                        value: number(row.sessions),
                        secondary:
                            row.engagementRate === undefined
                                ? undefined
                                : `${compact(row.engagementRate, "engagementRate")} engaged`,
                        onClick: () =>
                            open(
                                "source",
                                String(row[sourceDimension]),
                                row,
                                sourceTab,
                            ),
                    }))}
                />
                <RankedList
                    title="Top content"
                    subtitle="The pages people spend time with"
                    metric="Visits"
                    tone="teal"
                    href={exploreHref(websiteId, "pages", period)}
                    tabs={
                        <Tabs
                            values={[
                                ["pages", "All pages"],
                                ["landing", "Landing pages"],
                            ]}
                            value={pageTab}
                            onChange={setPageTab}
                        />
                    }
                    items={pages.slice(0, 7).map((row) => ({
                        label: pageLabel(
                            String(
                                row[pageDimension] ??
                                    row.pagePathPlusQueryString ??
                                    "/",
                            ),
                        ),
                        detail: row.hostName ? String(row.hostName) : undefined,
                        value: number(row.sessions),
                        onClick: () =>
                            open(
                                "page",
                                String(
                                    row[pageDimension] ??
                                        row.pageLocation ??
                                        `https://${row.hostName ?? website.domain}${row.pagePathPlusQueryString ?? "/"}`,
                                ),
                                row,
                                pageTab,
                            ),
                    }))}
                />
                <RankedList
                    title="Events & key actions"
                    subtitle="The interactions that matter"
                    metric="Events"
                    tone="violet"
                    href={exploreHref(websiteId, "events", period)}
                    items={events.slice(0, 7).map((row) => ({
                        label: String(row.eventName),
                        value: number(row.eventCount),
                        secondary: row.keyEvents
                            ? `${compact(row.keyEvents)} key events`
                            : undefined,
                        onClick: () =>
                            open("event", String(row.eventName), row, "events"),
                    }))}
                />
                <RankedList
                    title="Search discovery"
                    subtitle="What people search before finding you"
                    metric="Clicks"
                    tone="amber"
                    href={exploreHref(websiteId, "queries", period)}
                    items={queries.slice(0, 7).map((row) => ({
                        label: String(row.query),
                        value: number(row.clicks),
                        secondary: `${compact(row.impressions)} impressions`,
                        onClick: () =>
                            open("query", String(row.query), row, "queries"),
                    }))}
                />
            </div>
            <div className="site-bottom-grid">
                <RankedList
                    title="Your audience"
                    subtitle="A little more context about your visitors"
                    metric="Active visitors"
                    tone="blue"
                    href={exploreHref(websiteId, "audience", period)}
                    tabs={
                        <Tabs
                            values={[
                                ["countries", "Countries"],
                                ["devices", "Devices"],
                                ["browsers", "Browsers"],
                            ]}
                            value={audienceTab}
                            onChange={setAudienceTab}
                        />
                    }
                    items={audience.slice(0, 6).map((row) => ({
                        label: String(row[audienceDimension]),
                        value: number(row.activeUsers),
                        onClick: () =>
                            open(
                                "audience",
                                String(row[audienceDimension]),
                                row,
                                audienceTab,
                            ),
                    }))}
                />
                <section className="site-insights report-card">
                    <div className="report-card-heading">
                        <div>
                            <span className="section-kicker">
                                CONNECTING THE DOTS
                            </span>
                            <h2>Ideas worth investigating</h2>
                            <p>Evidence first. No invented attribution.</p>
                        </div>
                        <BoltIcon />
                    </div>
                    <Insights
                        items={data.insights.slice(0, 3)}
                        period={period}
                    />
                </section>
            </div>
            <div className="explore-callout">
                <span className="insight-icon">
                    <MagnifyingGlassIcon />
                </span>
                <div>
                    <h2>A question worth going deeper on?</h2>
                    <p>
                        Explore events, pages, acquisition and search with
                        detailed metrics, parameter breakdowns and exports.
                    </p>
                </div>
                <Link
                    className="button"
                    href={exploreHref(websiteId, "events", period)}
                >
                    Open explorer
                    <ArrowRightIcon />
                </Link>
            </div>
            <p className="portfolio-disclaimer">
                Visitors come from GA4. Search performance comes from Search
                Console. These measure different activity; matching pages does
                not establish person-level attribution. Search dates use Pacific
                Time.
            </p>
            {selection && (
                <DetailDrawer
                    selection={selection}
                    website={website}
                    data={data}
                    period={period}
                    onClose={() => setSelection(null)}
                />
            )}
        </main>
    );
}
function pageLabel(value: string) {
    try {
        const url = new URL(value);
        return url.pathname + url.search;
    } catch {
        return value;
    }
}

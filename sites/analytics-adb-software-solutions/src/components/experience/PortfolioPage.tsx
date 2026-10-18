"use client";
import {useEffect, useState} from "react";
import Link from "next/link";
import {
    ArrowPathIcon,
    ArrowRightIcon,
    ArrowUpRightIcon,
    BoltIcon,
    CursorArrowRaysIcon,
    GlobeAltIcon,
    MagnifyingGlassIcon,
    UsersIcon,
} from "@heroicons/react/24/outline";
import type {Portfolio, SiteSummary} from "../../lib/experience";
import {change, compact, number, series, siteHref} from "../../lib/experience";
import {GoogleOnboarding} from "../../app/onboarding";
import {ActivityChart} from "./ActivityChart";
import {
    ErrorState,
    LoadingExperience,
    useExperience,
} from "./ExperienceProvider";
import {Insights} from "./Insights";
import {Delta, MetricCard} from "./MetricCard";
import {PeriodControls} from "./PeriodControls";
import {useResource} from "./useResource";
const metrics = [
    {key: "visitors", label: "Visitors across sites", icon: UsersIcon},
    {key: "sessions", label: "Visits", icon: CursorArrowRaysIcon},
    {key: "clicks", label: "Search clicks", icon: MagnifyingGlassIcon},
    {key: "keyEvents", label: "Key events", icon: BoltIcon},
];

export function PortfolioPage({
    insightsOnly = false,
}: {
    insightsOnly?: boolean;
}) {
    const {session, period, comparison, refreshSession} = useExperience();
    const [metric, setMetric] = useState("visitors"),
        [search, setSearch] = useState(""),
        [sort, setSort] = useState("attention"),
        [business, setBusiness] = useState(""),
        [showDefinitions, setShowDefinitions] = useState(false);
    const path =
        "/portfolio?" +
        new URLSearchParams({
            ...period,
            ...(business ? {business_id: business} : {}),
        }).toString();
    const {data, error, loading, reload} = useResource<Portfolio>(path);
    const syncing = data?.sites.some((site) => site.syncing) ?? false;
    // Keep progress automatic without polling settled portfolios.
    useEffect(() => {
        if (!syncing) return;
        const timer = window.setInterval(reload, 10000);
        return () => window.clearInterval(timer);
    }, [syncing, reload]);
    const hasSites = session.businesses.some(
        (item) => item.websites.length > 0,
    );
    if (!hasSites) {
        const workspace = session.businesses.find(
            (item) => item.role !== "viewer",
        );
        return (
            <main className="experience-page onboarding-page">
                {!workspace && session.businesses.length ? (
                    <div className="empty-state">
                        <h1>Your portfolio is waiting</h1>
                        <p>
                            Your workspace administrator can connect Google and
                            add websites.
                        </p>
                    </div>
                ) : (
                    <GoogleOnboarding
                        business={workspace}
                        onComplete={async () => {
                            refreshSession();
                            reload();
                        }}
                    />
                )}
            </main>
        );
    }
    if (!data && loading) return <LoadingExperience />;
    if (!data)
        return (
            <main className="experience-page">
                <ErrorState
                    message={error || "No portfolio data is available."}
                    retry={reload}
                />
            </main>
        );
    const filtered = data.sites
        .filter((site) =>
            (site.domain + " " + site.name)
                .toLowerCase()
                .includes(search.toLowerCase()),
        )
        .sort((a, b) =>
            sort === "name"
                ? a.domain.localeCompare(b.domain)
                : sort === "visitors"
                  ? (number(b.ga4.current?.totalUsers) ?? -1) -
                    (number(a.ga4.current?.totalUsers) ?? -1)
                  : attentionScore(b) - attentionScore(a),
        );
    return (
        <main className="experience-page">
            <div className="page-heading">
                <div>
                    <p className="eyebrow">
                        {insightsOnly ? "SIGNALS, NOT NOISE" : "YOUR PORTFOLIO"}
                    </p>
                    <h1>
                        {insightsOnly
                            ? "Know where to look next."
                            : "Every website. One clear view."}
                    </h1>
                    <p className="page-description">
                        {insightsOnly
                            ? "Measured changes, useful questions and the evidence behind them."
                            : `${data.sites.length} websites. Your traffic, search visibility and meaningful actions, together.`}
                    </p>
                </div>
                <PeriodControls />
            </div>
            {error && <ErrorState message={error} retry={reload} />}
            <div className="portfolio-context">
                <span>
                    <span
                        className={`status-dot ${syncing ? "working" : ""}`}
                    />
                    {syncing
                        ? "Reports are updating in the background"
                        : "Based on your synchronised Google reports"}
                </span>
                <button className="text-link" onClick={reload}>
                    <ArrowPathIcon />
                    Refresh
                </button>
            </div>
            {insightsOnly ? (
                <>
                    <div className="insights-intro">
                        <span className="insight-summary-icon">
                            <BoltIcon />
                        </span>
                        <div>
                            <h2>
                                {data.insights.length} evidence-backed signals
                            </h2>
                            <p>
                                Changes are compared with the previous
                                equal-length period. They suggest an
                                investigation, not a guaranteed explanation.
                            </p>
                        </div>
                    </div>
                    <div className="insights-board">
                        <Insights items={data.insights} period={period} />
                    </div>
                </>
            ) : (
                <>
                    <div className="metric-grid">
                        {metrics.map((item) => {
                            const value = data.metrics[item.key];
                            return (
                                <MetricCard
                                    key={item.key}
                                    label={item.label}
                                    value={value?.current}
                                    delta={value?.change ?? null}
                                    icon={<item.icon />}
                                    selected={metric === item.key}
                                    onClick={() => setMetric(item.key)}
                                    comparison={comparison}
                                    caption={
                                        value && value.covered < value.expected
                                            ? `${value.covered} of ${value.expected} reporting properties covered`
                                            : undefined
                                    }
                                />
                            );
                        })}
                    </div>
                    <div className="portfolio-feature-grid">
                        <section className="activity-card">
                            <div className="report-card-heading">
                                <div>
                                    <h2>Portfolio activity</h2>
                                    <p>
                                        {
                                            metrics.find(
                                                (item) => item.key === metric,
                                            )?.label
                                        }{" "}
                                        over the selected period
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
                                data={data.trend}
                                currentKey={metric}
                                previousKey={"previous_" + metric}
                                label={
                                    metrics.find((item) => item.key === metric)
                                        ?.label
                                }
                                comparison={comparison}
                            />
                            <div className="chart-note">
                                <span>
                                    Daily counts · gaps mean unavailable data
                                </span>
                                <button
                                    className="text-link"
                                    onClick={() =>
                                        setShowDefinitions(!showDefinitions)
                                    }
                                >
                                    How to read these numbers
                                </button>
                            </div>
                            {showDefinitions && (
                                <p className="measurement-note">
                                    {data.notice} A missing or zero previous
                                    period produces no percentage change.
                                </p>
                            )}
                        </section>
                        <aside className="attention-card">
                            <div className="report-card-heading">
                                <div>
                                    <span className="section-kicker">
                                        A LITTLE DIRECTION
                                    </span>
                                    <h2>Worth your attention</h2>
                                </div>
                                <BoltIcon />
                            </div>
                            <Insights
                                items={data.insights.slice(0, 3)}
                                period={period}
                                compact
                            />
                            <Link
                                className="attention-footer"
                                href={
                                    "/dashboard/insights?" +
                                    new URLSearchParams(period)
                                }
                            >
                                See all insights
                                <ArrowRightIcon />
                            </Link>
                        </aside>
                    </div>
                    <section className="portfolio-websites" id="websites">
                        <div className="section-heading">
                            <div>
                                <h2>
                                    Your websites{" "}
                                    <span className="count-badge">
                                        {data.sites.length}
                                    </span>
                                </h2>
                                <p>
                                    A little context for every corner of your
                                    portfolio.
                                </p>
                            </div>
                            <div className="website-tools">
                                <label className="search-field">
                                    <MagnifyingGlassIcon />
                                    <input
                                        aria-label="Find a website"
                                        placeholder="Find a website…"
                                        value={search}
                                        onChange={(event) =>
                                            setSearch(event.target.value)
                                        }
                                    />
                                </label>
                                {session.businesses.length > 1 && (
                                    <select
                                        aria-label="Workspace"
                                        value={business}
                                        onChange={(event) =>
                                            setBusiness(event.target.value)
                                        }
                                    >
                                        <option value="">All workspaces</option>
                                        {session.businesses.map((item) => (
                                            <option
                                                key={item.id}
                                                value={item.id}
                                            >
                                                {item.name}
                                            </option>
                                        ))}
                                    </select>
                                )}
                                <select
                                    aria-label="Sort websites"
                                    value={sort}
                                    onChange={(event) =>
                                        setSort(event.target.value)
                                    }
                                >
                                    <option value="attention">
                                        Attention first
                                    </option>
                                    <option value="visitors">
                                        Most visitors
                                    </option>
                                    <option value="name">Website name</option>
                                </select>
                            </div>
                        </div>
                        {filtered.length ? (
                            <div className="site-grid">
                                {filtered.map((site, index) => (
                                    <SiteCard
                                        key={site.id}
                                        site={site}
                                        index={index}
                                    />
                                ))}
                            </div>
                        ) : (
                            <div className="empty-state">
                                <GlobeAltIcon />
                                <h3>No websites match that search</h3>
                                <p>Try a different name or workspace.</p>
                                <button
                                    className="button"
                                    onClick={() => {
                                        setSearch("");
                                        setBusiness("");
                                    }}
                                >
                                    Clear filters
                                </button>
                            </div>
                        )}
                    </section>
                </>
            )}
            <p className="portfolio-disclaimer">
                Visitors are summed across distinct reporting properties, not
                distinct people. Shared properties are counted once. Search
                clicks and visits are different measurements.
            </p>
        </main>
    );
}

function attentionScore(site: SiteSummary) {
    return site.issues.length
        ? 1000
        : site.syncing
          ? 0
          : Math.max(
                0,
                ...site.insights.map((item) =>
                    item.level === "attention"
                        ? 200 + Math.abs(item.change ?? 0)
                        : item.level === "opportunity"
                          ? 100
                          : 20,
                ),
            );
}
function SiteCard({site, index}: {site: SiteSummary; index: number}) {
    const {period, comparison} = useExperience();
    const visitors = number(site.ga4.current?.totalUsers),
        delta = change(visitors, site.ga4.previous?.totalUsers);
    const status = site.issues.length
        ? "Connection needs attention"
        : site.syncing
          ? "Updating reports"
          : site.insights.some((item) => item.level === "attention")
            ? "Worth a closer look"
            : delta !== null && delta >= 20
              ? "Building momentum"
              : site.ga4.current === null && site.gsc.current === null
                ? "Awaiting reports"
                : "Your website at a glance";
    return (
        <Link
            className={`site-card site-colour-${index % 4}`}
            href={siteHref(site.id, period)}
        >
            <div className="site-card-top">
                <span className="site-avatar">
                    {site.domain
                        .replace(/^www\./, "")
                        .slice(0, 1)
                        .toUpperCase()}
                </span>
                <div>
                    <h3>{site.domain}</h3>
                    <p>
                        {site.providers.includes("ga4") ? "Analytics" : ""}
                        {site.providers.length > 1 ? " + " : ""}
                        {site.providers.includes("gsc") ? "Search Console" : ""}
                    </p>
                </div>
                <ArrowUpRightIcon />
            </div>
            {site.shared_providers?.length > 0 && (
                <p className="scope-note">
                    Shared property · property-wide totals
                </p>
            )}
            <div className="site-card-main">
                <div>
                    <span>Visitors</span>
                    <strong>{compact(visitors)}</strong>
                    <Delta value={delta} comparison={comparison} />
                </div>
                <ActivityChart
                    small
                    comparison={false}
                    data={series(
                        site.trends.ga4.current,
                        site.trends.ga4.previous,
                        "totalUsers",
                        period,
                    )}
                />
            </div>
            <div className="site-card-metrics">
                <div>
                    <span>Visits</span>
                    <b>{compact(site.ga4.current?.sessions)}</b>
                </div>
                <div>
                    <span>Search clicks</span>
                    <b>{compact(site.gsc.current?.clicks)}</b>
                </div>
                <div>
                    <span>Key events</span>
                    <b>{compact(site.ga4.current?.keyEvents)}</b>
                </div>
            </div>
            <div
                className={`site-card-status ${site.issues.length || site.insights.some((item) => item.level === "attention") ? "needs-attention" : ""}`}
            >
                <span className="status-dot" />
                {status}
                <ArrowRightIcon />
            </div>
        </Link>
    );
}

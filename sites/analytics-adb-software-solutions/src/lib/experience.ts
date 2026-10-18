import type {Row, Snapshot} from "../app/client";
export type Pair<T> = {current: T | null; previous: T | null};
export interface Insight {
    id: string;
    website_id: number;
    domain: string;
    title: string;
    detail: string;
    action: string;
    level: "attention" | "positive" | "opportunity";
    report: string;
    metric: string;
    current: number;
    previous: number | null;
    change: number | null;
    dimension: string;
    value: string;
}
export interface SiteSummary {
    id: number;
    business_id: number;
    name: string;
    domain: string;
    timezone: string;
    providers: string[];
    property_ids: Record<string, string>;
    shared_providers: string[];
    ga4: Pair<Row>;
    gsc: Pair<Row>;
    trends: {ga4: Pair<Row[]>; gsc: Pair<Row[]>};
    insights: Insight[];
    syncing: boolean;
    updated_at: string | null;
    issues: string[];
}
export interface Portfolio {
    sites: SiteSummary[];
    metrics: Record<
        string,
        {
            current: number | null;
            previous: number | null;
            change: number | null;
            covered: number;
            expected: number;
        }
    >;
    trend: Row[];
    insights: Insight[];
    start: string;
    end: string;
    notice: string;
}
export interface DashboardData {
    site: SiteSummary;
    parameters: {parameterName: string; displayName: string}[];
    reports: Record<string, Record<string, Pair<Snapshot & {total: number}>>>;
    insights: Insight[];
    start: string;
    end: string;
}
export type Period = {start: string; end: string};
export function number(value: unknown): number | null {
    return typeof value === "number" && Number.isFinite(value) ? value : null;
}
export function compact(value: unknown, metric = ""): string {
    const n = number(value);
    if (n === null) return "—";
    if (["engagementRate", "ctr"].includes(metric))
        return new Intl.NumberFormat("en-GB", {
            style: "percent",
            maximumFractionDigits: 1,
        }).format(n);
    if (metric === "averageEngagementTime") return `${Math.round(n)}s`;
    return new Intl.NumberFormat("en-GB", {
        notation: Math.abs(n) >= 100000 ? "compact" : "standard",
        maximumFractionDigits: metric === "position" ? 1 : 0,
    }).format(n);
}
export function change(current: unknown, previous: unknown): number | null {
    const a = number(current),
        b = number(previous);
    return a === null || b === null || b === 0 ? null : ((a - b) / b) * 100;
}
export function siteHref(id: number, period?: Period, section = ""): string {
    return `/dashboard/websites/${id}${section}${period ? `?${new URLSearchParams(period).toString()}` : ""}`;
}
export function exploreHref(
    id: number,
    report: string,
    period: Period,
    value = "",
): string {
    return (
        siteHref(id, undefined, "/explore") +
        "?" +
        new URLSearchParams({
            ...period,
            report,
            ...(value ? {value} : {}),
        }).toString()
    );
}
export function series(
    current: Row[] | null,
    previous: Row[] | null,
    metric: string,
    period: Period,
): Row[] {
    const start = Date.parse(period.start + "T00:00:00Z"),
        end = Date.parse(period.end + "T00:00:00Z");
    const length = Math.round((end - start) / 86400000) + 1;
    const normalize = (value: unknown) => String(value ?? "").replace(/-/g, "");
    const now = new Map(
        (current ?? []).map((row) => [normalize(row.date), row]),
    );
    const before = new Map(
        (previous ?? []).map((row) => [normalize(row.date), row]),
    );
    return Array.from(
        {length: Math.min(Math.max(length, 0), 366)},
        (_, index) => {
            const date = new Date(start + index * 86400000)
                .toISOString()
                .slice(0, 10);
            const prior = new Date(start + (index - length) * 86400000)
                .toISOString()
                .slice(0, 10);
            return {
                date,
                previous_date: prior,
                value: number(now.get(normalize(date))?.[metric]),
                previous: number(before.get(normalize(prior))?.[metric]),
            };
        },
    );
}

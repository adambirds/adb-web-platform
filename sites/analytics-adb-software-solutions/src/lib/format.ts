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

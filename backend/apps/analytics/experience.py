"""Snapshot-only portfolio and dashboard views with explicit coverage and evidence."""

from collections import Counter, defaultdict
from datetime import date, timedelta
from itertools import pairwise
from typing import Any

from django.db.models import Q

from apps.analytics.models import Business, ProviderProperty, ReportSnapshot, SyncJob, Website
from apps.analytics.reports import derive_metrics
from apps.analytics.services import previous_window

DASHBOARD_REPORTS = {
    "ga4": [
        "overview",
        "trend",
        "acquisition",
        "pages",
        "landing",
        "events",
        "devices",
        "browsers",
        "countries",
    ],
    "gsc": ["overview", "trend", "queries", "pages", "countries", "devices"],
}
METRICS = {
    "visitors": ("ga4", "totalUsers"),
    "sessions": ("ga4", "sessions"),
    "clicks": ("gsc", "clicks"),
    "keyEvents": ("ga4", "keyEvents"),
}


def percent_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None or previous == 0:
        return None
    return round((current - previous) / previous * 100, 1)


def load_snapshots(
    websites: Any, start: date, end: date, *, detailed: bool = False
) -> dict[tuple[int, str, str, str], ReportSnapshot]:
    previous_start, previous_end = previous_window(start, end)
    reports = (
        {name for names in DASHBOARD_REPORTS.values() for name in names}
        if detailed
        else {"overview", "trend", "queries", "acquisition"}
    )
    queryset = (
        ReportSnapshot.objects.filter(property__website__in=websites, report__in=reports)
        .filter(Q(start=start, end=end) | Q(start=previous_start, end=previous_end))
        .select_related("property")
    )
    return {
        (
            item.property.website_id,
            item.property.provider,
            item.report,
            "current" if item.start == start else "previous",
        ): item
        for item in queryset
    }


def rows(stored: ReportSnapshot | None) -> list[dict[str, Any]] | None:
    return [derive_metrics(row) for row in stored.payload.get("rows", [])] if stored else None


def overview(stored: ReportSnapshot | None) -> dict[str, Any] | None:
    if stored and not stored.payload.get("complete", True):
        return None
    data = rows(stored)
    return data[0] if data else ({} if stored else None)


def group_acquisition(values: list[dict[str, Any]], dimension: str) -> list[dict[str, Any]]:
    grouped_rows: dict[str, dict[str, Any]] = {}
    for row in values:
        label = str(row.get(dimension, "(not set)"))
        grouped = grouped_rows.setdefault(label, {dimension: label})
        for metric in ("sessions", "engagedSessions", "keyEvents"):
            if metric in row:
                grouped[metric] = grouped.get(metric, 0) + row[metric]
    return [derive_metrics(row) for row in grouped_rows.values()]


def evidence_insights(
    website: Website, reports: dict[tuple[int, str, str, str], ReportSnapshot]
) -> list[dict[str, Any]]:
    insights: list[dict[str, Any]] = []

    def get(provider: str, report: str, period: str) -> list[dict[str, Any]] | None:
        stored = reports.get((website.pk, provider, report, period))
        if stored and (
            not stored.payload.get("complete", True)
            or stored.payload.get("metadata", {}).get("subjectToThresholding")
        ):
            return None
        return rows(stored)

    def add(
        key: str,
        title: str,
        detail: str,
        action: str,
        level: str,
        report: str,
        metric: str,
        current: float,
        previous: float | None,
        *,
        dimension: str = "",
        value: str = "",
    ) -> None:
        insights.append(
            {
                "id": f"{website.pk}:{key}",
                "website_id": website.pk,
                "domain": website.domain,
                "title": title,
                "detail": detail,
                "action": action,
                "level": level,
                "report": report,
                "metric": metric,
                "current": current,
                "previous": previous,
                "change": percent_change(current, previous),
                "dimension": dimension,
                "value": value,
            }
        )

    for provider, metric, minimum, threshold, label, report in [
        ("ga4", "totalUsers", 100, 20, "Visitors", "acquisition"),
        ("ga4", "keyEvents", 10, 25, "Key events", "events"),
        ("gsc", "clicks", 30, 25, "Search clicks", "queries"),
    ]:
        now, before = get(provider, "overview", "current"), get(provider, "overview", "previous")
        if not now or not before:
            continue
        current, previous = now[0].get(metric), before[0].get(metric)
        if current is None or previous is None or previous < minimum:
            continue
        change = percent_change(current, previous)
        if change is not None and abs(change) >= threshold and abs(current - previous) >= 5:
            direction = "up" if change > 0 else "down"
            add(
                metric,
                f"{label} are {direction} {abs(change):g}%",
                f"{current:,.0f} this period versus {previous:,.0f} in the equally long previous period. This is a measured change, not a diagnosis of its cause.",
                "Inspect sources and landing pages"
                if report == "acquisition"
                else "Review the underlying report",
                "positive" if change > 0 else "attention",
                report,
                metric,
                current,
                previous,
            )

    # Only compare rows present in both windows; missing/privacy-filtered rows are not zeros.
    current_sources, previous_sources = (
        get("ga4", "acquisition", "current"),
        get("ga4", "acquisition", "previous"),
    )
    if current_sources is not None and previous_sources is not None:
        old = {
            str(row.get("sessionSourceMedium")): row
            for row in group_acquisition(previous_sources, "sessionSourceMedium")
        }
        changes = []
        for row in group_acquisition(current_sources, "sessionSourceMedium"):
            previous = old.get(str(row.get("sessionSourceMedium")))
            if (
                previous
                and previous.get("sessions", 0) >= 30
                and abs(row.get("sessions", 0) - previous["sessions"]) >= 25
            ):
                changes.append((row, previous))
        if changes:
            row, prior_source = max(
                changes, key=lambda pair: abs(pair[0].get("sessions", 0) - pair[1]["sessions"])
            )
            current, previous = row.get("sessions", 0), prior_source["sessions"]
            source = str(row.get("sessionSourceMedium", "Unknown source"))
            add(
                "source",
                f"A shift in {source}",
                f"Sessions changed from {previous:,.0f} to {current:,.0f}. This identifies a source to investigate; it does not establish why traffic changed.",
                "Inspect this source and campaign mix",
                "attention" if current < previous else "positive",
                "acquisition",
                "sessions",
                current,
                previous,
                dimension="sessionSourceMedium",
                value=source,
            )

    queries = get("gsc", "queries", "current")
    if queries:
        candidates = [
            row
            for row in queries
            if row.get("impressions", 0) >= 100
            and 0 < row.get("ctr", 0) < 0.02
            and 4 <= row.get("position", 0) <= 20
        ]
        if candidates:
            row = max(candidates, key=lambda item: item["impressions"])
            query = str(row.get("query", ""))
            add(
                "search-opportunity",
                "Visibility without many clicks",
                f"“{query}” earned {row['impressions']:,.0f} impressions with {row['ctr']:.1%} CTR at average position {row['position']:.1f}. Low CTR can have several causes; compare the result title, intent and ranking before changing content.",
                "Investigate this search query",
                "opportunity",
                "queries",
                "impressions",
                row["impressions"],
                None,
                dimension="query",
                value=query,
            )

    trend = get("ga4", "trend", "current")
    if trend and len(trend) >= 8:
        ordered = sorted(trend, key=lambda row: str(row.get("date", "")))
        # Require consecutive calendar days, not eight arbitrary sparse points.
        tail = ordered[-8:]
        try:
            dates = [
                date.fromisoformat(
                    str(row["date"])[:4] + "-" + str(row["date"])[4:6] + "-" + str(row["date"])[6:8]
                )
                for row in tail
            ]
            consecutive = all((b - a).days == 1 for a, b in pairwise(dates))
        except (KeyError, ValueError):
            consecutive = False
        values = [
            float(row["totalUsers"])
            for row in tail
            if isinstance(row.get("totalUsers"), (int, float))
        ]
        if consecutive and len(values) == 8:
            baseline = sum(values[:-1]) / 7
            latest = values[-1]
            if baseline >= 30 and latest < baseline * 0.5:
                add(
                    "daily-dip",
                    "The latest day needs a closer look",
                    f"{latest:,.0f} visitors on {dates[-1].isoformat()} versus a {baseline:,.0f} daily average in the preceding seven days. Check collection and source mix; this comparison is not seasonally adjusted.",
                    "Explore daily visitor data",
                    "attention",
                    "overview",
                    "totalUsers",
                    latest,
                    baseline,
                )
    return insights


def site_summary(
    website: Website,
    reports: dict[tuple[int, str, str, str], ReportSnapshot],
    active_jobs: set[int],
) -> dict[str, Any]:
    props = list(website.provider_properties.all())
    synced = [prop.last_synced_at for prop in props if prop.last_synced_at]
    return {
        "id": website.pk,
        "business_id": website.business_id,
        "name": website.name,
        "domain": website.domain,
        "timezone": website.timezone,
        "providers": [prop.provider for prop in props],
        "property_ids": {prop.provider: prop.external_id for prop in props},
        "shared_providers": [],
        "ga4": {
            period: overview(reports.get((website.pk, "ga4", "overview", period)))
            for period in ("current", "previous")
        },
        "gsc": {
            period: overview(reports.get((website.pk, "gsc", "overview", period)))
            for period in ("current", "previous")
        },
        "trends": {
            provider: {
                period: rows(reports.get((website.pk, provider, "trend", period)))
                for period in ("current", "previous")
            }
            for provider in ("ga4", "gsc")
        },
        "insights": evidence_insights(website, reports),
        "syncing": website.pk in active_jobs,
        "updated_at": min(synced).isoformat() if synced else None,
        "issues": sorted(
            {
                prop.error_code or prop.connection.error_code
                for prop in props
                if prop.error_code or prop.connection.error_code
            }
        ),
    }


def portfolio(user: Any, start: date, end: date, business_id: int | None = None) -> dict[str, Any]:
    businesses = Business.objects.filter(memberships__user=user)
    if business_id is not None:
        businesses = businesses.filter(pk=business_id)
    permitted = [
        business.pk for business in businesses if user.has_perm("analytics.view_report", business)
    ]
    websites = (
        Website.objects.filter(business_id__in=permitted, is_active=True)
        .prefetch_related("provider_properties__connection")
        .order_by("domain")
    )
    reports = load_snapshots(websites, start, end)
    active = set(
        SyncJob.objects.filter(
            property__website__in=websites, status__in=["queued", "running", "retrying"]
        ).values_list("property__website_id", flat=True)
    )
    sites = [site_summary(website, reports, active) for website in websites]
    counts = Counter(
        (provider, identifier)
        for site in sites
        for provider, identifier in site["property_ids"].items()
    )
    for site in sites:
        site["shared_providers"] = [
            provider
            for provider, identifier in site["property_ids"].items()
            if counts[(provider, identifier)] > 1
        ]
    unique: dict[str, list[dict[str, Any]]] = {}
    for provider in ("ga4", "gsc"):
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for site in sites:
            if provider in site["property_ids"]:
                grouped[site["property_ids"][provider]].append(site)
        unique[provider] = [
            max(
                group,
                key=lambda site: (site[provider]["current"] is not None, site["updated_at"] or ""),
            )
            for group in grouped.values()
        ]
    metrics = {}
    for key, (provider, metric) in METRICS.items():
        eligible = unique[provider]
        current = [
            site[provider]["current"].get(metric)
            for site in eligible
            if site[provider]["current"] is not None
            and site[provider]["current"].get(metric) is not None
        ]
        previous = [
            site[provider]["previous"].get(metric)
            for site in eligible
            if site[provider]["current"] is not None
            and site[provider]["current"].get(metric) is not None
            and site[provider]["previous"] is not None
            and site[provider]["previous"].get(metric) is not None
        ]
        current_total = sum(current) if current else None
        previous_total = sum(previous) if previous and len(previous) == len(current) else None
        metrics[key] = {
            "current": current_total,
            "previous": previous_total,
            "change": percent_change(current_total, previous_total),
            "covered": len(current),
            "expected": len(eligible),
        }
    previous_start, _ = previous_window(start, end)
    points: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for key, (provider, metric) in METRICS.items():
        for site in unique[provider]:
            for period in ("current", "previous"):
                for row in site["trends"][provider][period] or []:
                    if row.get(metric) is not None:
                        points[(key, period, str(row.get("date", "")).replace("-", ""))].append(
                            row[metric]
                        )
    trend = []
    for offset in range((end - start).days + 1):
        current_day, previous_day = (
            start + timedelta(days=offset),
            previous_start + timedelta(days=offset),
        )
        point: dict[str, Any] = {
            "date": current_day.isoformat(),
            "previous_date": previous_day.isoformat(),
        }
        for key in METRICS:
            for period, day in (("current", current_day), ("previous", previous_day)):
                values = points[(key, period, day.strftime("%Y%m%d"))]
                point[key if period == "current" else "previous_" + key] = (
                    sum(values) if values else None
                )
        trend.append(point)
    return {
        "sites": sites,
        "metrics": metrics,
        "trend": trend,
        "insights": sorted(
            [insight for site in sites for insight in site["insights"]],
            key=lambda item: (item["level"] != "attention", -abs(item["change"] or 0)),
        ),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "notice": "Visitors are summed across distinct reporting properties, not deduplicated people. Shared properties are counted once; linked website cards can show property-wide data. Daily visitor values must not be added to obtain period visitors. Dates follow each website timezone; Search Console uses Pacific Time. Missing snapshots are excluded and coverage is shown.",
    }


def dashboard(website: Website, start: date, end: date) -> dict[str, Any]:
    reports = load_snapshots(Website.objects.filter(pk=website.pk), start, end, detailed=True)
    active = set(
        SyncJob.objects.filter(
            property__website=website, status__in=["queued", "running", "retrying"]
        ).values_list("property__website_id", flat=True)
    )
    data: dict[str, Any] = {}
    for provider, names in DASHBOARD_REPORTS.items():
        data[provider] = {}
        for name in names:
            pair = {}
            for period in ("current", "previous"):
                stored = reports.get((website.pk, provider, name, period))
                values = rows(stored)
                pair[period] = (
                    {
                        "rows": values
                        if name == "trend"
                        else sorted(
                            values,
                            key=lambda row: row.get(
                                "eventCount"
                                if name == "events"
                                else "clicks"
                                if provider == "gsc"
                                else "activeUsers"
                                if name in {"devices", "countries", "browsers"}
                                else "sessions",
                                0,
                            ),
                            reverse=True,
                        )[:12],
                        "total": len(values),
                        "complete": stored.payload.get("complete", True),
                        "updated_at": stored.updated_at.isoformat(),
                        "limitations": stored.payload.get("limitations", ""),
                    }
                    if stored is not None and values is not None
                    else None
                )
            data[provider][name] = pair
    for name, dimension in (
        ("channels", "sessionDefaultChannelGroup"),
        ("referrals", "sessionSourceMedium"),
    ):
        data["ga4"][name] = {}
        for period in ("current", "previous"):
            stored = reports.get((website.pk, "ga4", "acquisition", period))
            if stored is None:
                data["ga4"][name][period] = None
                continue
            grouped_values = group_acquisition(stored.payload.get("rows", []), dimension)
            data["ga4"][name][period] = {
                "rows": sorted(
                    grouped_values, key=lambda row: row.get("sessions", 0), reverse=True
                )[:12],
                "total": len(grouped_values),
                "complete": stored.payload.get("complete", True),
                "updated_at": stored.updated_at.isoformat(),
            }
    site = site_summary(website, reports, active)
    site["shared_providers"] = [
        prop.provider
        for prop in website.provider_properties.all()
        if ProviderProperty.objects.filter(
            website__business=website.business, provider=prop.provider, external_id=prop.external_id
        )
        .exclude(website=website)
        .exists()
    ]
    parameters = [
        {
            "parameterName": definition.payload.get("parameterName", ""),
            "displayName": definition.payload.get("displayName", ""),
        }
        for prop in website.provider_properties.all()
        if prop.provider == "ga4"
        for definition in prop.definitions.filter(kind="dimensions", payload__scope="EVENT")
    ]
    return {
        "site": site,
        "parameters": parameters,
        "reports": data,
        "insights": evidence_insights(website, reports),
        "start": start.isoformat(),
        "end": end.isoformat(),
    }

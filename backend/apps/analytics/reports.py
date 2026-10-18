"""Provider report contracts and deterministic opportunities from aggregate data."""

from datetime import date
from typing import Any
from urllib.parse import quote

from apps.analytics.google import DATA_URL, SEARCH_URL, ProviderError, google_request
from apps.analytics.models import ProviderProperty

GA_METRICS = [
    "totalUsers",
    "activeUsers",
    "newUsers",
    "sessions",
    "screenPageViews",
    "engagedSessions",
    "userEngagementDuration",
    "keyEvents",
    "eventCount",
]
GA_REPORTS = {
    "overview": ([], GA_METRICS),
    "trend": (["date"], GA_METRICS),
    "pages": (
        ["pageLocation", "pagePathPlusQueryString", "hostName"],
        [
            "screenPageViews",
            "sessions",
            "engagedSessions",
            "activeUsers",
            "userEngagementDuration",
            "keyEvents",
        ],
    ),
    "page_trend": (
        ["date", "pageLocation"],
        ["sessions", "screenPageViews", "activeUsers", "userEngagementDuration", "keyEvents"],
    ),
    "page_events": (["pageLocation", "eventName"], ["eventCount", "keyEvents"]),
    "acquisition": (
        ["sessionDefaultChannelGroup", "sessionSourceMedium", "sessionCampaignName"],
        ["sessions", "engagedSessions", "keyEvents"],
    ),
    "landing": (["landingPagePlusQueryString"], ["sessions", "engagedSessions", "keyEvents"]),
    "devices": (["deviceCategory"], ["activeUsers", "sessions", "engagedSessions"]),
    "browsers": (["browser"], ["activeUsers", "sessions", "engagedSessions"]),
    "countries": (["country"], ["activeUsers", "sessions", "engagedSessions"]),
    "events": (["eventName"], ["eventCount", "totalUsers", "keyEvents"]),
    "event_trend": (["date", "eventName"], ["eventCount", "totalUsers", "keyEvents"]),
}
GSC_REPORTS = {
    "overview": [],
    "trend": ["date"],
    "queries": ["query"],
    "pages": ["page"],
    "countries": ["country"],
    "devices": ["device"],
    "page_trend": ["date", "page"],
}
PAGE_SIZE = 25000
MAX_PAGES = 4


def parse_ga(result: dict[str, Any]) -> list[dict[str, Any]]:
    dimensions = [h["name"] for h in result.get("dimensionHeaders", [])]
    metrics = [h["name"] for h in result.get("metricHeaders", [])]
    return [
        {
            **dict(
                zip(dimensions, (v["value"] for v in row.get("dimensionValues", [])), strict=True)
            ),
            **dict(
                zip(metrics, (float(v["value"]) for v in row.get("metricValues", [])), strict=True)
            ),
        }
        for row in result.get("rows", [])
    ]


def ga_report(
    prop: ProviderProperty,
    report: str,
    start: date,
    end: date,
    *,
    event: str = "",
    parameter: str = "",
) -> dict[str, Any]:
    dimensions, metrics = GA_REPORTS[report]
    dimensions = list(dimensions)
    if parameter:
        dimensions.append(parameter)
    body: dict[str, Any] = {
        "dimensions": [{"name": d} for d in dimensions],
        "metrics": [{"name": m} for m in metrics],
        "dateRanges": [{"startDate": start.isoformat(), "endDate": end.isoformat()}],
        "limit": PAGE_SIZE,
        "returnPropertyQuota": True,
    }
    if event:
        body["dimensionFilter"] = {
            "filter": {
                "fieldName": "eventName",
                "stringFilter": {"matchType": "EXACT", "value": event},
            }
        }
    rows: list[dict[str, Any]] = []
    result: dict[str, Any] = {}
    complete = False
    for page in range(MAX_PAGES):
        result = google_request(
            prop.connection,
            "POST",
            DATA_URL + prop.external_id + ":runReport",
            body={**body, "offset": page * PAGE_SIZE},
        )
        rows.extend(parse_ga(result))
        if len(rows) >= int(result.get("rowCount", 0)):
            complete = True
            break
    return {
        "rows": rows,
        "complete": complete,
        "metadata": result.get("metadata", {}),
        "quota": result.get("propertyQuota", {}),
        "measurement": "GA4 property timezone",
        "start": str(start),
        "end": str(end),
    }


def gsc_report(
    prop: ProviderProperty, report: str, start: date, end: date, *, search_type: str = "web"
) -> dict[str, Any]:
    if search_type not in {"web", "image", "video", "news", "discover", "googleNews"}:
        raise ProviderError("unsupported_search_type")
    dimensions = GSC_REPORTS[report]
    rows: list[dict[str, Any]] = []
    complete = False
    for page in range(MAX_PAGES):
        result = google_request(
            prop.connection,
            "POST",
            SEARCH_URL + "sites/" + quote(prop.external_id, safe="") + "/searchAnalytics/query",
            body={
                "startDate": str(start),
                "endDate": str(end),
                "dimensions": dimensions,
                "type": search_type,
                "dataState": "final",
                "rowLimit": PAGE_SIZE,
                "startRow": page * PAGE_SIZE,
            },
        )
        batch = result.get("rows", [])
        rows.extend(
            {
                **dict(zip(dimensions, row.get("keys", []), strict=True)),
                **{key: row[key] for key in ("clicks", "impressions", "ctr", "position")},
            }
            for row in batch
        )
        if len(batch) < PAGE_SIZE:
            complete = True
            break
    return {
        "rows": rows,
        "complete": complete,
        "measurement": "Search Console Pacific Time; final data only",
        "search_type": search_type,
        "start": str(start),
        "end": str(end),
        "limitations": "Top rows only; anonymised queries and canonical URLs can make breakdown totals differ from overview. Search clicks are distinct from GA4 sessions.",
    }


def realtime(prop: ProviderProperty) -> dict[str, Any]:
    result = google_request(
        prop.connection,
        "POST",
        DATA_URL + prop.external_id + ":runRealtimeReport",
        body={
            "dimensions": [{"name": "eventName"}, {"name": "country"}, {"name": "deviceCategory"}],
            "metrics": [{"name": "eventCount"}],
            "limit": 1000,
        },
    )
    totals = google_request(
        prop.connection,
        "POST",
        DATA_URL + prop.external_id + ":runRealtimeReport",
        body={"metrics": [{"name": "activeUsers"}, {"name": "eventCount"}]},
    )
    return {
        "rows": parse_ga(result),
        "totals": parse_ga(totals),
        "window": "Last 30 minutes",
        "limitations": "Breakdown rows show event counts by event, country and device. Active users are shown only in the overall total because Google does not support activeUsers with eventName. Page paths are not available in this realtime report.",
    }


def derive_metrics(row: dict[str, Any]) -> dict[str, Any]:
    values = dict(row)
    sessions = float(row.get("sessions", 0))
    users = float(row.get("activeUsers", 0))
    if "engagedSessions" in row:
        values["engagementRate"] = float(row["engagedSessions"]) / sessions if sessions else None
    if "userEngagementDuration" in row:
        values["averageEngagementTime"] = (
            float(row["userEngagementDuration"]) / users if users else None
        )
    return values


def opportunities(
    current: list[dict[str, Any]], previous: list[dict[str, Any]], dimension: str
) -> list[dict[str, Any]]:
    old = {r[dimension]: r for r in previous}
    insights = []
    for row in current:
        if row["impressions"] < 100:
            continue
        reasons = []
        prior = old.get(row[dimension])
        if row["ctr"] < 0.02 and row["position"] < 20:
            reasons.append(
                "High impressions with low CTR: review the search title and description."
            )
        if 8 <= row["position"] <= 20:
            reasons.append("Near page one: review content relevance and internal links.")
        if prior and prior["impressions"] >= 100:
            if prior["clicks"] >= 10 and row["clicks"] < prior["clicks"] * 0.8:
                reasons.append("Clicks declined by more than 20%.")
            if row["impressions"] > prior["impressions"] * 1.2:
                reasons.append("Search visibility grew by more than 20%.")
            if row["position"] > prior["position"] + 2:
                reasons.append("Average ranking fell by more than two positions.")
            if prior["ctr"] > 0 and row["ctr"] < prior["ctr"] * 0.8:
                reasons.append("CTR declined by more than 20%.")
        if reasons:
            insights.append(
                {"subject": row[dimension], "reasons": reasons, "heuristic": True, "metrics": row}
            )
    return sorted(insights, key=lambda item: item["metrics"]["impressions"], reverse=True)

"use client";
import {useEffect, useRef, useState} from "react";
import Link from "next/link";
import {ArrowUpRightIcon, XMarkIcon} from "@heroicons/react/24/outline";
import type {Row, Website} from "../../app/client";
import {
    compact,
    exploreHref,
    type DashboardData,
    type Period,
} from "../../lib/experience";
import {titleCase} from "../../lib/format";
import {ActivityChart} from "./ActivityChart";
import {RankedList} from "./RankedList";
import {useResource} from "./useResource";
export type Selection = {
    type: "page" | "event" | "source" | "query" | "audience" | "day";
    label: string;
    row: Row;
    report: string;
};
type PageData = {
    rows: {
        url: string;
        ga4?: Row;
        gsc?: Row;
        ga4_page_trend?: Row[];
        gsc_page_trend?: Row[];
        ga4_page_events?: Row[];
    }[];
    notice: string;
};
export function DetailDrawer({
    selection,
    website,
    data,
    period,
    onClose,
}: {
    selection: Selection;
    website: Website;
    data: DashboardData;
    period: Period;
    onClose: () => void;
}) {
    const dialog = useRef<HTMLDialogElement>(null);
    const [parameter, setParameter] = useState("");
    useEffect(() => {
        const element = dialog.current;
        if (!element) return;
        if (element.showModal) element.showModal();
        else element.setAttribute("open", "");
        return () => {
            if (element.open) element.close?.();
        };
    }, []);
    const path =
        selection.type === "page"
            ? `/websites/${website.id}/combined?${new URLSearchParams({...period, page: selection.label})}`
            : selection.type === "event"
              ? `/websites/${website.id}/events/${encodeURIComponent(selection.label)}/trend?${new URLSearchParams(period)}`
              : null;
    const pageDetail = useResource<PageData>(
        selection.type === "page" ? path : null,
    );
    const eventDetail = useResource<{rows: Row[]; available: boolean}>(
        selection.type === "event" ? path : null,
    );
    const {error, loading} =
        selection.type === "page" ? pageDetail : eventDetail;
    const property = useResource<{rows: Row[]}>(
        parameter
            ? `/websites/${website.id}/events/${encodeURIComponent(selection.label)}/parameters?${new URLSearchParams({...period, parameter})}`
            : null,
    );
    const parameters = data.parameters;
    return (
        <dialog
            className="detail-drawer"
            ref={dialog}
            aria-labelledby="detail-title"
            onCancel={(event) => {
                event.preventDefault();
                onClose();
            }}
            onClick={(event) => {
                if (event.target === event.currentTarget) onClose();
            }}
        >
            <div className="drawer-inner">
                <div className="drawer-heading">
                    <div>
                        <p className="eyebrow">
                            {selection.type === "day"
                                ? "DAILY EVIDENCE"
                                : `${selection.type.toUpperCase()} EXPLORER`}
                        </p>
                        <h2 id="detail-title">{selection.label}</h2>
                    </div>
                    <button
                        className="icon-button"
                        onClick={onClose}
                        aria-label="Close detail"
                    >
                        <XMarkIcon />
                    </button>
                </div>
                <div className="detail-metrics">
                    {Object.entries(selection.row)
                        .filter(
                            ([key, value]) =>
                                typeof value === "number" &&
                                ![
                                    "engagedSessions",
                                    "userEngagementDuration",
                                ].includes(key),
                        )
                        .map(([key, value]) => (
                            <div key={key}>
                                <span>{titleCase(key)}</span>
                                <strong>{compact(value, key)}</strong>
                            </div>
                        ))}
                </div>
                {loading && path && (
                    <p role="status" className="data-notice">
                        Loading the underlying evidence…
                    </p>
                )}
                {error && (
                    <p role="alert" className="data-notice warning">
                        {error}
                    </p>
                )}
                {selection.type === "event" && eventDetail.data && (
                    <>
                        <h3>When this event happened</h3>
                        <ActivityChart
                            data={eventDetail.data.rows.map((row) => ({
                                ...row,
                                date: String(row.date).replace(
                                    /^(\d{4})(\d{2})(\d{2})$/,
                                    "$1-$2-$3",
                                ),
                                value: row.eventCount,
                            }))}
                            label="Events"
                            comparison={false}
                        />
                        <div className="event-properties">
                            <h3>Explore event properties</h3>
                            <p>
                                Break down this event using registered,
                                reportable GA4 parameters. Registration is not
                                retroactive.
                            </p>
                            {parameters.length ? (
                                <label>
                                    Event parameter
                                    <select
                                        aria-label="Event parameter"
                                        value={parameter}
                                        onChange={(event) =>
                                            setParameter(event.target.value)
                                        }
                                    >
                                        <option value="">
                                            Choose a parameter
                                        </option>
                                        {parameters.map((item) => (
                                            <option
                                                key={item.parameterName}
                                                value={item.parameterName}
                                            >
                                                {item.displayName ||
                                                    item.parameterName}
                                            </option>
                                        ))}
                                    </select>
                                </label>
                            ) : (
                                <p className="data-notice">
                                    No event-scoped parameters are registered in
                                    the stored definitions. Refresh definitions
                                    or register a parameter in website
                                    administration.
                                </p>
                            )}
                            {property.loading && parameter && (
                                <p role="status">Loading parameter values…</p>
                            )}
                            {property.error && (
                                <p role="alert">{property.error}</p>
                            )}
                            {property.data && (
                                <RankedList
                                    title={parameter}
                                    metric="Events"
                                    items={property.data.rows.map((row) => ({
                                        label: String(
                                            row["customEvent:" + parameter] ??
                                                "(not set)",
                                        ),
                                        value:
                                            typeof row.eventCount === "number"
                                                ? row.eventCount
                                                : null,
                                    }))}
                                />
                            )}
                        </div>
                    </>
                )}
                {selection.type === "page" &&
                    pageDetail.data &&
                    pageDetail.data.rows.map((row) => (
                        <section className="page-evidence" key={row.url}>
                            <h3>Traffic & search, side by side</h3>
                            <p>
                                Exact URL matches only. These are independent
                                measurements, not a joined visitor journey.
                            </p>
                            <div className="page-provider-grid">
                                {(
                                    [
                                        ["Analytics", row.ga4],
                                        ["Search Console", row.gsc],
                                    ] as const
                                ).map(([label, values]) => (
                                    <div key={label}>
                                        <h4>{label}</h4>
                                        {values ? (
                                            <div className="detail-metrics">
                                                {Object.entries(values)
                                                    .filter(
                                                        ([, value]) =>
                                                            typeof value ===
                                                            "number",
                                                    )
                                                    .slice(0, 6)
                                                    .map(([key, value]) => (
                                                        <div key={key}>
                                                            <span>
                                                                {titleCase(key)}
                                                            </span>
                                                            <strong>
                                                                {compact(
                                                                    value,
                                                                    key,
                                                                )}
                                                            </strong>
                                                        </div>
                                                    ))}
                                            </div>
                                        ) : (
                                            <p>
                                                No matching stored page report.
                                            </p>
                                        )}
                                    </div>
                                ))}
                            </div>
                            {row.ga4_page_trend && (
                                <ActivityChart
                                    data={row.ga4_page_trend.map((point) => ({
                                        ...point,
                                        date: String(point.date).replace(
                                            /^(\d{4})(\d{2})(\d{2})$/,
                                            "$1-$2-$3",
                                        ),
                                        value: point.sessions,
                                    }))}
                                    label="Page visits"
                                    comparison={false}
                                />
                            )}
                            <RankedList
                                title="Events on this page"
                                metric="Events"
                                items={(row.ga4_page_events ?? [])
                                    .slice(0, 8)
                                    .map((event) => ({
                                        label: String(event.eventName),
                                        value:
                                            typeof event.eventCount === "number"
                                                ? event.eventCount
                                                : null,
                                        href: exploreHref(
                                            website.id,
                                            "events",
                                            period,
                                            String(event.eventName),
                                        ),
                                    }))}
                            />
                        </section>
                    ))}
                {["source", "query", "audience"].includes(selection.type) && (
                    <div className="evidence-explanation">
                        <h3>Follow the evidence</h3>
                        <p>
                            These metrics describe this report row for the
                            selected period. The main dashboard remains
                            unfiltered; they do not imply a cross-provider or
                            person-level relationship.
                        </p>
                        <p>
                            {selection.type === "query"
                                ? "Compare impressions, click rate and average position before deciding whether to revise content or search snippets."
                                : selection.type === "source"
                                  ? "Compare source and campaign mix in the full acquisition report. A traffic shift alone does not explain its cause."
                                  : "Explore the complete audience report to compare this breakdown with other visitors."}
                        </p>
                    </div>
                )}
                <Link
                    className="button primary drawer-explore"
                    href={exploreHref(
                        website.id,
                        selection.type === "page"
                            ? "pages"
                            : selection.report === "channels" ||
                                selection.report === "referrals"
                              ? "acquisition"
                              : selection.report,
                        selection.type === "day"
                            ? {start: selection.label, end: selection.label}
                            : period,
                        selection.type === "day" ? "" : selection.label,
                    )}
                >
                    Investigate in explorer
                    <ArrowUpRightIcon />
                </Link>
            </div>
        </dialog>
    );
}

"use client";
import {useEffect, useState} from "react";
import {api, type Row, type Website} from "../../app/client";
import {DataTable} from "./ReportTable";
import {Trend} from "../experience/ActivityChart";
export function CombinedPage({
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

export function EventTrend({
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

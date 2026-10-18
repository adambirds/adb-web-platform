"use client";
import {useId, useState} from "react";
import {
    Area,
    AreaChart,
    CartesianGrid,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";
import type {Row} from "../../app/client";
import {titleCase} from "../../lib/format";
import {compact} from "../../lib/experience";

export function ActivityChart({
    data,
    currentKey = "value",
    previousKey = "previous",
    label = "Visitors",
    comparison = true,
    small = false,
    onDay,
}: {
    data: Row[];
    currentKey?: string;
    previousKey?: string;
    label?: string;
    comparison?: boolean;
    small?: boolean;
    onDay?: (date: string) => void;
}) {
    const id = useId().replace(/:/g, "");
    const [day, setDay] = useState("");
    if (!data.some((row) => typeof row[currentKey] === "number"))
        return small ? (
            <div className="sparkline sparkline-empty">No trend yet</div>
        ) : (
            <div className="chart-empty">
                <span>No trend data for this period</span>
                <small>
                    Synchronise this date range to see the shape of your
                    traffic.
                </small>
            </div>
        );
    return (
        <div
            className={small ? "sparkline" : "activity-chart"}
            aria-label={`${label} over time`}
        >
            <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                <AreaChart
                    data={data}
                    margin={{
                        top: small ? 0 : 16,
                        right: 8,
                        bottom: 0,
                        left: small ? 0 : -20,
                    }}
                    accessibilityLayer
                    onClick={(state) => {
                        const selected = state.activeLabel;
                        if (typeof selected === "string") {
                            setDay(selected);
                            onDay?.(selected);
                        }
                    }}
                >
                    <defs>
                        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
                            <stop
                                offset="0%"
                                stopColor="var(--accent)"
                                stopOpacity={0.2}
                            />
                            <stop
                                offset="100%"
                                stopColor="var(--accent)"
                                stopOpacity={0.005}
                            />
                        </linearGradient>
                    </defs>
                    {!small && (
                        <CartesianGrid
                            vertical={false}
                            stroke="var(--line)"
                            strokeDasharray="3 5"
                        />
                    )}
                    <XAxis
                        dataKey="date"
                        hide={small}
                        minTickGap={55}
                        tickLine={false}
                        axisLine={false}
                        tick={{fill: "var(--muted)", fontSize: 11}}
                        tickFormatter={(date) =>
                            new Date(
                                String(date) + "T00:00:00Z",
                            ).toLocaleDateString("en-GB", {
                                day: "numeric",
                                month: "short",
                                timeZone: "UTC",
                            })
                        }
                    />
                    <YAxis
                        hide={small}
                        tickLine={false}
                        axisLine={false}
                        tick={{fill: "var(--muted)", fontSize: 11}}
                        tickFormatter={(value) => compact(value)}
                    />
                    {!small && (
                        <Tooltip
                            content={({active, payload, label: date}) =>
                                active && payload?.length ? (
                                    <div className="chart-tooltip">
                                        <strong>{String(date)}</strong>
                                        {payload.map((item) => (
                                            <div key={String(item.dataKey)}>
                                                <span>
                                                    {item.dataKey ===
                                                    previousKey
                                                        ? "Previous period"
                                                        : label}
                                                </span>
                                                <b>{compact(item.value)}</b>
                                            </div>
                                        ))}
                                    </div>
                                ) : null
                            }
                            cursor={{
                                stroke: "var(--accent)",
                                strokeDasharray: "3 3",
                            }}
                        />
                    )}
                    {comparison && (
                        <Area
                            dataKey={previousKey}
                            name="Previous period"
                            type="monotone"
                            stroke="var(--chart-previous)"
                            strokeWidth={1.75}
                            strokeDasharray="5 5"
                            fill="transparent"
                            connectNulls={false}
                            isAnimationActive={false}
                        />
                    )}
                    <Area
                        dataKey={currentKey}
                        name={label}
                        type="monotone"
                        stroke="var(--accent)"
                        strokeWidth={small ? 1.75 : 2.5}
                        fill={`url(#${id})`}
                        connectNulls={false}
                        activeDot={
                            small
                                ? false
                                : {r: 5, stroke: "var(--panel)", strokeWidth: 3}
                        }
                        isAnimationActive={false}
                    />
                </AreaChart>
            </ResponsiveContainer>
            {!small && day && (
                <p className="chart-selection" role="status">
                    Selected {day}
                    {onDay
                        ? " · Exploring this day"
                        : " · Use the arrow keys to inspect adjacent points"}
                </p>
            )}
        </div>
    );
}

export function Trend({rows, metric}: {rows: Row[]; metric: string}) {
    return (
        <ActivityChart
            data={rows.map((row) => ({
                ...row,
                date: String(row.date ?? "").replace(
                    /^(\d{4})(\d{2})(\d{2})$/,
                    "$1-$2-$3",
                ),
                value: row[metric],
            }))}
            label={titleCase(metric)}
            comparison={false}
        />
    );
}

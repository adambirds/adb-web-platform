"use client";

import { Card, EmptyState } from "@/components/ui";
import { useState } from "react";

interface TimingResult {
    id: number;
    started_at: string;
    duration_ms: number;
    outcome: string;
    message: string;
}

const dateLabel = (value: string) =>
    new Intl.DateTimeFormat("en-GB", {
        dateStyle: "medium",
        timeStyle: "short",
    }).format(new Date(value));

export function MonitoringHistoryChart({
    results,
    total,
}: {
    results: TimingResult[];
    total: number;
}) {
    const [selectedId, setSelectedId] = useState<number | null>(null);
    const points = results
        .filter(
            (result) =>
                Number.isFinite(Date.parse(result.started_at)) &&
                Number.isFinite(result.duration_ms),
        )
        .toSorted(
            (a, b) =>
                Date.parse(a.started_at) - Date.parse(b.started_at) ||
                a.id - b.id,
        );
    const selected = points.find((point) => point.id === selectedId);
    const maxDuration = Math.max(
        1,
        ...points
            .filter((point) => point.outcome === "success")
            .map((point) => point.duration_ms),
    );
    const first = points[0];
    const last = points.at(-1);
    const start = first ? Date.parse(first.started_at) : 0;
    const end = last ? Date.parse(last.started_at) : 0;
    const x = (point: TimingResult) =>
        start === end
            ? 435
            : 70 +
              ((Date.parse(point.started_at) - start) / (end - start)) * 730;
    const y = (point: TimingResult) =>
        220 - (point.duration_ms / maxDuration) * 180;
    const segments: string[] = [];
    let segment = "";
    for (const point of points) {
        if (point.outcome === "success") {
            segment += `${segment ? " L" : "M"}${x(point)},${y(point)}`;
        } else if (segment) {
            segments.push(segment);
            segment = "";
        }
    }
    if (segment) segments.push(segment);

    return (
        <Card className="space-y-4 p-5">
            <div>
                <h2 className="text-sm font-semibold text-white">
                    Probe duration history
                </h2>
                <p className="mt-1 text-xs text-slate-400">
                    Latest {points.length} of {total} observations. Complete
                    probe duration, including DNS and connection setup where
                    applicable.
                </p>
            </div>
            {!first || !last ? (
                <EmptyState
                    title="No timing history yet"
                    description="The graph will appear after this check runs."
                />
            ) : (
                <>
                    <div className="overflow-x-auto">
                        <svg
                            viewBox="0 0 850 310"
                            className="w-full min-w-[640px]"
                            role="group"
                            aria-label="Monitoring probe duration graph"
                        >
                            {[0, 0.5, 1].map((fraction) => (
                                <g key={fraction}>
                                    <line
                                        x1="70"
                                        x2="800"
                                        y1={220 - fraction * 180}
                                        y2={220 - fraction * 180}
                                        stroke="#334155"
                                    />
                                    <text
                                        x="60"
                                        y={224 - fraction * 180}
                                        textAnchor="end"
                                        fill="#94a3b8"
                                        fontSize="12"
                                    >
                                        {Math.round(maxDuration * fraction)} ms
                                    </text>
                                </g>
                            ))}
                            {segments.map((path, index) => (
                                <path
                                    key={index}
                                    d={path}
                                    fill="none"
                                    stroke="#22d3ee"
                                    strokeWidth="2"
                                    data-testid="successful-timing-segment"
                                />
                            ))}
                            <text x="70" y="254" fill="#94a3b8" fontSize="11">
                                Failed / error probes
                            </text>
                            <line
                                x1="70"
                                x2="800"
                                y1="270"
                                y2="270"
                                stroke="#334155"
                            />
                            {points.map((point) => {
                                const label = `${dateLabel(point.started_at)}: ${point.outcome}, ${point.duration_ms} ms`;
                                return (
                                    <circle
                                        key={point.id}
                                        cx={x(point)}
                                        cy={
                                            point.outcome === "success"
                                                ? y(point)
                                                : 270
                                        }
                                        r={selectedId === point.id ? 6 : 4}
                                        fill={
                                            point.outcome === "success"
                                                ? "#22d3ee"
                                                : point.outcome === "error"
                                                  ? "#fbbf24"
                                                  : "#f87171"
                                        }
                                        tabIndex={0}
                                        role="button"
                                        aria-label={label}
                                        onMouseEnter={() =>
                                            setSelectedId(point.id)
                                        }
                                        onFocus={() => setSelectedId(point.id)}
                                        onClick={() => setSelectedId(point.id)}
                                        onKeyDown={(event) => {
                                            if (
                                                event.key === "Enter" ||
                                                event.key === " "
                                            ) {
                                                event.preventDefault();
                                                setSelectedId(point.id);
                                            }
                                        }}
                                    >
                                        <title>{label}</title>
                                    </circle>
                                );
                            })}
                            <text x="70" y="302" fill="#94a3b8" fontSize="11">
                                {dateLabel(first.started_at)}
                            </text>
                            <text
                                x="800"
                                y="302"
                                textAnchor="end"
                                fill="#94a3b8"
                                fontSize="11"
                            >
                                {dateLabel(last.started_at)}
                            </text>
                        </svg>
                    </div>
                    <div className="flex flex-wrap gap-4 text-xs text-slate-400">
                        <span className="text-cyan-300">● Success</span>
                        <span className="text-red-300">● Failure</span>
                        <span className="text-amber-300">
                            ● Execution error
                        </span>
                    </div>
                    <p
                        className="min-h-10 text-sm text-slate-300"
                        aria-live="polite"
                    >
                        {selected
                            ? `${dateLabel(selected.started_at)} · ${selected.outcome} · ${selected.duration_ms} ms${selected.message ? ` · ${selected.message}` : ""}`
                            : "Hover, tap or focus an observation to inspect it. Failures break the timing line."}
                    </p>
                </>
            )}
        </Card>
    );
}

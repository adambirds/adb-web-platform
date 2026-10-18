import type {ReactNode} from "react";
import {
    ArrowDownRightIcon,
    ArrowUpRightIcon,
} from "@heroicons/react/24/outline";
import {compact} from "../../lib/experience";
export function Delta({
    value,
    comparison = true,
}: {
    value: number | null;
    comparison?: boolean;
}) {
    return !comparison ? null : (
        <span
            className={`delta ${value === null || value === 0 ? "neutral" : value > 0 ? "up" : "down"}`}
            title={
                value === null
                    ? "A comparable previous period is unavailable or zero"
                    : "Compared with the previous equal-length period"
            }
        >
            {value === null ? (
                "No comparison"
            ) : (
                <>
                    {value >= 0 ? <ArrowUpRightIcon /> : <ArrowDownRightIcon />}
                    {Math.abs(value).toFixed(1)}%
                </>
            )}
        </span>
    );
}
export function MetricCard({
    label,
    value,
    delta,
    metric = "",
    icon,
    selected,
    onClick,
    comparison = true,
    caption,
}: {
    label: string;
    value: unknown;
    delta: number | null;
    metric?: string;
    icon: ReactNode;
    selected?: boolean;
    onClick?: () => void;
    comparison?: boolean;
    caption?: string;
}) {
    return (
        <button
            className={`metric-card ${selected ? "selected" : ""}`}
            onClick={onClick}
            aria-pressed={selected}
            title={caption}
            aria-label={`${label}: ${compact(value, metric)}`}
        >
            <span className="metric-label">
                {label}
                <span>{icon}</span>
            </span>
            <span className="metric-value">{compact(value, metric)}</span>
            <span className="metric-foot">
                <Delta value={delta} comparison={comparison} />
                <small>
                    {caption ??
                        (comparison ? "vs previous period" : "Selected period")}
                </small>
            </span>
        </button>
    );
}

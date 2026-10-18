import Link from "next/link";
import {
    ArrowRightIcon,
    ArrowTrendingUpIcon,
    BoltIcon,
    ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";
import type {Insight, Period} from "../../lib/experience";
import {exploreHref} from "../../lib/experience";
export function InsightCard({
    insight,
    period,
    compact = false,
}: {
    insight: Insight;
    period: Period;
    compact?: boolean;
}) {
    const Icon =
        insight.level === "attention"
            ? ExclamationTriangleIcon
            : insight.level === "positive"
              ? ArrowTrendingUpIcon
              : BoltIcon;
    return (
        <Link
            className={`insight-card ${insight.level} ${compact ? "compact" : ""}`}
            href={exploreHref(
                insight.website_id,
                insight.report,
                period,
                insight.value,
            )}
        >
            <span className="insight-icon">
                <Icon />
            </span>
            <div>
                <span className="insight-domain">{insight.domain}</span>
                <h3>{insight.title}</h3>
                {!compact && <p>{insight.detail}</p>}
                <span className="insight-action">
                    {insight.action}
                    <ArrowRightIcon />
                </span>
            </div>
        </Link>
    );
}
export function Insights({
    items,
    period,
    compact = false,
}: {
    items: Insight[];
    period: Period;
    compact?: boolean;
}) {
    return items.length ? (
        <div className="insight-list">
            {items.map((insight) => (
                <InsightCard
                    key={insight.id}
                    insight={insight}
                    period={period}
                    compact={compact}
                />
            ))}
        </div>
    ) : (
        <div className="insights-quiet">
            <span className="quiet-orbit">
                <BoltIcon />
            </span>
            <strong>A clearer picture is building</strong>
            <p>
                Meaningful insights appear when there is enough comparable data.
                No unsupported predictions or invented explanations.
            </p>
        </div>
    );
}

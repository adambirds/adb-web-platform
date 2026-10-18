"use client";
import Link from "next/link";
import {ArrowUpRightIcon} from "@heroicons/react/24/outline";
import {compact} from "../../lib/experience";
export type RankingItem = {
    label: string;
    detail?: string;
    value: number | null;
    secondary?: string;
    onClick?: () => void;
    href?: string;
};
export function RankedList({
    title,
    subtitle,
    metric,
    items,
    href,
    tone = "blue",
    empty = "No data for this period",
    tabs,
}: {
    title: string;
    subtitle?: string;
    metric: string;
    items: RankingItem[];
    href?: string;
    tone?: string;
    empty?: string;
    tabs?: React.ReactNode;
}) {
    const max = Math.max(...items.map((item) => item.value ?? 0), 1);
    return (
        <section className={`report-card tone-${tone}`}>
            <div className="report-card-heading">
                <div>
                    <h2>{title}</h2>
                    {subtitle && <p>{subtitle}</p>}
                </div>
                {href && (
                    <Link
                        href={href}
                        className="text-link"
                        aria-label={`Explore ${title}`}
                    >
                        Explore
                        <ArrowUpRightIcon />
                    </Link>
                )}
            </div>
            {tabs}
            <div className="rank-labels">
                <span>{title === "Traffic sources" ? "Source" : "Name"}</span>
                <span>{metric}</span>
            </div>
            {items.length ? (
                <div className="ranking">
                    {items.map((item, index) => {
                        const body = (
                            <>
                                <span
                                    className="rank-track"
                                    style={{
                                        width: `${Math.max(((item.value ?? 0) / max) * 100, 1)}%`,
                                    }}
                                />
                                <span className="rank-content">
                                    <span
                                        className="rank-name"
                                        title={item.label}
                                    >
                                        <span className="rank-number">
                                            {String(index + 1).padStart(2, "0")}
                                        </span>
                                        <span>
                                            {item.label}
                                            {item.detail && (
                                                <small>{item.detail}</small>
                                            )}
                                        </span>
                                    </span>
                                    <span className="rank-value">
                                        {compact(item.value)}
                                        {item.secondary && (
                                            <small>{item.secondary}</small>
                                        )}
                                    </span>
                                </span>
                            </>
                        );
                        return item.href ? (
                            <Link
                                className="ranking-row"
                                href={item.href}
                                key={item.label + index}
                            >
                                {body}
                            </Link>
                        ) : (
                            <button
                                className="ranking-row"
                                key={item.label + index}
                                onClick={item.onClick}
                            >
                                {body}
                            </button>
                        );
                    })}
                </div>
            ) : (
                <div className="ranking-empty">
                    <p>{empty}</p>
                    <small>
                        Missing reports are never replaced with sample
                        statistics.
                    </small>
                </div>
            )}
        </section>
    );
}

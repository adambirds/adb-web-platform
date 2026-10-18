"use client";
import {useState} from "react";
import Link from "next/link";
import {useRouter, useSearchParams} from "next/navigation";
import {
    ArrowLeftIcon,
    AdjustmentsHorizontalIcon,
} from "@heroicons/react/24/outline";
import {exploreHref, siteHref} from "../../lib/experience";
import {Reports, type Section} from "../reports/ReportExplorer";
import {PeriodControls} from "./PeriodControls";
import {ErrorState, useExperience} from "./ExperienceProvider";
const reports: [Section, string][] = [
    ["overview", "Traffic overview"],
    ["acquisition", "Traffic sources & campaigns"],
    ["pages", "Pages & engagement"],
    ["audience", "Countries, devices & browsers"],
    ["events", "Custom events & parameters"],
    ["key-events", "Key events"],
    ["search", "Search overview, countries & devices"],
    ["queries", "Search queries"],
    ["search-pages", "Search pages"],
    ["opportunities", "SEO opportunities"],
    ["realtime", "Realtime activity"],
];
export function ExplorerPage({websiteId}: {websiteId: number}) {
    const {session, period, comparison} = useExperience();
    const query = useSearchParams(),
        router = useRouter();
    const [revision, setRevision] = useState(0);
    const website = session.businesses
            .flatMap((b) => b.websites)
            .find((item) => item.id === websiteId),
        business = session.businesses.find(
            (b) => b.id === website?.business_id,
        );
    const section =
        reports.find(([key]) => key === query.get("report"))?.[0] ?? "events";
    const value = query.get("value") ?? "";
    if (!website)
        return (
            <main className="experience-page">
                <ErrorState
                    message="This website is unavailable."
                    retry={() => router.push("/dashboard")}
                />
            </main>
        );
    return (
        <main className="experience-page explorer-page">
            <Link className="back-link" href={siteHref(websiteId, period)}>
                <ArrowLeftIcon />
                {website.domain}
            </Link>
            <div className="page-heading">
                <div>
                    <p className="eyebrow">POWERFUL ON DEMAND</p>
                    <h1>Follow your curiosity.</h1>
                    <p className="page-description">
                        Detailed reports, real evidence and room to investigate.
                    </p>
                </div>
                <PeriodControls />
            </div>
            <div className="explorer-selector">
                <AdjustmentsHorizontalIcon />
                <label>
                    Explore
                    <select
                        value={section}
                        onChange={(event) =>
                            router.push(
                                exploreHref(
                                    websiteId,
                                    event.target.value,
                                    period,
                                ),
                            )
                        }
                    >
                        {reports.map(([key, label]) => (
                            <option key={key} value={key}>
                                {label}
                            </option>
                        ))}
                    </select>
                </label>
                <span>
                    Filters apply to this report only. Portfolio and overview
                    totals remain unchanged.
                </span>
            </div>
            {value && (
                <div className="filter-chip-row">
                    <span>
                        Contains: <strong>{value}</strong>
                    </span>
                    <button
                        className="text-link"
                        onClick={() =>
                            router.replace(
                                exploreHref(websiteId, section, period),
                            )
                        }
                    >
                        Clear filter ×
                    </button>
                </div>
            )}
            <div className="advanced-tools">
                <Reports
                    key={`${website.id}:${section}:${value}`}
                    website={website}
                    section={section}
                    dates={period}
                    comparison={comparison}
                    canManage={business?.role !== "viewer"}
                    revision={revision}
                    refresh={() => setRevision((n) => n + 1)}
                    onIntegrations={() =>
                        router.push(siteHref(websiteId, period, "/settings"))
                    }
                    initialSearch={value}
                />
            </div>
        </main>
    );
}

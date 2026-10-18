"use client";
import {useState} from "react";
import {usePathname, useRouter, useSearchParams} from "next/navigation";
import {CalendarDaysIcon, ChevronDownIcon} from "@heroicons/react/24/outline";
import {initialDates} from "../../app/client";
import {useExperience} from "./ExperienceProvider";

export function PeriodControls() {
    const {period, comparison} = useExperience();
    const router = useRouter(),
        pathname = usePathname(),
        query = useSearchParams();
    const [custom, setCustom] = useState(period);
    function update(start: string, end: string) {
        const next = new URLSearchParams(query.toString());
        next.set("start", start);
        next.set("end", end);
        router.replace(pathname + "?" + next.toString());
    }
    return (
        <div className="period-controls">
            <label className="compare-toggle">
                <input
                    type="checkbox"
                    checked={comparison}
                    onChange={(event) => {
                        const next = new URLSearchParams(query.toString());
                        next.set("compare", event.target.checked ? "1" : "0");
                        router.replace(pathname + "?" + next.toString());
                    }}
                />
                Compare previous period
            </label>
            <details className="period-picker">
                <summary className="button">
                    <CalendarDaysIcon />
                    {new Date(period.start + "T00:00:00Z").toLocaleDateString(
                        "en-GB",
                        {day: "numeric", month: "short", timeZone: "UTC"},
                    )}{" "}
                    —{" "}
                    {new Date(period.end + "T00:00:00Z").toLocaleDateString(
                        "en-GB",
                        {day: "numeric", month: "short", timeZone: "UTC"},
                    )}
                    <ChevronDownIcon />
                </summary>
                <div className="period-popover">
                    <p>Reporting period</p>
                    <div className="period-presets">
                        {[7, 28, 90].map((days) => (
                            <button
                                key={days}
                                onClick={(event) => {
                                    const end = initialDates().end;
                                    const start = new Date(
                                        Date.parse(end + "T00:00:00Z") -
                                            (days - 1) * 86400000,
                                    )
                                        .toISOString()
                                        .slice(0, 10);
                                    update(start, end);
                                    event.currentTarget
                                        .closest("details")
                                        ?.removeAttribute("open");
                                }}
                            >
                                Last {days} days
                            </button>
                        ))}
                    </div>
                    <form
                        onSubmit={(event) => {
                            event.preventDefault();
                            update(custom.start, custom.end);
                            event.currentTarget
                                .closest("details")
                                ?.removeAttribute("open");
                        }}
                    >
                        <label>
                            From
                            <input
                                aria-label="From"
                                type="date"
                                required
                                max={custom.end}
                                value={custom.start}
                                onChange={(event) =>
                                    setCustom({
                                        ...custom,
                                        start: event.target.value,
                                    })
                                }
                            />
                        </label>
                        <label>
                            To
                            <input
                                aria-label="To"
                                type="date"
                                required
                                min={custom.start}
                                max={new Date().toISOString().slice(0, 10)}
                                value={custom.end}
                                onChange={(event) =>
                                    setCustom({
                                        ...custom,
                                        end: event.target.value,
                                    })
                                }
                            />
                        </label>
                        <button className="button primary">Apply dates</button>
                    </form>
                    <small>
                        Latest complete reporting window ends three days ago to
                        align search and traffic data.
                    </small>
                </div>
            </details>
        </div>
    );
}

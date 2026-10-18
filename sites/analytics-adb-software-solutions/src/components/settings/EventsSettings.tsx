"use client";
import {useState} from "react";
import {type Report, type Website} from "../../app/client";
import {useExperience} from "../experience/ExperienceProvider";
import {useResource} from "../experience/useResource";
import {compact} from "../../lib/experience";
import {TrackingSettings} from "./TrackingSettings";
export function EventsSettings({website}: {website: Website}) {
    const {period} = useExperience();
    const [selectedEvent, setSelectedEvent] = useState("");
    const {data, error} = useResource<Report>(
        website.providers.some((prop) => prop.provider === "ga4")
            ? `/websites/${website.id}/reports/ga4/events?${new URLSearchParams(period)}&page_size=12`
            : null,
    );
    return (
        <div className="settings-sections">
            <section className="settings-card">
                <p className="eyebrow">UNDERSTAND THE ACTIONS THAT MATTER</p>
                <h2>Events on your website</h2>
                <p>
                    Observed events for the selected reporting period. Discover
                    what is already being collected, then choose the actions you
                    want to count as key events.
                </p>
                {error && (
                    <p role="alert" className="data-notice warning">
                        {error}
                    </p>
                )}
                <div className="observed-events">
                    {data?.current?.rows.length ? (
                        data.current.rows.map((row) => (
                            <div
                                className="observed-event"
                                key={String(row.eventName)}
                            >
                                <button
                                    className="text-link"
                                    onClick={() => {
                                        setSelectedEvent(String(row.eventName));
                                        document
                                            .getElementById(
                                                "event-configuration",
                                            )
                                            ?.scrollIntoView?.({
                                                behavior: "smooth",
                                                block: "start",
                                            });
                                    }}
                                >
                                    {row.eventName}
                                </button>
                                <strong>{compact(row.eventCount)}</strong>
                                {Number(row.keyEvents) > 0 && (
                                    <span className="health-pill healthy">
                                        Key action
                                    </span>
                                )}
                            </div>
                        ))
                    ) : (
                        <p className="data-notice">
                            {data
                                ? "No stored events for this reporting period. Sync your website or choose a period with data."
                                : "Event discovery uses your stored Google reports; it cannot discover unregistered event parameters."}
                        </p>
                    )}
                </div>
            </section>
            <div className="data-notice">
                Google consent and Google property roles are separate. Editor or
                Administrator access on this GA4 property is required for
                configuration changes. Nothing is created or changed
                automatically.
            </div>
            <div
                className="advanced-tools event-configuration"
                id="event-configuration"
            >
                <TrackingSettings
                    key={`${website.id}:${selectedEvent}`}
                    website={website}
                    initialEvent={selectedEvent}
                />
            </div>
        </div>
    );
}

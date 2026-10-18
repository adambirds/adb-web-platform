"use client";
import {useState} from "react";
import Link from "next/link";
import {useSearchParams} from "next/navigation";
import {ArrowLeftIcon} from "@heroicons/react/24/outline";
import {GoogleOnboarding} from "../../app/onboarding";
import {siteHref} from "../../lib/experience";
import {IntegrationSettings} from "../settings/IntegrationSettings";
import {TrackingSettings} from "../settings/TrackingSettings";
import {WorkspaceSettings} from "../settings/WorkspaceSettings";
import {useExperience} from "./ExperienceProvider";
import {Tabs} from "./Tabs";
export function SettingsPage({websiteId}: {websiteId?: number}) {
    const {session, period, refreshSession} = useExperience();
    const query = useSearchParams();
    const website = session.businesses
        .flatMap((b) => b.websites)
        .find((site) => site.id === websiteId);
    const [businessId, setBusinessId] = useState(
        website?.business_id ?? session.businesses[0]?.id ?? 0,
    );
    const business = session.businesses.find((item) => item.id === businessId);
    const [tab, setTab] = useState(
        query.get("tab") === "websites" || !website
            ? "websites"
            : "connections",
    );
    const refresh = async () => {
        refreshSession();
    };
    return (
        <main className="experience-page settings-page">
            <Link
                className="back-link"
                href={website ? siteHref(website.id, period) : "/dashboard"}
            >
                <ArrowLeftIcon />
                {website?.domain ?? "Portfolio"}
            </Link>
            <div className="page-heading">
                <div>
                    <p className="eyebrow">WORKSPACE & CONNECTIONS</p>
                    <h1>
                        {website
                            ? "Keep everything connected."
                            : "Make yourself at home."}
                    </h1>
                    <p className="page-description">
                        Google connections, website settings and advanced
                        tracking configuration.
                    </p>
                </div>
                {!website && session.businesses.length > 1 && (
                    <label>
                        Workspace
                        <select
                            value={businessId}
                            onChange={(event) =>
                                setBusinessId(Number(event.target.value))
                            }
                        >
                            {session.businesses.map((item) => (
                                <option key={item.id} value={item.id}>
                                    {item.name}
                                </option>
                            ))}
                        </select>
                    </label>
                )}
            </div>
            {business?.role === "viewer" ? (
                <div className="data-notice">
                    Your workspace administrator manages connections and access.{" "}
                    <Link href="/dashboard">Return to reports</Link>
                </div>
            ) : (
                <>
                    <Tabs
                        value={tab}
                        onChange={setTab}
                        values={
                            website
                                ? [
                                      ["connections", "Connections"],
                                      ["tracking", "Events & configuration"],
                                      ["workspace", "Website & access"],
                                      ["websites", "Add websites"],
                                  ]
                                : [
                                      ["websites", "Add websites"],
                                      ["workspace", "Workspace"],
                                  ]
                        }
                    />
                    {tab === "websites" ? (
                        <div className="onboarding-page">
                            <GoogleOnboarding
                                business={business}
                                onComplete={refresh}
                            />
                        </div>
                    ) : !website || !business ? (
                        <section className="empty-state">
                            <h2>Select a website to manage its settings</h2>
                            <div className="settings-site-links">
                                {session.businesses
                                    .flatMap((item) => item.websites)
                                    .map((site) => (
                                        <Link
                                            key={site.id}
                                            href={siteHref(
                                                site.id,
                                                period,
                                                "/settings",
                                            )}
                                        >
                                            {site.domain}
                                        </Link>
                                    ))}
                            </div>
                        </section>
                    ) : (
                        <div className="advanced-tools">
                            {tab === "connections" ? (
                                <IntegrationSettings
                                    business={business}
                                    website={website}
                                    refresh={refresh}
                                />
                            ) : tab === "tracking" ? (
                                <TrackingSettings website={website} />
                            ) : (
                                <WorkspaceSettings
                                    business={business}
                                    website={website}
                                    refresh={refresh}
                                />
                            )}
                        </div>
                    )}
                </>
            )}
        </main>
    );
}

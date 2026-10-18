"use client";
import {useState} from "react";
import Link from "next/link";
import {useRouter, useSearchParams} from "next/navigation";
import {
    ArrowLeftIcon,
    ArrowUpRightIcon,
    BoltIcon,
    GlobeAltIcon,
    LinkIcon,
    PlusIcon,
    UsersIcon,
} from "@heroicons/react/24/outline";
import {GoogleOnboarding} from "../../app/onboarding";
import {siteHref} from "../../lib/experience";
import {IntegrationSettings} from "../settings/IntegrationSettings";
import {EventsSettings} from "../settings/EventsSettings";
import {WebsiteSettings} from "../settings/WebsiteSettings";
import {WorkspaceSettings} from "../settings/WorkspaceSettings";
import {WebsiteForm} from "../settings/WorkspaceForms";
import {useExperience} from "./ExperienceProvider";
const areas = [
    {
        key: "websites",
        label: "Websites",
        detail: "Properties & collection",
        icon: GlobeAltIcon,
    },
    {
        key: "accounts",
        label: "Google accounts",
        detail: "Connections & permissions",
        icon: LinkIcon,
    },
    {
        key: "events",
        label: "Events & conversions",
        detail: "Actions & definitions",
        icon: BoltIcon,
    },
    {
        key: "workspace",
        label: "Workspace",
        detail: "People & access",
        icon: UsersIcon,
    },
];
export function SettingsPage({websiteId}: {websiteId?: number}) {
    const {session, period, refreshSession} = useExperience(),
        query = useSearchParams(),
        router = useRouter();
    const website = session.businesses
        .flatMap((business) => business.websites)
        .find((site) => site.id === websiteId);
    const requestedBusiness =
        website?.business_id ??
        (query.has("business")
            ? Number(query.get("business"))
            : session.businesses[0]?.id);
    const business = session.businesses.find(
        (item) => item.id === requestedBusiness,
    );
    const legacyTab = {connections: "accounts", tracking: "events"}[
            query.get("tab") ?? ""
        ],
        tab =
            areas.find((area) => area.key === query.get("tab"))?.key ??
            legacyTab ??
            "websites";
    const [eventSite, setEventSite] = useState(
        website?.id ?? business?.websites[0]?.id ?? 0,
    );
    const chosen =
        website ??
        business?.websites.find((site) => site.id === eventSite) ??
        business?.websites[0];
    const href = (area: string, id = business?.id) =>
        `${websiteId ? siteHref(websiteId, undefined, "/settings") : "/dashboard/settings"}?${new URLSearchParams({tab: area, ...(id ? {business: String(id)} : {})})}`;
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
                    <p className="eyebrow">
                        A LITTLE ORGANISATION. A LOT LESS FRICTION.
                    </p>
                    <h1>
                        {website
                            ? "Website settings"
                            : "Your workspace, connected."}
                    </h1>
                    <p className="page-description">
                        {website
                            ? `${website.domain} · Properties, collection and meaningful actions.`
                            : "Your websites, Google accounts and people. Everything in its place."}
                    </p>
                </div>
                {!website && session.businesses.length > 1 && (
                    <label>
                        Workspace
                        <select
                            value={business?.id}
                            onChange={(event) =>
                                router.push(
                                    href(tab, Number(event.target.value)),
                                )
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
            {(websiteId && !website) || (query.has("business") && !business) ? (
                <div className="error-state" role="alert">
                    This website or workspace is not available to your account.
                </div>
            ) : business?.role === "viewer" ? (
                <div className="data-notice">
                    Your workspace administrator manages connections and access.{" "}
                    <Link href="/dashboard">Return to reports</Link>
                </div>
            ) : (
                <div className="settings-layout">
                    <nav
                        className="settings-navigation"
                        aria-label="Settings areas"
                    >
                        {areas.map((area) => (
                            <Link
                                key={area.key}
                                aria-label={area.label}
                                className={tab === area.key ? "active" : ""}
                                aria-current={
                                    tab === area.key ? "page" : undefined
                                }
                                href={
                                    area.key === "workspace" && website
                                        ? `/dashboard/settings?tab=workspace&business=${business?.id}`
                                        : href(area.key)
                                }
                            >
                                <area.icon />
                                <span>
                                    <strong>{area.label}</strong>
                                    <small>{area.detail}</small>
                                </span>
                                {area.key === "workspace" && website && (
                                    <ArrowUpRightIcon />
                                )}
                            </Link>
                        ))}
                        <p>
                            Changes to Google accounts and workspace access
                            apply across this business.
                        </p>
                    </nav>
                    <div
                        className="settings-content"
                        key={`${business?.id}:${websiteId ?? "portfolio"}:${tab}`}
                    >
                        {query.get("integration") === "denied" && (
                            <p role="alert" className="data-notice warning">
                                Google consent was cancelled or declined. Your
                                existing connection has not been replaced. Try
                                again when you’re ready.
                            </p>
                        )}
                        {query.get("integration") ===
                            "google_account_mismatch" && (
                            <p role="alert" className="data-notice warning">
                                Choose the same Google account to reconnect it.
                                Your existing connection has not changed. To add
                                a different account, choose Connect Google.
                            </p>
                        )}
                        {query.get("integration") ===
                            "offline_access_required" && (
                            <p role="alert" className="data-notice warning">
                                Google did not grant offline access. Connect
                                again and accept the requested permissions so
                                reporting can continue while you’re away.
                            </p>
                        )}
                        {["error", "google_access_not_granted"].includes(
                            query.get("integration") ?? "",
                        ) && (
                            <p role="alert" className="data-notice warning">
                                Google could not complete the connection. Your
                                existing reports are safe. Please try again.
                            </p>
                        )}
                        {query.get("integration") === "connected" && (
                            <p role="status" className="data-notice">
                                Google account connected. Permissions shown
                                below reflect the access Google actually
                                granted.
                            </p>
                        )}
                        {tab === "accounts" && business ? (
                            <IntegrationSettings
                                business={business}
                                refresh={refresh}
                            />
                        ) : tab === "workspace" && business ? (
                            <WorkspaceSettings
                                business={business}
                                refresh={refresh}
                            />
                        ) : tab === "events" ? (
                            <>
                                {!website && business && (
                                    <label className="settings-website-picker">
                                        Website
                                        <select
                                            value={chosen?.id ?? 0}
                                            onChange={(event) =>
                                                setEventSite(
                                                    Number(event.target.value),
                                                )
                                            }
                                        >
                                            {business.websites.map((site) => (
                                                <option
                                                    key={site.id}
                                                    value={site.id}
                                                >
                                                    {site.domain}
                                                </option>
                                            ))}
                                        </select>
                                    </label>
                                )}
                                {chosen ? (
                                    <EventsSettings website={chosen} />
                                ) : (
                                    <section className="settings-card settings-empty">
                                        <BoltIcon />
                                        <h2>Add a website to explore events</h2>
                                        <p>
                                            Connect a GA4 property, then
                                            discover collected events and
                                            configure key actions.
                                        </p>
                                        <Link
                                            className="button"
                                            href={href("websites")}
                                        >
                                            View websites
                                        </Link>
                                    </section>
                                )}
                            </>
                        ) : website && business ? (
                            <WebsiteSettings
                                website={website}
                                business={business}
                                refresh={refresh}
                            />
                        ) : (
                            <div className="settings-sections">
                                <div className="settings-section-heading">
                                    <div>
                                        <h2>Your connected websites</h2>
                                        <p>
                                            Manage individual properties and
                                            collection from each website.
                                        </p>
                                    </div>
                                    <Link
                                        className="button primary"
                                        href={href("websites") + "&action=add"}
                                    >
                                        <PlusIcon />
                                        Add websites
                                    </Link>
                                </div>
                                {query.get("action") === "add" ||
                                !business?.websites.length ? (
                                    <GoogleOnboarding
                                        business={business}
                                        onComplete={refresh}
                                    />
                                ) : (
                                    <div className="settings-website-grid">
                                        {business.websites.map((site) => (
                                            <section
                                                className="settings-card website-settings-tile"
                                                key={site.id}
                                            >
                                                <div className="settings-card-title">
                                                    <span className="site-avatar">
                                                        {site.domain[0].toUpperCase()}
                                                    </span>
                                                    <div>
                                                        <h3>{site.domain}</h3>
                                                        <p>{site.timezone}</p>
                                                    </div>
                                                </div>
                                                <div className="website-provider-badges">
                                                    {site.providers.map(
                                                        (prop) => (
                                                            <span
                                                                key={
                                                                    prop.provider
                                                                }
                                                                className={`health-pill ${prop.error_code ? "warning" : "healthy"}`}
                                                            >
                                                                {prop.provider ===
                                                                "ga4"
                                                                    ? "Analytics"
                                                                    : "Search Console"}{" "}
                                                                ·{" "}
                                                                {prop.error_code
                                                                    ? "Needs attention"
                                                                    : "Connected"}
                                                            </span>
                                                        ),
                                                    )}
                                                    {!site.providers.length && (
                                                        <span className="health-pill warning">
                                                            No properties linked
                                                        </span>
                                                    )}
                                                </div>
                                                <p>
                                                    {site.is_active
                                                        ? "Scheduled collection enabled"
                                                        : "Collection paused"}
                                                </p>
                                                <div className="settings-card-actions">
                                                    <Link
                                                        className="button"
                                                        href={siteHref(
                                                            site.id,
                                                            period,
                                                            "/settings",
                                                        )}
                                                    >
                                                        Manage website
                                                    </Link>
                                                    <Link
                                                        className="text-link"
                                                        href={siteHref(
                                                            site.id,
                                                            period,
                                                        )}
                                                    >
                                                        View reports{" "}
                                                        <ArrowUpRightIcon />
                                                    </Link>
                                                </div>
                                            </section>
                                        ))}
                                    </div>
                                )}
                                {business && (
                                    <details className="settings-card settings-disclosure">
                                        <summary>
                                            Manually add a website
                                        </summary>
                                        <p>
                                            Automatic discovery pairs Google
                                            properties and detects timezone. Use
                                            manual entry only when you need a
                                            website record before connecting its
                                            properties.
                                        </p>
                                        <div className="advanced-tools">
                                            <WebsiteForm
                                                business={business}
                                                refresh={refresh}
                                            />
                                        </div>
                                    </details>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </main>
    );
}

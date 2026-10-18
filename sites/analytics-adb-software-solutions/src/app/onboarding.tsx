"use client";

import {useCallback, useEffect, useState} from "react";
import {api, type Business} from "./client";

type Connection = {
    id: number;
    email: string;
    status: string;
    scopes?: string[];
};
export type DiscoveredWebsite = {
    domain: string;
    existing_id: number | null;
    ga4: {id: string; name: string; timezone: string}[];
    gsc: {id: string; name: string}[];
};
type Inventory = {websites: DiscoveredWebsite[]; warnings: string[]};
type Selection = {domain: string; ga4: string | null; gsc: string | null};

export function GoogleOnboarding({
    business,
    onComplete,
    onCancel,
}: {
    business?: Business;
    onComplete: () => Promise<void>;
    onCancel?: () => void;
}) {
    const [connections, setConnections] = useState<Connection[]>([]);
    const [connectionId, setConnectionId] = useState(0);
    const [inventory, setInventory] = useState<Inventory | null>(null);
    const [selected, setSelected] = useState<Record<string, Selection>>({});
    const [busy, setBusy] = useState(false);
    const [loading, setLoading] = useState(Boolean(business));
    const [error, setError] = useState("");
    const [integrationDenied, setIntegrationDenied] = useState(false);
    useEffect(() => {
        setIntegrationDenied(
            new URLSearchParams(window.location.search).get("integration") ===
                "denied",
        );
    }, []);
    const discover = useCallback(async (id: number, refresh = false) => {
        setBusy(true);
        setError("");
        setInventory(null);
        setSelected({});
        setConnectionId(id);
        try {
            setInventory(
                await api<Inventory>(
                    `/connections/${id}/websites${refresh ? "?refresh=true" : ""}`,
                ),
            );
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Could not find your websites. Try again.",
            );
        } finally {
            setBusy(false);
        }
    }, []);
    useEffect(() => {
        let active = true;
        if (!business) return;
        setLoading(true);
        void api<Connection[]>(`/businesses/${business.id}/connections`)
            .then(async (accounts) => {
                if (!active) return;
                const connected = accounts.filter(
                    (account) => account.status === "connected",
                );
                setConnections(connected);
                const requested = Number(
                    new URLSearchParams(window.location.search).get(
                        "connection",
                    ),
                );
                const account =
                    connected.find((account) => account.id === requested) ??
                    connected.at(-1);
                if (account) await discover(account.id);
            })
            .catch((err: unknown) => {
                if (active)
                    setError(
                        err instanceof Error
                            ? err.message
                            : "Could not load Google accounts.",
                    );
            })
            .finally(() => {
                if (active) setLoading(false);
            });
        return () => {
            active = false;
        };
    }, [business, discover]);
    const connect = async () => {
        setBusy(true);
        setError("");
        try {
            const id =
                business?.id ??
                (await api<{business_id: number}>("/onboarding", "POST"))
                    .business_id;
            const result = await api<{url: string}>(
                `/businesses/${id}/oauth`,
                "POST",
                {mode: "administration"},
            );
            window.location.assign(result.url);
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Could not connect Google.",
            );
            setBusy(false);
        }
    };
    const addWebsites = async () => {
        setBusy(true);
        setError("");
        try {
            const value = await api<{websites: {id: number}[]}>(
                `/connections/${connectionId}/websites`,
                "POST",
                {websites: Object.values(selected)},
            );
            if (value.websites[0])
                await api("/preferences", "PUT", {
                    website_id: value.websites[0].id,
                });
            await onComplete();
            window.history.replaceState(null, "", "/dashboard");
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Could not add your websites.",
            );
        } finally {
            setBusy(false);
        }
    };
    return (
        <section className="onboarding panel" aria-busy={busy || loading}>
            <div className="onboarding-heading">
                <span className="app-mark" aria-hidden="true">
                    A
                </span>
                <p className="eyebrow">ADB Analytics</p>
                <h1>
                    {inventory
                        ? "Choose your websites"
                        : "Your websites. One clear view."}
                </h1>
                <p className="muted">
                    {inventory
                        ? "Select the websites you want to follow. We match Analytics and Search Console and set the timezone for you."
                        : "Connect your Google account to find your websites and bring Analytics and Search Console together."}
                </p>
            </div>
            <p className="onboarding-permissions">
                Google consent includes Analytics reports, Search Console and
                supported GA4 configuration. Offline access keeps reports
                updating while you’re away. We never change Google configuration
                without your confirmation. <a href="/privacy">Privacy</a> ·{" "}
                <a href="/terms">Terms</a>
            </p>
            <div className="setup-steps" aria-label="Setup progress">
                <span className={!inventory ? "current" : ""}>
                    1 · Connect Google
                </span>
                <span className={inventory ? "current" : ""}>
                    2 · Choose websites
                </span>
                <span>3 · Dashboard</span>
            </div>
            {error && (
                <p className="notice error" role="alert">
                    {error}
                </p>
            )}
            {integrationDenied && (
                <p className="notice">
                    Google access was not granted. Connect again when you are
                    ready.
                </p>
            )}
            {(loading || busy) && (
                <p role="status">
                    {inventory
                        ? "Adding your websites…"
                        : "Finding your websites in Google…"}
                </p>
            )}
            {connections.some(
                (account) =>
                    account.scopes &&
                    !account.scopes.some((scope) =>
                        scope.endsWith("/analytics.edit"),
                    ),
            ) && (
                <p className="data-notice warning">
                    Some existing Google connections have reporting-only
                    consent. Reauthorise them in{" "}
                    <a
                        href={`/dashboard/settings?tab=accounts&business=${business?.id}`}
                    >
                        Google accounts
                    </a>{" "}
                    to enable supported GA4 configuration. Available reporting
                    can continue.
                </p>
            )}
            {connections.length > 0 && (
                <div className="actions">
                    <label>
                        Google account
                        <select
                            disabled={busy}
                            value={connectionId}
                            onChange={(event) =>
                                void discover(Number(event.target.value))
                            }
                        >
                            {connections.map((account) => (
                                <option key={account.id} value={account.id}>
                                    {account.email ||
                                        "Connected Google account"}
                                </option>
                            ))}
                        </select>
                    </label>
                    <button
                        disabled={busy}
                        onClick={() => void discover(connectionId, true)}
                    >
                        Refresh websites
                    </button>
                </div>
            )}
            {inventory && (
                <>
                    {inventory.warnings.map((warning) => (
                        <p className="notice" key={warning}>
                            {warning}
                        </p>
                    ))}
                    {!inventory.websites.length && (
                        <div className="empty">
                            <h2>No websites found</h2>
                            <p>
                                Check that this Google account can access a GA4
                                web property or a verified Search Console
                                property, then refresh or connect another
                                account.
                            </p>
                        </div>
                    )}
                    <p className="muted">
                        <small>Select up to 25 websites at a time.</small>
                    </p>
                    <div className="website-options">
                        {inventory.websites.map((site) => {
                            const selection = selected[site.domain];
                            const timezone =
                                site.ga4.find(
                                    (prop) => prop.id === selection?.ga4,
                                )?.timezone ??
                                (site.ga4.length === 1
                                    ? site.ga4[0].timezone
                                    : "Detected from your chosen property");
                            return (
                                <div
                                    className={`website-option ${selection ? "selected" : ""}`}
                                    key={site.domain}
                                >
                                    <label className="website-choice">
                                        <input
                                            type="checkbox"
                                            disabled={
                                                busy ||
                                                (!selection &&
                                                    Object.keys(selected)
                                                        .length >= 25)
                                            }
                                            checked={Boolean(selection)}
                                            onChange={(event) =>
                                                setSelected((previous) => {
                                                    const next = {...previous};
                                                    if (event.target.checked)
                                                        next[site.domain] = {
                                                            domain: site.domain,
                                                            ga4:
                                                                site.ga4
                                                                    .length ===
                                                                1
                                                                    ? site
                                                                          .ga4[0]
                                                                          .id
                                                                    : null,
                                                            gsc:
                                                                site.gsc[0]
                                                                    ?.id ??
                                                                null,
                                                        };
                                                    else
                                                        delete next[
                                                            site.domain
                                                        ];
                                                    return next;
                                                })
                                            }
                                        />
                                        <span>
                                            <strong>{site.domain}</strong>
                                            <span className="provider-badges">
                                                {site.ga4.length > 0 && (
                                                    <span>
                                                        Google Analytics
                                                    </span>
                                                )}
                                                {site.gsc.length > 0 && (
                                                    <span>Search Console</span>
                                                )}
                                                {site.existing_id && (
                                                    <span>
                                                        Already in workspace
                                                    </span>
                                                )}
                                            </span>
                                        </span>
                                    </label>
                                    {site.ga4.length > 1 && (
                                        <label>
                                            Analytics property
                                            <select
                                                disabled={!selection || busy}
                                                value={selection?.ga4 ?? ""}
                                                onChange={(event) =>
                                                    setSelected((previous) => ({
                                                        ...previous,
                                                        [site.domain]: {
                                                            ...previous[
                                                                site.domain
                                                            ],
                                                            ga4: event.target
                                                                .value,
                                                        },
                                                    }))
                                                }
                                            >
                                                <option value="">
                                                    Choose the property to use
                                                </option>
                                                {site.ga4.map((prop) => (
                                                    <option
                                                        key={prop.id}
                                                        value={prop.id}
                                                    >
                                                        {prop.name} · {prop.id}{" "}
                                                        · {prop.timezone}
                                                    </option>
                                                ))}
                                            </select>
                                        </label>
                                    )}
                                    {site.gsc.length > 1 && (
                                        <label>
                                            Search Console property
                                            <select
                                                disabled={!selection || busy}
                                                value={
                                                    selection?.gsc ??
                                                    site.gsc[0].id
                                                }
                                                onChange={(event) =>
                                                    setSelected((previous) => ({
                                                        ...previous,
                                                        [site.domain]: {
                                                            ...previous[
                                                                site.domain
                                                            ],
                                                            gsc: event.target
                                                                .value,
                                                        },
                                                    }))
                                                }
                                            >
                                                {site.gsc.map((prop) => (
                                                    <option
                                                        key={prop.id}
                                                        value={prop.id}
                                                    >
                                                        {prop.name}
                                                    </option>
                                                ))}
                                            </select>
                                        </label>
                                    )}
                                    <small>
                                        Timezone ·{" "}
                                        {site.ga4.length
                                            ? timezone
                                            : "America/Los_Angeles (Search Console)"}
                                    </small>
                                </div>
                            );
                        })}
                    </div>
                    {inventory.websites.length > 0 && (
                        <button
                            className="primary"
                            disabled={
                                busy ||
                                !Object.keys(selected).length ||
                                Object.values(selected).some(
                                    (site) =>
                                        inventory.websites.find(
                                            (row) => row.domain === site.domain,
                                        )?.ga4.length && !site.ga4,
                                )
                            }
                            onClick={() => void addWebsites()}
                        >
                            Add {Object.keys(selected).length || "selected"}{" "}
                            {Object.keys(selected).length === 1
                                ? "website"
                                : "websites"}
                        </button>
                    )}
                </>
            )}
            <div className="onboarding-footer actions">
                <button
                    className={!connections.length ? "primary" : ""}
                    disabled={busy || loading}
                    onClick={() => void connect()}
                >
                    {connections.length
                        ? "Connect another Google account"
                        : "Connect Google"}
                </button>
                {onCancel && (
                    <button disabled={busy} onClick={onCancel}>
                        Back to dashboard
                    </button>
                )}
            </div>
            <p className="muted">
                <small>
                    Read-only access to start. Configuration changes require
                    separate permission.
                </small>
            </p>
        </section>
    );
}

"use client";
import {useCallback, useEffect, useState} from "react";
import {api, type Business, type Website} from "../../app/client";
type Connection = {
    id: number;
    email: string;
    status: string;
    scopes: string[];
    error_code: string;
};
type Discovery = {
    ga4: {property: string; displayName: string}[];
    gsc: {siteUrl: string; permissionLevel: string}[];
};
export function IntegrationSettings({
    business,
    website,
    refresh,
}: {
    business: Business;
    website: Website;
    refresh: () => Promise<void>;
}) {
    const [connections, setConnections] = useState<Connection[]>([]);
    const [connectionId, setConnectionId] = useState(0);
    const [properties, setProperties] = useState<Discovery | null>(null);
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");
    const [busy, setBusy] = useState(false);
    const load = useCallback(async () => {
        setConnections(
            await api<Connection[]>(`/businesses/${business.id}/connections`),
        );
    }, [business.id]);
    useEffect(() => {
        void load().catch((err) => setError(String(err)));
    }, [load]);
    const connect = async (mode: string) => {
        setBusy(true);
        try {
            const result = await api<{url: string}>(
                `/businesses/${business.id}/oauth`,
                "POST",
                {mode},
            );
            window.location.assign(result.url);
        } catch (err) {
            setError(String(err));
            setBusy(false);
        }
    };
    return (
        <>
            <section className="panel">
                <h2>Bring your Google data together</h2>
                <p>
                    Use + Add websites to discover websites and match their
                    Google properties automatically. Manage account access and
                    existing connections here.
                </p>
                <p>
                    Reporting access reads GA4 and Search Console.
                    Administration additionally permits confirmed changes to GA4
                    custom definitions and key events.
                </p>
                <div className="actions">
                    <button
                        className="primary"
                        disabled={busy}
                        onClick={() => connect("reporting")}
                    >
                        Connect Google for reporting
                    </button>
                    <button
                        disabled={busy}
                        onClick={() => connect("administration")}
                    >
                        Connect with GA4 administration
                    </button>
                </div>
            </section>
            {error && (
                <p role="alert" className="notice error">
                    {error}
                </p>
            )}
            {message && (
                <p role="status" className="notice">
                    {message}
                </p>
            )}
            <section className="panel">
                <h2>Connected accounts</h2>
                {connections.length === 0 && (
                    <p>No Google accounts connected to this business yet.</p>
                )}
                {connections.map((connection) => (
                    <div className="panel" key={connection.id}>
                        <h3>
                            {connection.email ||
                                `Google account ${connection.id}`}
                        </h3>
                        <p>
                            {connection.status}
                            {connection.error_code &&
                                ` · ${connection.error_code}`}
                        </p>
                        <div className="actions">
                            <button
                                disabled={
                                    busy || connection.status !== "connected"
                                }
                                onClick={async () => {
                                    setBusy(true);
                                    setError("");
                                    setProperties(null);
                                    try {
                                        const value = await api<Discovery>(
                                            `/connections/${connection.id}/properties`,
                                        );
                                        setConnectionId(connection.id);
                                        setProperties(value);
                                    } catch (err) {
                                        setError(String(err));
                                    } finally {
                                        setBusy(false);
                                    }
                                }}
                            >
                                Advanced property selection
                            </button>
                            {connection.status !== "disconnected" && (
                                <button
                                    disabled={busy}
                                    onClick={async () => {
                                        if (
                                            !window.confirm(
                                                "Revoke this Google connection? All websites using this account will stop synchronizing.",
                                            )
                                        )
                                            return;
                                        setBusy(true);
                                        try {
                                            await api(
                                                `/connections/${connection.id}/disconnect`,
                                                "POST",
                                            );
                                            setProperties(null);
                                            await load();
                                            await refresh();
                                        } catch (err) {
                                            setError(String(err));
                                        } finally {
                                            setBusy(false);
                                        }
                                    }}
                                >
                                    Disconnect
                                </button>
                            )}
                            {connection.status === "reconnect" && (
                                <button
                                    onClick={() =>
                                        connect(
                                            connection.scopes.some((scope) =>
                                                scope.endsWith(
                                                    "analytics.edit",
                                                ),
                                            )
                                                ? "administration"
                                                : "reporting",
                                        )
                                    }
                                >
                                    Reconnect account
                                </button>
                            )}
                        </div>
                    </div>
                ))}
            </section>
            {properties && (
                <section className="panel">
                    <h2>Select properties for {website.name}</h2>
                    {(["ga4", "gsc"] as const).map((provider) => (
                        <form
                            key={provider}
                            onSubmit={async (e) => {
                                e.preventDefault();
                                const form = new FormData(e.currentTarget);
                                setBusy(true);
                                setError("");
                                try {
                                    await api(
                                        `/websites/${website.id}/properties/${provider}`,
                                        "PUT",
                                        {
                                            connection_id: connectionId,
                                            external_id: form.get("property"),
                                            search_type:
                                                form.get("search_type") ??
                                                "web",
                                        },
                                    );
                                    setMessage(
                                        "Property linked. Your first synchronization has started.",
                                    );
                                    await refresh();
                                } catch (err) {
                                    setError(String(err));
                                } finally {
                                    setBusy(false);
                                }
                            }}
                        >
                            <label>
                                {provider === "ga4"
                                    ? "GA4 property"
                                    : "Search Console property"}
                                <select
                                    name="property"
                                    required
                                    defaultValue=""
                                >
                                    <option value="" disabled>
                                        Select a property
                                    </option>
                                    {provider === "ga4"
                                        ? properties.ga4.map((p) => (
                                              <option
                                                  key={p.property}
                                                  value={p.property}
                                              >
                                                  {p.displayName} · {p.property}
                                              </option>
                                          ))
                                        : properties.gsc.map((p) => (
                                              <option
                                                  key={p.siteUrl}
                                                  value={p.siteUrl}
                                              >
                                                  {p.siteUrl} ·{" "}
                                                  {p.permissionLevel}
                                              </option>
                                          ))}
                                </select>
                            </label>
                            {provider === "gsc" && (
                                <label>
                                    Search type
                                    <select name="search_type">
                                        <option value="web">Web</option>
                                        <option value="image">Image</option>
                                        <option value="video">Video</option>
                                        <option value="news">News</option>
                                        <option value="discover">
                                            Discover
                                        </option>
                                        <option value="googleNews">
                                            Google News
                                        </option>
                                    </select>
                                </label>
                            )}
                            <button className="primary" disabled={busy}>
                                Link{" "}
                                {provider === "ga4" ? "GA4" : "Search Console"}
                            </button>
                        </form>
                    ))}
                    <p>
                        <small>
                            GA4 sets the website timezone automatically. Search
                            Console reports use Pacific Time. Use this advanced
                            selection only to change an existing association.
                        </small>
                    </p>
                </section>
            )}
            <section className="panel">
                <h2>This website’s integrations</h2>
                {website.providers.length ? (
                    website.providers.map((p) => (
                        <p key={p.provider}>
                            <strong>{p.provider.toUpperCase()}</strong> ·{" "}
                            {p.external_id}
                            <br />
                            <small>
                                {p.error_code ||
                                    (p.last_synced_at
                                        ? `Last synchronized ${new Date(p.last_synced_at).toLocaleString("en-GB")}`
                                        : "Awaiting initial synchronization")}
                            </small>
                            <br />
                            <button
                                disabled={busy}
                                onClick={async () => {
                                    if (
                                        !window.confirm(
                                            "Unlink this website property and remove its synchronized reports? The Google account remains available to other websites.",
                                        )
                                    )
                                        return;
                                    setBusy(true);
                                    try {
                                        await api(
                                            `/websites/${website.id}/properties/${p.provider}`,
                                            "DELETE",
                                            {confirmed: true},
                                        );
                                        await refresh();
                                        setMessage("Property unlinked.");
                                    } catch (err) {
                                        setError(String(err));
                                    } finally {
                                        setBusy(false);
                                    }
                                }}
                            >
                                Unlink property
                            </button>
                        </p>
                    ))
                ) : (
                    <p>
                        No properties linked yet. You can begin with either
                        provider.
                    </p>
                )}
            </section>
        </>
    );
}

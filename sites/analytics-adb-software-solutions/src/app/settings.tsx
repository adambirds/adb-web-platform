"use client";
import {useCallback, useEffect, useState} from "react";
import {api, type Business, type Website} from "./client";
import {CreateBusiness, WebsiteForm} from "./workspace";

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
type Definition = {
    name: string;
    parameterName?: string;
    displayName?: string;
    eventName?: string;
    measurementUnit?: string;
    scope?: string;
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

export function TrackingSettings({website}: {website: Website}) {
    const [kind, setKind] = useState("dimensions");
    const [definitions, setDefinitions] = useState<Definition[]>([]);
    const [canEdit, setCanEdit] = useState(false);
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");
    const [event, setEvent] = useState("button_click");
    const [parameters, setParameters] = useState(
        "button_id, button_text, button_location",
    );
    const [plan, setPlan] = useState<{
        registered: string[];
        missing: string[];
        notice: string;
        event_dimensions_used: number;
    } | null>(null);
    const [confirmed, setConfirmed] = useState(false);
    const [busy, setBusy] = useState(false);
    const load = useCallback(async () => {
        const result = await api<{items: Definition[]; can_edit: boolean}>(
            `/websites/${website.id}/definitions/${kind}`,
        );
        setDefinitions(result.items);
        setCanEdit(result.can_edit);
    }, [website.id, kind]);
    useEffect(() => {
        void load().catch((err) => setError(String(err)));
    }, [load]);
    const example = `// Run in a client component after Google tagging has loaded.\n// Send only non-personal values and respect your consent configuration.\nwindow.gtag?.('event', '${event}', {\n${parameters
        .split(",")
        .map((p) => p.trim())
        .filter(Boolean)
        .map((p) => `  ${JSON.stringify(p)}: 'your_value'`)
        .join(",\n")}\n});`;
    if (!website.providers.some((p) => p.provider === "ga4"))
        return (
            <section className="panel">
                <h2>Connect GA4 first</h2>
                <p>
                    Open Integrations and link a GA4 property before configuring
                    custom definitions.
                </p>
            </section>
        );
    return (
        <>
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
                <h2>Register event parameters</h2>
                <p>
                    Tell us which parameters your tracking sends. Google’s
                    reporting API cannot reveal arbitrary unregistered
                    parameters.
                </p>
                <form
                    onSubmit={async (e) => {
                        e.preventDefault();
                        setBusy(true);
                        setError("");
                        setConfirmed(false);
                        try {
                            setPlan(
                                await api(
                                    `/websites/${website.id}/tracking/plan`,
                                    "POST",
                                    {
                                        event,
                                        parameters: parameters
                                            .split(",")
                                            .map((p) => p.trim())
                                            .filter(Boolean),
                                    },
                                ),
                            );
                        } catch (err) {
                            setError(String(err));
                        } finally {
                            setBusy(false);
                        }
                    }}
                >
                    <label>
                        Event name
                        <input
                            value={event}
                            pattern="[A-Za-z][A-Za-z0-9_]{0,39}"
                            onChange={(e) => {
                                setEvent(e.target.value);
                                setPlan(null);
                            }}
                            required
                        />
                    </label>
                    <label>
                        Parameters, separated by commas
                        <input
                            value={parameters}
                            onChange={(e) => {
                                setParameters(e.target.value);
                                setPlan(null);
                            }}
                            required
                        />
                    </label>
                    <button disabled={busy}>Review definitions</button>
                </form>
                {plan && (
                    <div className="notice">
                        <p>
                            Already registered:{" "}
                            {plan.registered.join(", ") || "None"}
                            <br />
                            Proposed new definitions:{" "}
                            {plan.missing.join(", ") || "None"}
                            <br />
                            Event dimensions in use:{" "}
                            {plan.event_dimensions_used}. Google enforces your
                            property’s tier limits.
                        </p>
                        <p>{plan.notice}</p>
                        <label className="check">
                            <input
                                type="checkbox"
                                checked={confirmed}
                                onChange={(e) => setConfirmed(e.target.checked)}
                            />
                            I confirm these event parameter registrations.
                        </label>
                        <button
                            className="primary"
                            disabled={!confirmed || !canEdit || busy}
                            onClick={async () => {
                                setBusy(true);
                                try {
                                    const value = await api<{notice: string}>(
                                        `/websites/${website.id}/tracking/register`,
                                        "POST",
                                        {
                                            event,
                                            parameters: parameters
                                                .split(",")
                                                .map((p) => p.trim())
                                                .filter(Boolean),
                                            confirmed,
                                        },
                                    );
                                    setMessage(value.notice);
                                    setPlan(null);
                                    await load();
                                } catch (err) {
                                    setError(String(err));
                                } finally {
                                    setBusy(false);
                                }
                            }}
                        >
                            Create missing definitions
                        </button>
                    </div>
                )}
                <h3>Next.js tracking example</h3>
                <pre>
                    <code>{example}</code>
                </pre>
                <button
                    onClick={() =>
                        navigator.clipboard
                            .writeText(example)
                            .then(() => setMessage("Tracking example copied."))
                            .catch(() =>
                                setError(
                                    "Copy unavailable. Select and copy the example manually.",
                                ),
                            )
                    }
                >
                    Copy example
                </button>
            </section>
            <section className="panel">
                <h2>GA4 property configuration</h2>
                <div className="actions">
                    <label>
                        Definition type
                        <select
                            value={kind}
                            onChange={(e) => {
                                setKind(e.target.value);
                                setError("");
                            }}
                        >
                            <option value="dimensions">
                                Custom dimensions
                            </option>
                            <option value="metrics">Custom metrics</option>
                            <option value="key-events">Key events</option>
                        </select>
                    </label>
                    <button
                        onClick={() =>
                            load().catch((err) => setError(String(err)))
                        }
                    >
                        Refresh definitions
                    </button>
                </div>
                {!canEdit && (
                    <p className="notice">
                        Reporting is available. Reconnect Google with
                        administration access to change definitions.
                    </p>
                )}
                {definitions.length === 0 && (
                    <p>No definitions configured for this type.</p>
                )}
                <div className="table-scroll">
                    <table>
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Parameter / event</th>
                                <th>Scope / unit</th>
                                {kind === "key-events" && <th>Action</th>}
                            </tr>
                        </thead>
                        <tbody>
                            {definitions.map((d) => (
                                <tr key={d.name}>
                                    <td>{d.displayName ?? d.eventName}</td>
                                    <td>{d.parameterName ?? d.eventName}</td>
                                    <td>
                                        {d.scope ??
                                            d.measurementUnit ??
                                            "Key event"}
                                    </td>
                                    {kind === "key-events" && (
                                        <td>
                                            <button
                                                disabled={!canEdit || busy}
                                                onClick={async () => {
                                                    if (
                                                        !window.confirm(
                                                            `Stop marking ${d.eventName} as a key event?`,
                                                        )
                                                    )
                                                        return;
                                                    try {
                                                        await api(
                                                            `/websites/${website.id}/key-events/delete`,
                                                            "POST",
                                                            {
                                                                name: d.name,
                                                                confirmed: true,
                                                            },
                                                        );
                                                        await load();
                                                    } catch (err) {
                                                        setError(String(err));
                                                    }
                                                }}
                                            >
                                                Remove key event
                                            </button>
                                        </td>
                                    )}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <h3>
                    Create{" "}
                    {kind === "key-events"
                        ? "key event"
                        : kind === "metrics"
                          ? "custom metric"
                          : "custom dimension"}
                </h3>
                <form
                    key={kind}
                    onSubmit={async (e) => {
                        e.preventDefault();
                        const form = new FormData(e.currentTarget);
                        if (
                            !window.confirm(
                                "Create this definition in the linked Google Analytics property? Registration is not retroactive.",
                            )
                        )
                            return;
                        setBusy(true);
                        try {
                            await api(
                                `/websites/${website.id}/definitions/${kind}`,
                                "POST",
                                {
                                    parameterName: form.get("parameter"),
                                    eventName: form.get("parameter"),
                                    displayName: form.get("display") ?? "",
                                    measurementUnit:
                                        form.get("unit") ?? "STANDARD",
                                    confirmed: true,
                                },
                            );
                            setMessage(
                                "Definition created and verified with Google.",
                            );
                            await load();
                        } catch (err) {
                            setError(String(err));
                        } finally {
                            setBusy(false);
                        }
                    }}
                >
                    <label>
                        {kind === "key-events"
                            ? "Event name"
                            : "Parameter name"}
                        <input
                            name="parameter"
                            pattern="[A-Za-z][A-Za-z0-9_]{0,39}"
                            required
                        />
                    </label>
                    {kind !== "key-events" && (
                        <label>
                            Display name
                            <input name="display" maxLength={82} required />
                        </label>
                    )}
                    {kind === "metrics" && (
                        <label>
                            Unit
                            <select name="unit">
                                <option>STANDARD</option>
                                <option>CURRENCY</option>
                                <option>SECONDS</option>
                                <option>MILLISECONDS</option>
                            </select>
                        </label>
                    )}
                    <button disabled={!canEdit || busy}>
                        Review and create
                    </button>
                </form>
            </section>
        </>
    );
}

export function WorkspaceSettings({
    business,
    website,
    refresh,
}: {
    business: Business;
    website: Website;
    refresh: () => Promise<void>;
}) {
    const [members, setMembers] = useState<{email: string; role: string}[]>([]);
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");
    const load = useCallback(async () => {
        if (business.role === "owner")
            setMembers(await api(`/businesses/${business.id}/members`));
    }, [business.id, business.role]);
    useEffect(() => {
        void load().catch((err) => setError(String(err)));
    }, [load]);
    return (
        <>
            {error && (
                <p className="notice error" role="alert">
                    {error}
                </p>
            )}
            {message && <p role="status">{message}</p>}
            {business.role === "owner" && (
                <section className="panel">
                    <h2>Business details</h2>
                    <form
                        onSubmit={async (e) => {
                            e.preventDefault();
                            try {
                                await api(`/businesses/${business.id}`, "PUT", {
                                    name: new FormData(e.currentTarget).get(
                                        "name",
                                    ),
                                });
                                await refresh();
                            } catch (err) {
                                setError(String(err));
                            }
                        }}
                    >
                        <label>
                            Name
                            <input
                                name="name"
                                defaultValue={business.name}
                                required
                            />
                        </label>
                        <button>Save business</button>
                    </form>
                    <h3>Members</h3>
                    {members.map((m) => (
                        <p key={m.email}>
                            {m.email} · {m.role}
                        </p>
                    ))}
                    <p>
                        Add an existing ADB account by email, change a role, or
                        remove access. The final owner cannot be removed.
                    </p>
                    <form
                        onSubmit={async (e) => {
                            e.preventDefault();
                            const form = new FormData(e.currentTarget);
                            try {
                                await api(
                                    `/businesses/${business.id}/members`,
                                    "PUT",
                                    {
                                        email: form.get("email"),
                                        role: form.get("role") || null,
                                    },
                                );
                                await load();
                                setMessage("Membership updated.");
                                await refresh();
                            } catch (err) {
                                setError(String(err));
                            }
                        }}
                    >
                        <label>
                            Account email
                            <input type="email" name="email" required />
                        </label>
                        <label>
                            Role
                            <select name="role">
                                <option value="viewer">Viewer</option>
                                <option value="admin">Admin</option>
                                <option value="owner">Owner</option>
                                <option value="">Remove membership</option>
                            </select>
                        </label>
                        <button>Update membership</button>
                    </form>
                </section>
            )}
            <section className="panel">
                <h2>Website settings</h2>
                <WebsiteForm
                    business={business}
                    website={website}
                    refresh={refresh}
                />
            </section>
            <section className="panel">
                <h2>Add another website</h2>
                <WebsiteForm business={business} refresh={refresh} />
            </section>
            <section className="panel">
                <h2>Create another business</h2>
                <CreateBusiness refresh={refresh} />
            </section>
        </>
    );
}

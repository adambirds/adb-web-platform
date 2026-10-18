"use client";
import {useCallback, useEffect, useState} from "react";
import {api, type Website} from "../../app/client";
type Definition = {
    name: string;
    parameterName?: string;
    displayName?: string;
    eventName?: string;
    measurementUnit?: string;
    scope?: string;
};
export function TrackingSettings({
    website,
    initialEvent = "",
}: {
    website: Website;
    initialEvent?: string;
}) {
    const [kind, setKind] = useState("key-events");
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
                    Open Websites and link a GA4 property before configuring
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
            <details className="settings-card settings-disclosure">
                <summary>Tracking plans & implementation</summary>
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
            </details>
            <section className="settings-card">
                <h2>Key events & custom definitions</h2>
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
                        Configuration permission was not granted to this
                        connection. Reauthorise it in Google accounts. Google
                        also requires Editor or Administrator access on this
                        property.
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
                            defaultValue={
                                kind === "key-events" ? initialEvent : ""
                            }
                            aria-label={
                                kind === "key-events"
                                    ? "Event name to configure"
                                    : "Parameter name to configure"
                            }
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

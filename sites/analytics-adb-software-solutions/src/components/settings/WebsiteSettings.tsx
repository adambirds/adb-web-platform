"use client";
import {useState} from "react";
import {ArrowPathIcon, GlobeAltIcon} from "@heroicons/react/24/outline";
import {api, initialDates, type Business, type Website} from "../../app/client";
import {useResource} from "../experience/useResource";
import {WebsiteForm} from "./WorkspaceForms";
import type {Connection} from "./IntegrationSettings";
type Inventory = {
    ga4: {property: string; displayName: string}[];
    gsc: {siteUrl: string; permissionLevel: string}[];
};
export function WebsiteSettings({
    website,
    business,
    refresh,
}: {
    website: Website;
    business: Business;
    refresh: () => Promise<void>;
}) {
    const [error, setError] = useState(""),
        [message, setMessage] = useState(""),
        [busy, setBusy] = useState(false),
        [connection, setConnection] = useState(0),
        [inventory, setInventory] = useState<Inventory | null>(null);
    const {data: accounts} = useResource<Connection[]>(
        `/businesses/${business.id}/connections`,
    );
    const {data: jobs, reload} = useResource<
        {id: number; status: string; progress: number; error_code: string}[]
    >(`/websites/${website.id}/sync`, 10000);
    const running = jobs?.some((job) =>
        ["queued", "running", "retrying"].includes(job.status),
    );
    return (
        <div className="settings-sections">
            {error && (
                <p role="alert" className="error-state">
                    {error}
                </p>
            )}
            {message && (
                <p role="status" className="data-notice">
                    {message}
                </p>
            )}
            <section className="settings-card">
                <div className="settings-card-title">
                    <span className="settings-symbol">
                        <GlobeAltIcon />
                    </span>
                    <div>
                        <h2>{website.domain}</h2>
                        <p>
                            {website.name} · {website.timezone} ·{" "}
                            {website.is_active
                                ? "Collecting reports"
                                : "Collection paused"}
                        </p>
                    </div>
                </div>
                <div className="provider-settings-grid">
                    {(["ga4", "gsc"] as const).map((provider) => {
                        const prop = website.providers.find(
                            (item) => item.provider === provider,
                        );
                        const account = accounts?.find(
                            (item) => item.id === prop?.connection_id,
                        );
                        const healthIssue =
                            prop?.error_code ||
                            (account && account.status !== "connected"
                                ? "Reconnect required"
                                : account &&
                                    !account.scopes.some((scope) =>
                                        scope.endsWith(
                                            provider === "ga4"
                                                ? "/analytics.readonly"
                                                : "/webmasters.readonly",
                                        ),
                                    )
                                  ? "Reporting permission missing"
                                  : "");
                        return (
                            <div className="provider-settings" key={provider}>
                                <span className="eyebrow">
                                    {provider === "ga4"
                                        ? "GOOGLE ANALYTICS 4"
                                        : "SEARCH CONSOLE"}
                                </span>
                                <h3>
                                    {prop
                                        ? "Property connected"
                                        : "Not connected"}
                                </h3>
                                <p className="property-id">
                                    {prop?.external_id ??
                                        "Add this provider through website discovery or advanced linking."}
                                </p>
                                {prop && (
                                    <>
                                        <span
                                            className={`health-pill ${healthIssue ? "warning" : "healthy"}`}
                                        >
                                            {healthIssue
                                                ? healthIssue.replaceAll(
                                                      "_",
                                                      " ",
                                                  )
                                                : "Ready to sync"}
                                        </span>
                                        <p>
                                            Last sync:{" "}
                                            {prop.last_synced_at
                                                ? new Date(
                                                      prop.last_synced_at,
                                                  ).toLocaleString("en-GB")
                                                : "Awaiting first report"}
                                        </p>
                                        <details className="settings-disclosure">
                                            <summary>
                                                Unlink this property
                                            </summary>
                                            <p>
                                                Removes its stored reports from
                                                this website. The Google account
                                                and other websites remain
                                                connected.
                                            </p>
                                            <button
                                                className="button destructive"
                                                disabled={busy}
                                                onClick={async () => {
                                                    if (
                                                        !window.confirm(
                                                            "Unlink this property and remove its synchronised reports?",
                                                        )
                                                    )
                                                        return;
                                                    setBusy(true);
                                                    try {
                                                        await api(
                                                            `/websites/${website.id}/properties/${provider}`,
                                                            "DELETE",
                                                            {confirmed: true},
                                                        );
                                                        await refresh();
                                                    } catch (err) {
                                                        setError(String(err));
                                                    } finally {
                                                        setBusy(false);
                                                    }
                                                }}
                                            >
                                                Confirm unlink
                                            </button>
                                        </details>
                                    </>
                                )}
                            </div>
                        );
                    })}
                </div>
            </section>
            <section className="settings-card settings-sync-card">
                <div>
                    <h2>Always collecting, even when you’re away</h2>
                    <p>
                        Scheduled collection runs every six hours for active
                        websites. Access tokens refresh automatically in the
                        background. The timezone comes from the linked Google
                        property.
                    </p>
                    {jobs?.slice(0, 2).map((job) => (
                        <p className="sync-job-status" key={job.id}>
                            <span
                                className={`status-dot ${["running", "queued", "retrying"].includes(job.status) ? "working" : ""}`}
                            />
                            {job.status.replaceAll("_", " ")} · {job.progress}%{" "}
                            {job.error_code &&
                                `· ${job.error_code.replaceAll("_", " ")}`}
                        </p>
                    ))}
                </div>
                <button
                    className="button"
                    disabled={busy || running || !website.providers.length}
                    onClick={async () => {
                        setBusy(true);
                        setError("");
                        try {
                            const queued = await api<{id: number}[]>(
                                `/websites/${website.id}/sync`,
                                "POST",
                                initialDates(),
                            );
                            setMessage(
                                queued.length
                                    ? "Synchronisation queued. Your reports will update in the background."
                                    : "No connected properties could be queued. Review Google accounts and property permissions.",
                            );
                            reload();
                        } catch (err) {
                            setError(String(err));
                        } finally {
                            setBusy(false);
                        }
                    }}
                >
                    <ArrowPathIcon />
                    {running ? "Sync in progress" : "Sync latest reports"}
                </button>
            </section>
            <section className="settings-card">
                <h2>Website details</h2>
                <p>Keep its display name and collection status up to date.</p>
                <div className="advanced-tools">
                    <WebsiteForm
                        business={business}
                        website={website}
                        refresh={refresh}
                    />
                </div>
            </section>
            <details className="settings-card settings-disclosure">
                <summary>Advanced property linking</summary>
                <p>
                    Choose specific properties when automatic discovery cannot
                    pair them. Linking does not change Google configuration.
                </p>
                <label>
                    Google account
                    <select
                        aria-label="Google account for linking"
                        value={connection}
                        onChange={(event) => {
                            setConnection(Number(event.target.value));
                            setInventory(null);
                        }}
                    >
                        <option value={0}>Choose a connected account</option>
                        {accounts
                            ?.filter(
                                (account) => account.status === "connected",
                            )
                            .map((account) => (
                                <option key={account.id} value={account.id}>
                                    {account.email}
                                </option>
                            ))}
                    </select>
                </label>
                <button
                    className="button"
                    disabled={!connection || busy}
                    onClick={async () => {
                        setBusy(true);
                        try {
                            setInventory(
                                await api(
                                    `/connections/${connection}/properties`,
                                ),
                            );
                        } catch (err) {
                            setError(String(err));
                        } finally {
                            setBusy(false);
                        }
                    }}
                >
                    Find properties
                </button>
                {inventory &&
                    (["ga4", "gsc"] as const).map((provider) => (
                        <form
                            key={provider}
                            onSubmit={async (event) => {
                                event.preventDefault();
                                const form = new FormData(event.currentTarget);
                                setBusy(true);
                                try {
                                    await api(
                                        `/websites/${website.id}/properties/${provider}`,
                                        "PUT",
                                        {
                                            connection_id: connection,
                                            external_id: form.get("property"),
                                            search_type:
                                                form.get("search_type") ??
                                                "web",
                                        },
                                    );
                                    await refresh();
                                    setMessage(
                                        "Property linked. Initial reports are being prepared.",
                                    );
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
                                <select name="property" required>
                                    {provider === "ga4"
                                        ? inventory.ga4.map((prop) => (
                                              <option
                                                  key={prop.property}
                                                  value={prop.property}
                                              >
                                                  {prop.displayName} ·{" "}
                                                  {prop.property}
                                              </option>
                                          ))
                                        : inventory.gsc.map((prop) => (
                                              <option
                                                  key={prop.siteUrl}
                                                  value={prop.siteUrl}
                                              >
                                                  {prop.siteUrl} ·{" "}
                                                  {prop.permissionLevel}
                                              </option>
                                          ))}
                                </select>
                            </label>
                            {provider === "gsc" && (
                                <label>
                                    Search type
                                    <select name="search_type">
                                        {[
                                            "web",
                                            "image",
                                            "video",
                                            "news",
                                            "discover",
                                            "googleNews",
                                        ].map((value) => (
                                            <option key={value}>{value}</option>
                                        ))}
                                    </select>
                                </label>
                            )}
                            <button
                                className="button"
                                disabled={
                                    busy ||
                                    website.providers.some(
                                        (prop) => prop.provider === provider,
                                    )
                                }
                            >
                                Link{" "}
                                {provider === "ga4"
                                    ? "Analytics"
                                    : "Search Console"}
                            </button>
                        </form>
                    ))}
            </details>
        </div>
    );
}

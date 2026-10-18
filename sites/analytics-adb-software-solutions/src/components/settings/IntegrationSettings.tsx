"use client";
import {useCallback, useEffect, useState} from "react";
import {
    ArrowPathIcon,
    CheckCircleIcon,
    ExclamationTriangleIcon,
    LinkIcon,
} from "@heroicons/react/24/outline";
import {api, type Business} from "../../app/client";
export type Connection = {
    id: number;
    email: string;
    status: string;
    scopes: string[];
    error_code: string;
    last_validated_at?: string | null;
    last_refreshed_at?: string | null;
    expires_at?: string | null;
    refresh_retry_at?: string | null;
    refresh_failures?: number;
};
export const GOOGLE_SCOPES = [
    "analytics.readonly",
    "webmasters.readonly",
    "analytics.edit",
];
export function missingPermissions(connection: Connection) {
    return GOOGLE_SCOPES.filter(
        (scope) =>
            !connection.scopes.some((value) => value.endsWith("/" + scope)),
    );
}
export function IntegrationSettings({
    business,
    refresh,
}: {
    business: Business;
    refresh: () => Promise<void>;
}) {
    const [accounts, setAccounts] = useState<Connection[] | null>(null),
        [error, setError] = useState(""),
        [busy, setBusy] = useState<number | null>(null);
    const load = useCallback(
        async () =>
            setAccounts(
                await api<Connection[]>(
                    `/businesses/${business.id}/connections`,
                ),
            ),
        [business.id],
    );
    useEffect(() => {
        setAccounts(null);
        void load().catch((err) => setError(String(err)));
    }, [load]);
    const connect = async (connection?: Connection) => {
        setBusy(connection?.id ?? 0);
        setError("");
        try {
            const value = await api<{url: string}>(
                `/businesses/${business.id}/oauth`,
                "POST",
                {
                    return_to: "settings",
                    ...(connection ? {connection_id: connection.id} : {}),
                },
            );
            window.location.assign(value.url);
        } catch (err) {
            setError(String(err));
            setBusy(null);
        }
    };
    return (
        <div className="settings-sections">
            <section className="settings-card settings-connect-card">
                <span className="settings-symbol">
                    <LinkIcon />
                </span>
                <div>
                    <p className="eyebrow">
                        ONE CONNECTION. EVERYTHING IN SYNC.
                    </p>
                    <h2>Your Google accounts</h2>
                    <p>
                        Read Analytics and Search Console, and manage supported
                        GA4 events and definitions with one consent. Every
                        configuration change still needs your confirmation.
                    </p>
                    <div className="permission-summary">
                        <span>
                            <CheckCircleIcon /> Analytics reports
                        </span>
                        <span>
                            <CheckCircleIcon /> Search performance
                        </span>
                        <span>
                            <CheckCircleIcon /> Confirmed GA4 configuration
                        </span>
                    </div>
                </div>
                <button
                    className="button primary"
                    disabled={busy !== null}
                    onClick={() => void connect()}
                >
                    Connect Google
                </button>
            </section>
            {error && (
                <div className="error-state" role="alert">
                    <strong>We couldn’t complete that action</strong>
                    <p>{error}</p>
                    <button
                        className="button"
                        onClick={() => {
                            setError("");
                            void load().catch((err) => setError(String(err)));
                        }}
                    >
                        Try again
                    </button>
                </div>
            )}
            {accounts === null && !error && (
                <p className="data-notice" role="status">
                    Checking your connected accounts…
                </p>
            )}
            {accounts?.length === 0 && (
                <section className="settings-card settings-empty">
                    <LinkIcon />
                    <h3>A single connection brings it together</h3>
                    <p>
                        Connect Google to discover your websites. Access tokens
                        refresh securely in the background, even when you’re
                        signed out.
                    </p>
                </section>
            )}
            <div className="account-settings-grid">
                {accounts?.map((account) => {
                    const missing = missingPermissions(account),
                        reconnect = account.status !== "connected",
                        retrying = Boolean(account.refresh_retry_at),
                        limited = missing.length > 0;
                    const affected = business.websites.filter((site) =>
                        site.providers.some(
                            (prop) => prop.connection_id === account.id,
                        ),
                    );
                    return (
                        <section
                            className="settings-card google-account-card"
                            key={account.id}
                        >
                            <div className="settings-card-title">
                                <span className="account-initial">
                                    {account.email.slice(0, 1).toUpperCase() ||
                                        "G"}
                                </span>
                                <div>
                                    <h3>{account.email || "Google account"}</h3>
                                    <span
                                        className={`health-pill ${reconnect || limited ? "warning" : retrying ? "pending" : "healthy"}`}
                                    >
                                        {reconnect
                                            ? account.status === "disconnected"
                                                ? "Disconnected"
                                                : "Reconnect required"
                                            : limited
                                              ? "Permissions incomplete"
                                              : retrying
                                                ? "Retry scheduled"
                                                : "Connected"}
                                    </span>
                                </div>
                            </div>
                            <p>
                                {reconnect
                                    ? "Google access needs your attention. Existing reports are retained; reconnect this same account to resume collection."
                                    : retrying
                                      ? "Google could not refresh access temporarily. We’ll retry automatically; you don’t need to reconnect for a temporary outage."
                                      : "Access refreshes automatically. Scheduled reporting does not depend on you being signed in."}
                            </p>
                            {limited && !reconnect && (
                                <div className="data-notice warning">
                                    This connection predates the current
                                    consent. Reauthorise once to grant the
                                    missing permissions; available reporting
                                    continues.
                                </div>
                            )}
                            <dl className="account-facts">
                                <div>
                                    <dt>Linked websites</dt>
                                    <dd>{affected.length}</dd>
                                </div>
                                <div>
                                    <dt>Last token refresh</dt>
                                    <dd>
                                        {account.last_refreshed_at
                                            ? new Date(
                                                  account.last_refreshed_at,
                                              ).toLocaleString("en-GB")
                                            : "Not recorded yet"}
                                    </dd>
                                </div>
                                {account.expires_at && (
                                    <div>
                                        <dt>Access token valid until</dt>
                                        <dd>
                                            {new Date(
                                                account.expires_at,
                                            ).toLocaleString("en-GB")}
                                        </dd>
                                    </div>
                                )}
                                {account.refresh_retry_at && (
                                    <div>
                                        <dt>Next retry</dt>
                                        <dd>
                                            {new Date(
                                                account.refresh_retry_at,
                                            ).toLocaleString("en-GB")}
                                        </dd>
                                    </div>
                                )}
                            </dl>
                            <div className="permission-checks">
                                {GOOGLE_SCOPES.map((scope, i) => (
                                    <span
                                        key={scope}
                                        className={
                                            missing.includes(scope)
                                                ? "missing"
                                                : ""
                                        }
                                    >
                                        {missing.includes(scope) ? (
                                            <ExclamationTriangleIcon />
                                        ) : (
                                            <CheckCircleIcon />
                                        )}
                                        {
                                            [
                                                "Analytics reporting",
                                                "Search Console reporting",
                                                "GA4 configuration",
                                            ][i]
                                        }
                                    </span>
                                ))}
                            </div>
                            <details className="settings-disclosure">
                                <summary>Permissions & linked websites</summary>
                                <p>
                                    OAuth consent allows the application to
                                    request these actions. Google also checks
                                    your role on each property: Editor or
                                    Administrator is required for supported GA4
                                    configuration writes.
                                </p>
                                {affected.length ? (
                                    <ul>
                                        {affected.map((site) => (
                                            <li key={site.id}>{site.domain}</li>
                                        ))}
                                    </ul>
                                ) : (
                                    <p>
                                        No websites currently use this
                                        connection.
                                    </p>
                                )}
                                <p>
                                    Connection status: {account.status}.{" "}
                                    {account.error_code &&
                                        `Last issue: ${account.error_code.replaceAll("_", " ")}.`}
                                </p>
                            </details>
                            <div className="settings-card-actions">
                                <button
                                    className={`button ${reconnect || limited ? "primary" : ""}`}
                                    disabled={busy !== null}
                                    onClick={() => void connect(account)}
                                >
                                    <ArrowPathIcon />
                                    {reconnect
                                        ? "Reconnect account"
                                        : limited
                                          ? "Reauthorise account"
                                          : "Renew Google consent"}
                                </button>
                                {account.status !== "disconnected" && (
                                    <button
                                        className="text-link destructive"
                                        disabled={busy !== null}
                                        onClick={async () => {
                                            if (
                                                !window.confirm(
                                                    `Disconnect ${account.email || "this Google account"}? ${affected.length} linked websites will stop synchronising. Existing reports are retained.`,
                                                )
                                            )
                                                return;
                                            setBusy(account.id);
                                            setError("");
                                            try {
                                                await api(
                                                    `/connections/${account.id}/disconnect`,
                                                    "POST",
                                                );
                                                await load();
                                                await refresh();
                                            } catch (err) {
                                                setError(String(err));
                                            } finally {
                                                setBusy(null);
                                            }
                                        }}
                                    >
                                        Disconnect
                                    </button>
                                )}
                            </div>
                        </section>
                    );
                })}
            </div>
            <p className="settings-footnote">
                Offline access keeps scheduled reports running while credentials
                remain valid. Google can revoke or expire refresh tokens;
                reconnection may occasionally be necessary.{" "}
                <a href="/privacy">Privacy policy</a> ·{" "}
                <a href="/terms">Terms</a>
            </p>
        </div>
    );
}

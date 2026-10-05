"use client";

import { useLiveRefresh } from "@/contexts/LiveEventsContext";
import { Button, Card, Input, Select } from "@/components/ui";
import { fetchAPI } from "@/lib/api/fetch";
import { useCallback, useEffect, useState } from "react";
import { githubAPI } from "./contracts";
interface Connection {
    id: number;
    github_id: number;
    account: string;
    enabled: boolean;
    client_id: number | null;
    last_synced_at: string | null;
    sync_error: string;
}
interface Connections {
    rows: Connection[];
    clients: { id: number; name: string }[];
}
export function GitHubConnections({
    installURL,
    onChanged,
}: {
    installURL: string;
    onChanged: () => void;
}) {
    const [data, setData] = useState<Connections | null>(null);
    const [installation, setInstallation] = useState("");
    const [client, setClient] = useState("");
    const [error, setError] = useState("");
    const [notice, setNotice] = useState("");
    const [busy, setBusy] = useState(false);
    const load = useCallback(async () => {
        setData((await fetchAPI(`${githubAPI}/installations`)) as Connections);
    }, []);
    useEffect(() => {
        void load().catch((reason: Error) => setError(reason.message));
    }, [load]);
    useLiveRefresh(["github"], load);
    async function connect() {
        setBusy(true);
        setError("");
        try {
            await fetchAPI(`${githubAPI}/installations`, {
                method: "POST",
                body: JSON.stringify({
                    github_id: Number(installation),
                    client_id: client ? Number(client) : null,
                }),
            });
            await load();
            onChanged();
            setNotice(
                "Connected. Initial repository synchronisation is queued.",
            );
        } catch (reason) {
            setError(
                reason instanceof Error ? reason.message : "Unable to connect.",
            );
        } finally {
            setBusy(false);
        }
    }
    async function sync(id: number) {
        setBusy(true);
        setError("");
        try {
            await fetchAPI(`${githubAPI}/installations/${id}/sync`, {
                method: "POST",
            });
            setNotice("Synchronisation queued.");
        } catch (reason) {
            setError(
                reason instanceof Error
                    ? reason.message
                    : "Unable to synchronise.",
            );
        } finally {
            setBusy(false);
        }
    }
    return (
        <div className="space-y-4">
            <Card className="space-y-3 p-4">
                <h2 className="font-semibold text-white">
                    Connect a GitHub account
                </h2>
                <p className="text-sm text-slate-400">
                    Install the App on each organisation or personal account,
                    then approve its installation here. Choose who owns its
                    repository records before importing them.
                </p>
                {installURL ? (
                    <a
                        className="text-sm text-cyan-300"
                        href={installURL}
                        target="_blank"
                        rel="noreferrer"
                    >
                        Install GitHub App
                    </a>
                ) : null}
                <label className="block text-sm text-slate-300">
                    Installation ID
                    <Input
                        type="number"
                        min="1"
                        value={installation}
                        onChange={(event) =>
                            setInstallation(event.target.value)
                        }
                    />
                </label>
                <label className="block text-sm text-slate-300">
                    Repository ownership
                    <Select
                        value={client}
                        onChange={(event) => setClient(event.target.value)}
                    >
                        <option value="">Internal</option>
                        {data?.clients.map((row) => (
                            <option key={row.id} value={row.id}>
                                {row.name}
                            </option>
                        ))}
                    </Select>
                </label>
                <Button
                    disabled={busy || Number(installation) <= 0}
                    onClick={() => void connect()}
                >
                    Connect and synchronise
                </Button>
            </Card>
            {error ? (
                <p role="alert" className="text-sm text-red-300">
                    {error}
                </p>
            ) : null}
            {notice ? (
                <p role="status" className="text-sm text-emerald-300">
                    {notice}
                </p>
            ) : null}
            {data?.rows.map((row) => (
                <Card key={row.id} className="space-y-2 p-4">
                    <p className="font-medium text-white">
                        {row.account} ·{" "}
                        {row.enabled ? "Connected" : "Awaiting approval"}
                    </p>
                    <p className="text-xs text-slate-400">
                        Installation {row.github_id} · Last sync:{" "}
                        {row.last_synced_at
                            ? new Date(row.last_synced_at).toLocaleString(
                                  "en-GB",
                                  { timeZone: "Europe/London" },
                              )
                            : "Pending"}
                    </p>
                    {row.sync_error ? (
                        <p className="text-sm text-red-300">{row.sync_error}</p>
                    ) : null}
                    <Button
                        variant="secondary"
                        disabled={busy}
                        onClick={() => {
                            if (row.enabled) void sync(row.id);
                            else {
                                setInstallation(String(row.github_id));
                                setClient(
                                    row.client_id ? String(row.client_id) : "",
                                );
                            }
                        }}
                    >
                        {row.enabled
                            ? "Synchronise now"
                            : "Choose ownership and approve"}
                    </Button>
                </Card>
            ))}
        </div>
    );
}

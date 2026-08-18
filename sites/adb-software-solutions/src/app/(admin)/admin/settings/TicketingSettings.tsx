"use client";

import {
    Badge,
    Button,
    Card,
    DataError,
    DataLoading,
    Input,
    Select,
} from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

interface GraphConnection {
    id: number;
    name: string;
    tenant_id: string;
    client_id: string;
    authentication_method: string;
    credential_id: number | null;
    credential_name: string | null;
    enabled: boolean;
    last_verified_at: string | null;
    last_error: string;
}

interface Mailbox {
    id: number;
    email_address: string;
    display_name: string;
    graph_connection_id: number;
    graph_connection_name: string;
    brand_id: number;
    brand_name: string;
    purpose: string;
    default_queue_id: number;
    default_queue_name: string;
    enabled: boolean;
    last_successful_sync_at: string | null;
    last_error: string;
}

interface Brand {
    id: number;
    name: string;
    is_active: boolean;
}

interface Queue {
    id: number;
    name: string;
    brand_id: number | null;
    enabled: boolean;
}

interface Credential {
    id: number;
    name: string;
    ownership_type: string;
    credential_type: string | null;
}

function label(value: string) {
    return value
        .split("_")
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" ");
}

export function TicketingSettings() {
    const [connections, setConnections] = useState<GraphConnection[]>([]);
    const [mailboxes, setMailboxes] = useState<Mailbox[]>([]);
    const [brands, setBrands] = useState<Brand[]>([]);
    const [queues, setQueues] = useState<Queue[]>([]);
    const [credentials, setCredentials] = useState<Credential[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [connectionForm, setConnectionForm] = useState({
        name: "",
        tenant_id: "",
        client_id: "",
        authentication_method: "certificate",
        credential_id: "",
    });
    const [mailboxForm, setMailboxForm] = useState({
        graph_connection_id: "",
        email_address: "",
        display_name: "",
        brand_id: "",
        purpose: "support",
        default_queue_id: "",
    });

    const loadSettings = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            const [connectionRows, mailboxRows, brandRows, queueRows, credentialRows] =
                await Promise.all([
                    fetchAPI(AdminAPI.tickets.settings.graphConnections()),
                    fetchAPI(AdminAPI.tickets.settings.mailboxes()),
                    fetchAPI(AdminAPI.brands.list()),
                    fetchAPI(AdminAPI.tickets.queues()),
                    fetchAPI(AdminAPI.credentials.list()),
                ]);
            setConnections(connectionRows as GraphConnection[]);
            setMailboxes(mailboxRows as Mailbox[]);
            setBrands(brandRows as Brand[]);
            setQueues(queueRows as Queue[]);
            setCredentials(
                (credentialRows as Credential[]).filter(
                    (credential) => credential.ownership_type === "internal",
                ),
            );
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "Unable to load ticketing settings.",
            );
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        void loadSettings();
    }, [loadSettings]);

    const availableQueues = useMemo(() => {
        const brandId = Number(mailboxForm.brand_id);
        if (!brandId) return [];
        return queues.filter((queue) => queue.enabled && (!queue.brand_id || queue.brand_id === brandId));
    }, [mailboxForm.brand_id, queues]);

    async function createConnection(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        try {
            setIsSaving(true);
            setError(null);
            await fetchAPI(AdminAPI.tickets.settings.graphConnections(), {
                method: "POST",
                body: JSON.stringify({
                    ...connectionForm,
                    credential_id: connectionForm.credential_id
                        ? Number(connectionForm.credential_id)
                        : null,
                }),
            });
            setConnectionForm({
                name: "",
                tenant_id: "",
                client_id: "",
                authentication_method: "certificate",
                credential_id: "",
            });
            await loadSettings();
        } catch (saveError) {
            setError(saveError instanceof Error ? saveError.message : "Unable to save Graph connection.");
        } finally {
            setIsSaving(false);
        }
    }

    async function createMailbox(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        try {
            setIsSaving(true);
            setError(null);
            await fetchAPI(AdminAPI.tickets.settings.mailboxes(), {
                method: "POST",
                body: JSON.stringify({
                    ...mailboxForm,
                    graph_connection_id: Number(mailboxForm.graph_connection_id),
                    brand_id: Number(mailboxForm.brand_id),
                    default_queue_id: Number(mailboxForm.default_queue_id),
                }),
            });
            setMailboxForm({
                graph_connection_id: "",
                email_address: "",
                display_name: "",
                brand_id: "",
                purpose: "support",
                default_queue_id: "",
            });
            await loadSettings();
        } catch (saveError) {
            setError(saveError instanceof Error ? saveError.message : "Unable to save mailbox.");
        } finally {
            setIsSaving(false);
        }
    }

    if (isLoading) return <DataLoading label="Loading platform settings..." />;

    return (
        <div className="space-y-6">
            {error ? <DataError message={error} onRetry={() => void loadSettings()} /> : null}

            <Card className="p-5">
                <div className="max-w-3xl">
                    <h2 className="text-base font-semibold text-white">Microsoft Graph</h2>
                    <p className="mt-2 text-sm leading-6 text-slate-400">
                        Configure tenant/application connections once, then attach as many shared or
                        user mailboxes as required. Secret material remains in the platform credential
                        store rather than being entered directly into ticketing settings.
                    </p>
                </div>

                <div className="mt-5 grid gap-3 xl:grid-cols-2">
                    {connections.map((connection) => (
                        <div key={connection.id} className="rounded-xl border border-slate-800 bg-slate-950 p-4">
                            <div className="flex items-start justify-between gap-3">
                                <div>
                                    <div className="font-medium text-slate-200">{connection.name}</div>
                                    <div className="mt-1 text-xs text-slate-500">
                                        Tenant {connection.tenant_id} · Client {connection.client_id}
                                    </div>
                                </div>
                                <Badge>{connection.enabled ? "Enabled" : "Disabled"}</Badge>
                            </div>
                            <div className="mt-3 text-xs text-slate-500">
                                {label(connection.authentication_method)}
                                {connection.credential_name
                                    ? ` · ${connection.credential_name}`
                                    : " · No credential linked"}
                            </div>
                            {connection.last_error ? (
                                <div className="mt-3 rounded-lg border border-red-950 bg-red-950/20 p-3 text-xs text-red-300">
                                    {connection.last_error}
                                </div>
                            ) : null}
                        </div>
                    ))}
                </div>

                <form onSubmit={createConnection} className="mt-6 rounded-xl border border-slate-800 p-4">
                    <h3 className="text-sm font-semibold text-white">Add Graph application</h3>
                    <div className="mt-4 grid gap-3 lg:grid-cols-2 xl:grid-cols-3">
                        <Input
                            required
                            value={connectionForm.name}
                            onChange={(event) =>
                                setConnectionForm((current) => ({ ...current, name: event.target.value }))
                            }
                            placeholder="Connection name"
                        />
                        <Input
                            required
                            value={connectionForm.tenant_id}
                            onChange={(event) =>
                                setConnectionForm((current) => ({
                                    ...current,
                                    tenant_id: event.target.value,
                                }))
                            }
                            placeholder="Microsoft tenant ID"
                        />
                        <Input
                            required
                            value={connectionForm.client_id}
                            onChange={(event) =>
                                setConnectionForm((current) => ({
                                    ...current,
                                    client_id: event.target.value,
                                }))
                            }
                            placeholder="Application client ID"
                        />
                        <Select
                            value={connectionForm.authentication_method}
                            onChange={(event) =>
                                setConnectionForm((current) => ({
                                    ...current,
                                    authentication_method: event.target.value,
                                }))
                            }
                        >
                            <option value="certificate">Certificate</option>
                            <option value="client_secret">Client secret</option>
                            <option value="delegated">Delegated OAuth</option>
                        </Select>
                        <Select
                            value={connectionForm.credential_id}
                            onChange={(event) =>
                                setConnectionForm((current) => ({
                                    ...current,
                                    credential_id: event.target.value,
                                }))
                            }
                        >
                            <option value="">No credential yet</option>
                            {credentials.map((credential) => (
                                <option key={credential.id} value={credential.id}>
                                    {credential.name}
                                    {credential.credential_type ? ` (${credential.credential_type})` : ""}
                                </option>
                            ))}
                        </Select>
                        <Button type="submit" disabled={isSaving}>
                            Add connection
                        </Button>
                    </div>
                </form>
            </Card>

            <Card className="p-5">
                <div>
                    <h2 className="text-base font-semibold text-white">Ticket mailboxes</h2>
                    <p className="mt-2 text-sm text-slate-400">
                        Each mailbox has an explicit brand, purpose and default queue. Routing rules can
                        become more granular without changing the mailbox identity.
                    </p>
                </div>

                <div className="mt-5 divide-y divide-slate-800 overflow-hidden rounded-xl border border-slate-800">
                    {mailboxes.length === 0 ? (
                        <div className="p-5 text-sm text-slate-500">No mailboxes configured yet.</div>
                    ) : (
                        mailboxes.map((mailbox) => (
                            <div
                                key={mailbox.id}
                                className="grid gap-3 bg-slate-950/60 p-4 lg:grid-cols-[minmax(0,1fr)_200px_200px_120px] lg:items-center"
                            >
                                <div>
                                    <div className="font-medium text-slate-200">
                                        {mailbox.display_name || mailbox.email_address}
                                    </div>
                                    <div className="mt-1 text-xs text-slate-500">
                                        {mailbox.email_address} · {mailbox.graph_connection_name}
                                    </div>
                                </div>
                                <div className="text-sm text-slate-400">{mailbox.brand_name}</div>
                                <div className="text-sm text-slate-400">{mailbox.default_queue_name}</div>
                                <Badge>{mailbox.enabled ? label(mailbox.purpose) : "Disabled"}</Badge>
                            </div>
                        ))
                    )}
                </div>

                <form onSubmit={createMailbox} className="mt-6 rounded-xl border border-slate-800 p-4">
                    <h3 className="text-sm font-semibold text-white">Add mailbox</h3>
                    <div className="mt-4 grid gap-3 lg:grid-cols-2 xl:grid-cols-3">
                        <Select
                            required
                            value={mailboxForm.graph_connection_id}
                            onChange={(event) =>
                                setMailboxForm((current) => ({
                                    ...current,
                                    graph_connection_id: event.target.value,
                                }))
                            }
                        >
                            <option value="">Select Graph connection</option>
                            {connections
                                .filter((connection) => connection.enabled)
                                .map((connection) => (
                                    <option key={connection.id} value={connection.id}>
                                        {connection.name}
                                    </option>
                                ))}
                        </Select>
                        <Input
                            required
                            type="email"
                            value={mailboxForm.email_address}
                            onChange={(event) =>
                                setMailboxForm((current) => ({
                                    ...current,
                                    email_address: event.target.value,
                                }))
                            }
                            placeholder="support@example.com"
                        />
                        <Input
                            value={mailboxForm.display_name}
                            onChange={(event) =>
                                setMailboxForm((current) => ({
                                    ...current,
                                    display_name: event.target.value,
                                }))
                            }
                            placeholder="Display name"
                        />
                        <Select
                            required
                            value={mailboxForm.brand_id}
                            onChange={(event) =>
                                setMailboxForm((current) => ({
                                    ...current,
                                    brand_id: event.target.value,
                                    default_queue_id: "",
                                }))
                            }
                        >
                            <option value="">Select brand</option>
                            {brands
                                .filter((brand) => brand.is_active)
                                .map((brand) => (
                                    <option key={brand.id} value={brand.id}>
                                        {brand.name}
                                    </option>
                                ))}
                        </Select>
                        <Select
                            required
                            value={mailboxForm.default_queue_id}
                            onChange={(event) =>
                                setMailboxForm((current) => ({
                                    ...current,
                                    default_queue_id: event.target.value,
                                }))
                            }
                            disabled={!mailboxForm.brand_id}
                        >
                            <option value="">Select default queue</option>
                            {availableQueues.map((queue) => (
                                <option key={queue.id} value={queue.id}>
                                    {queue.name}
                                </option>
                            ))}
                        </Select>
                        <Select
                            value={mailboxForm.purpose}
                            onChange={(event) =>
                                setMailboxForm((current) => ({
                                    ...current,
                                    purpose: event.target.value,
                                }))
                            }
                        >
                            <option value="support">Support</option>
                            <option value="sales">Sales</option>
                            <option value="accounts">Accounts</option>
                            <option value="operations">Operations</option>
                            <option value="general">General</option>
                        </Select>
                        <Button type="submit" disabled={isSaving || connections.length === 0}>
                            Add mailbox
                        </Button>
                    </div>
                </form>
            </Card>
        </div>
    );
}

"use client";

import { Button, ButtonLink, DataLoading, Input, Select, Textarea } from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

interface ClientFormState {
    name: string;
    company: string;
    email: string;
    phone: string;
    address: string;
    city: string;
    state: string;
    country: string;
    postal_code: string;
    status: "active" | "inactive" | "archived";
    notes: string;
}

interface ClientResponse extends ClientFormState {
    id: number;
}

const EMPTY_FORM: ClientFormState = {
    name: "",
    company: "",
    email: "",
    phone: "",
    address: "",
    city: "",
    state: "",
    country: "United Kingdom",
    postal_code: "",
    status: "active",
    notes: "",
};

const labelClasses = "space-y-1.5 text-sm font-medium text-slate-300";

export function ClientForm({ clientId }: { clientId?: number }) {
    const router = useRouter();
    const [form, setForm] = useState<ClientFormState>(EMPTY_FORM);
    const [isLoading, setIsLoading] = useState(Boolean(clientId));
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!clientId) return;

        async function loadClient() {
            try {
                setIsLoading(true);
                setError(null);
                const client = (await fetchAPI(AdminAPI.clients.get(clientId!))) as ClientResponse;
                setForm({
                    name: client.name,
                    company: client.company,
                    email: client.email,
                    phone: client.phone,
                    address: client.address,
                    city: client.city,
                    state: client.state,
                    country: client.country,
                    postal_code: client.postal_code,
                    status: client.status,
                    notes: client.notes,
                });
            } catch (loadError) {
                setError(
                    loadError instanceof Error ? loadError.message : "Unable to load client details.",
                );
            } finally {
                setIsLoading(false);
            }
        }

        void loadClient();
    }, [clientId]);

    function update<K extends keyof ClientFormState>(key: K, value: ClientFormState[K]) {
        setForm((current) => ({ ...current, [key]: value }));
    }

    async function save(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setIsSaving(true);
        setError(null);

        try {
            const client = (await fetchAPI(
                clientId ? AdminAPI.clients.update(clientId) : AdminAPI.clients.create(),
                {
                    method: clientId ? "PUT" : "POST",
                    body: JSON.stringify(form),
                },
            )) as ClientResponse;
            router.push(`/admin/clients/${client.id}`);
            router.refresh();
        } catch (saveError) {
            setError(
                saveError instanceof Error ? saveError.message : "Unable to save the client account.",
            );
        } finally {
            setIsSaving(false);
        }
    }

    if (isLoading) return <DataLoading label="Loading client details..." />;

    return (
        <form onSubmit={(event) => void save(event)} className="space-y-6">
            {error ? (
                <div
                    role="alert"
                    className="rounded-lg border border-red-900/70 bg-red-950/40 px-4 py-3 text-sm text-red-200"
                >
                    {error}
                </div>
            ) : null}

            <div className="grid gap-5 md:grid-cols-2">
                <label className={labelClasses}>
                    <span>Account contact name</span>
                    <Input
                        value={form.name}
                        onChange={(event) => update("name", event.target.value)}
                        autoComplete="name"
                        required
                        maxLength={200}
                    />
                </label>
                <label className={labelClasses}>
                    <span>Company</span>
                    <Input
                        value={form.company}
                        onChange={(event) => update("company", event.target.value)}
                        autoComplete="organization"
                        maxLength={200}
                    />
                </label>
                <label className={labelClasses}>
                    <span>Primary email</span>
                    <Input
                        type="email"
                        value={form.email}
                        onChange={(event) => update("email", event.target.value)}
                        autoComplete="email"
                        required
                    />
                </label>
                <label className={labelClasses}>
                    <span>Primary phone</span>
                    <Input
                        type="tel"
                        value={form.phone}
                        onChange={(event) => update("phone", event.target.value)}
                        autoComplete="tel"
                        maxLength={20}
                    />
                </label>
                <label className={labelClasses}>
                    <span>Status</span>
                    <Select
                        value={form.status}
                        onChange={(event) =>
                            update(
                                "status",
                                event.target.value as ClientFormState["status"],
                            )
                        }
                    >
                        <option value="active">Active</option>
                        <option value="inactive">Inactive</option>
                        <option value="archived">Archived</option>
                    </Select>
                </label>
            </div>

            <div className="border-t border-slate-800 pt-6">
                <h2 className="text-sm font-semibold text-white">Address</h2>
                <div className="mt-4 grid gap-5 md:grid-cols-2">
                    <label className={`${labelClasses} md:col-span-2`}>
                        <span>Street address</span>
                        <Textarea
                            value={form.address}
                            onChange={(event) => update("address", event.target.value)}
                            rows={3}
                            autoComplete="street-address"
                        />
                    </label>
                    <label className={labelClasses}>
                        <span>City</span>
                        <Input
                            value={form.city}
                            onChange={(event) => update("city", event.target.value)}
                            autoComplete="address-level2"
                            maxLength={100}
                        />
                    </label>
                    <label className={labelClasses}>
                        <span>County / state / region</span>
                        <Input
                            value={form.state}
                            onChange={(event) => update("state", event.target.value)}
                            autoComplete="address-level1"
                            maxLength={100}
                        />
                    </label>
                    <label className={labelClasses}>
                        <span>Postcode</span>
                        <Input
                            value={form.postal_code}
                            onChange={(event) => update("postal_code", event.target.value)}
                            autoComplete="postal-code"
                            maxLength={20}
                        />
                    </label>
                    <label className={labelClasses}>
                        <span>Country</span>
                        <Input
                            value={form.country}
                            onChange={(event) => update("country", event.target.value)}
                            autoComplete="country-name"
                            maxLength={100}
                        />
                    </label>
                </div>
            </div>

            <div className="border-t border-slate-800 pt-6">
                <label className={labelClasses}>
                    <span>Internal account notes</span>
                    <Textarea
                        value={form.notes}
                        onChange={(event) => update("notes", event.target.value)}
                        rows={6}
                        placeholder="Commercial context, preferences, account history or other internal notes."
                    />
                </label>
            </div>

            <div className="flex flex-wrap gap-3 border-t border-slate-800 pt-6">
                <Button type="submit" disabled={isSaving}>
                    {isSaving ? "Saving..." : clientId ? "Save changes" : "Create client"}
                </Button>
                <ButtonLink
                    href={clientId ? `/admin/clients/${clientId}` : "/admin/clients"}
                    variant="outline"
                >
                    Cancel
                </ButtonLink>
            </div>
        </form>
    );
}

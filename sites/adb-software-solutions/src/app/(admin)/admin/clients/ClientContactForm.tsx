"use client";

import { Button, ButtonLink, DataLoading, Input } from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

interface ClientContactFormState {
    name: string;
    email: string;
    phone: string;
    role: string;
    is_active: boolean;
    is_primary: boolean;
    is_billing: boolean;
    is_technical: boolean;
}

interface ClientContactResponse extends ClientContactFormState {
    id: number;
}

const EMPTY_FORM: ClientContactFormState = {
    name: "",
    email: "",
    phone: "",
    role: "",
    is_active: true,
    is_primary: false,
    is_billing: false,
    is_technical: false,
};

const labelClasses = "space-y-1.5 text-sm font-medium text-slate-300";
const responsibilityClasses =
    "flex items-start gap-3 rounded-lg border border-slate-800 bg-slate-950/40 p-4";

export function ClientContactForm({
    clientId,
    contactId,
}: {
    clientId: number;
    contactId?: number;
}) {
    const router = useRouter();
    const [form, setForm] = useState<ClientContactFormState>(EMPTY_FORM);
    const [isLoading, setIsLoading] = useState(Boolean(contactId));
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!contactId) return;

        async function loadContact() {
            try {
                setIsLoading(true);
                setError(null);
                const contact = (await fetchAPI(
                    AdminAPI.clients.contacts.get(clientId, contactId!),
                )) as ClientContactResponse;
                setForm({
                    name: contact.name,
                    email: contact.email,
                    phone: contact.phone,
                    role: contact.role,
                    is_active: contact.is_active,
                    is_primary: contact.is_primary,
                    is_billing: contact.is_billing,
                    is_technical: contact.is_technical,
                });
            } catch (loadError) {
                setError(
                    loadError instanceof Error
                        ? loadError.message
                        : "Unable to load contact details.",
                );
            } finally {
                setIsLoading(false);
            }
        }

        void loadContact();
    }, [clientId, contactId]);

    function update<K extends keyof ClientContactFormState>(
        key: K,
        value: ClientContactFormState[K],
    ) {
        setForm((current) => ({ ...current, [key]: value }));
    }

    async function persist(nextForm: ClientContactFormState) {
        setIsSaving(true);
        setError(null);

        try {
            await fetchAPI(
                contactId
                    ? AdminAPI.clients.contacts.update(clientId, contactId)
                    : AdminAPI.clients.contacts.create(clientId),
                {
                    method: contactId ? "PUT" : "POST",
                    body: JSON.stringify(nextForm),
                },
            );
            router.push(`/admin/clients/${clientId}`);
            router.refresh();
        } catch (saveError) {
            setError(
                saveError instanceof Error ? saveError.message : "Unable to save the contact.",
            );
        } finally {
            setIsSaving(false);
        }
    }

    async function save(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        await persist(form);
    }

    async function changeActiveState(isActive: boolean) {
        const nextForm = {
            ...form,
            is_active: isActive,
            ...(!isActive
                ? { is_primary: false, is_billing: false, is_technical: false }
                : {}),
        };
        setForm(nextForm);
        await persist(nextForm);
    }

    if (isLoading) return <DataLoading label="Loading contact details..." />;

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
                    <span>Name</span>
                    <Input
                        value={form.name}
                        onChange={(event) => update("name", event.target.value)}
                        autoComplete="name"
                        required
                        maxLength={200}
                    />
                </label>
                <label className={labelClasses}>
                    <span>Role / job title</span>
                    <Input
                        value={form.role}
                        onChange={(event) => update("role", event.target.value)}
                        autoComplete="organization-title"
                        maxLength={100}
                        placeholder="e.g. Director, Project Manager, CTO"
                    />
                </label>
                <label className={labelClasses}>
                    <span>Email</span>
                    <Input
                        type="email"
                        value={form.email}
                        onChange={(event) => update("email", event.target.value)}
                        autoComplete="email"
                        required
                    />
                </label>
                <label className={labelClasses}>
                    <span>Phone</span>
                    <Input
                        type="tel"
                        value={form.phone}
                        onChange={(event) => update("phone", event.target.value)}
                        autoComplete="tel"
                        maxLength={20}
                    />
                </label>
            </div>

            <div className="border-t border-slate-800 pt-6">
                <div>
                    <h2 className="text-sm font-semibold text-white">Responsibilities</h2>
                    <p className="mt-1 text-xs leading-5 text-slate-500">
                        These flags help the platform choose the right person for account, billing and
                        technical conversations. A client can have several billing or technical contacts,
                        but only one primary contact.
                    </p>
                </div>
                <div className="mt-4 grid gap-3 lg:grid-cols-3">
                    <label className={responsibilityClasses}>
                        <input
                            type="checkbox"
                            checked={form.is_primary}
                            onChange={(event) => update("is_primary", event.target.checked)}
                            disabled={!form.is_active || isSaving}
                            className="mt-0.5 h-4 w-4 rounded border-slate-600 bg-slate-900 text-cyan-500"
                        />
                        <span>
                            <span className="block text-sm font-medium text-slate-200">Primary</span>
                            <span className="mt-1 block text-xs leading-5 text-slate-500">
                                Main person for this client account.
                            </span>
                        </span>
                    </label>
                    <label className={responsibilityClasses}>
                        <input
                            type="checkbox"
                            checked={form.is_billing}
                            onChange={(event) => update("is_billing", event.target.checked)}
                            disabled={!form.is_active || isSaving}
                            className="mt-0.5 h-4 w-4 rounded border-slate-600 bg-slate-900 text-cyan-500"
                        />
                        <span>
                            <span className="block text-sm font-medium text-slate-200">Billing</span>
                            <span className="mt-1 block text-xs leading-5 text-slate-500">
                                Appropriate for accounts and invoice conversations.
                            </span>
                        </span>
                    </label>
                    <label className={responsibilityClasses}>
                        <input
                            type="checkbox"
                            checked={form.is_technical}
                            onChange={(event) => update("is_technical", event.target.checked)}
                            disabled={!form.is_active || isSaving}
                            className="mt-0.5 h-4 w-4 rounded border-slate-600 bg-slate-900 text-cyan-500"
                        />
                        <span>
                            <span className="block text-sm font-medium text-slate-200">Technical</span>
                            <span className="mt-1 block text-xs leading-5 text-slate-500">
                                Appropriate for technical and project discussions.
                            </span>
                        </span>
                    </label>
                </div>
            </div>

            {contactId ? (
                <div className="border-t border-slate-800 pt-6">
                    <div className="flex flex-col gap-3 rounded-lg border border-slate-800 bg-slate-950/40 p-4 sm:flex-row sm:items-center sm:justify-between">
                        <div>
                            <h2 className="text-sm font-semibold text-white">Contact status</h2>
                            <p className="mt-1 text-xs leading-5 text-slate-500">
                                {form.is_active
                                    ? "Deactivate this contact when they no longer work with the client. Historical links are retained."
                                    : "This contact is inactive and will not hold primary, billing or technical responsibilities."}
                            </p>
                        </div>
                        <Button
                            type="button"
                            variant={form.is_active ? "destructive" : "secondary"}
                            disabled={isSaving}
                            onClick={() => void changeActiveState(!form.is_active)}
                        >
                            {form.is_active ? "Deactivate contact" : "Reactivate contact"}
                        </Button>
                    </div>
                </div>
            ) : null}

            <div className="flex flex-wrap gap-3 border-t border-slate-800 pt-6">
                <Button type="submit" disabled={isSaving || !form.is_active}>
                    {isSaving ? "Saving..." : contactId ? "Save changes" : "Create contact"}
                </Button>
                <ButtonLink href={`/admin/clients/${clientId}`} variant="outline">
                    Cancel
                </ButtonLink>
            </div>
        </form>
    );
}

"use client";

import { Button, ButtonLink, DataLoading, Input, Select, Textarea } from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

interface Lookup {
    id: number;
    name: string;
}

interface Brand extends Lookup {
    is_active: boolean;
}

interface LeadFormState {
    name: string;
    email: string;
    phone: string;
    company: string;
    brand_id: number | null;
    status_id: number | null;
    source_id: number | null;
    message: string;
    notes: string;
}

interface LeadResponse extends LeadFormState {
    id: number;
}

interface LeadOptions {
    statuses: Lookup[];
    sources: Lookup[];
}

const EMPTY_FORM: LeadFormState = {
    name: "",
    email: "",
    phone: "",
    company: "",
    brand_id: null,
    status_id: null,
    source_id: null,
    message: "",
    notes: "",
};

const labelClasses = "space-y-1.5 text-sm font-medium text-slate-300";

function optionalId(value: string) {
    return value ? Number(value) : null;
}

export function LeadForm({ leadId }: { leadId?: number }) {
    const router = useRouter();
    const [form, setForm] = useState<LeadFormState>(EMPTY_FORM);
    const [brands, setBrands] = useState<Brand[]>([]);
    const [options, setOptions] = useState<LeadOptions>({ statuses: [], sources: [] });
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function load() {
            try {
                setIsLoading(true);
                setError(null);
                const [brandRows, optionRows, lead] = await Promise.all([
                    fetchAPI(AdminAPI.brands.list()) as Promise<Brand[]>,
                    fetchAPI(AdminAPI.leads.options()) as Promise<LeadOptions>,
                    leadId
                        ? (fetchAPI(AdminAPI.leads.get(leadId)) as Promise<LeadResponse>)
                        : Promise.resolve(null),
                ]);
                setBrands(brandRows);
                setOptions(optionRows);
                if (lead) {
                    setForm({
                        name: lead.name,
                        email: lead.email,
                        phone: lead.phone,
                        company: lead.company,
                        brand_id: lead.brand_id,
                        status_id: lead.status_id,
                        source_id: lead.source_id,
                        message: lead.message,
                        notes: lead.notes,
                    });
                }
            } catch (loadError) {
                setError(loadError instanceof Error ? loadError.message : "Unable to load lead details.");
            } finally {
                setIsLoading(false);
            }
        }

        void load();
    }, [leadId]);

    function update<K extends keyof LeadFormState>(key: K, value: LeadFormState[K]) {
        setForm((current) => ({ ...current, [key]: value }));
    }

    async function save(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setIsSaving(true);
        setError(null);

        try {
            const lead = (await fetchAPI(
                leadId ? AdminAPI.leads.update(leadId) : AdminAPI.leads.create(),
                {
                    method: leadId ? "PUT" : "POST",
                    body: JSON.stringify(form),
                },
            )) as LeadResponse;
            router.push(`/admin/leads/${lead.id}`);
            router.refresh();
        } catch (saveError) {
            setError(saveError instanceof Error ? saveError.message : "Unable to save the lead.");
        } finally {
            setIsSaving(false);
        }
    }

    if (isLoading) return <DataLoading label="Loading lead details..." />;

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
                    <span>Contact name</span>
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
                <label className={labelClasses}>
                    <span>Brand</span>
                    <Select
                        value={form.brand_id ?? ""}
                        onChange={(event) => update("brand_id", optionalId(event.target.value))}
                    >
                        <option value="">Unassigned</option>
                        {brands.map((brand) => (
                            <option key={brand.id} value={brand.id}>
                                {brand.name}{brand.is_active ? "" : " (inactive)"}
                            </option>
                        ))}
                    </Select>
                </label>
                <label className={labelClasses}>
                    <span>Pipeline status</span>
                    <Select
                        value={form.status_id ?? ""}
                        onChange={(event) => update("status_id", optionalId(event.target.value))}
                    >
                        <option value="">Unassigned</option>
                        {options.statuses.map((status) => (
                            <option key={status.id} value={status.id}>
                                {status.name}
                            </option>
                        ))}
                    </Select>
                </label>
                <label className={labelClasses}>
                    <span>Source</span>
                    <Select
                        value={form.source_id ?? ""}
                        onChange={(event) => update("source_id", optionalId(event.target.value))}
                    >
                        <option value="">Unknown</option>
                        {options.sources.map((source) => (
                            <option key={source.id} value={source.id}>
                                {source.name}
                            </option>
                        ))}
                    </Select>
                </label>
            </div>

            <div className="border-t border-slate-800 pt-6">
                <label className={labelClasses}>
                    <span>Original enquiry / opportunity</span>
                    <Textarea
                        value={form.message}
                        onChange={(event) => update("message", event.target.value)}
                        rows={6}
                        placeholder="What is the prospect asking for?"
                    />
                </label>
            </div>

            <div className="border-t border-slate-800 pt-6">
                <label className={labelClasses}>
                    <span>Internal notes</span>
                    <Textarea
                        value={form.notes}
                        onChange={(event) => update("notes", event.target.value)}
                        rows={6}
                        placeholder="Follow-ups, qualification notes, commercial context and next steps."
                    />
                </label>
            </div>

            <div className="flex flex-wrap gap-3 border-t border-slate-800 pt-6">
                <Button type="submit" disabled={isSaving}>
                    {isSaving ? "Saving..." : leadId ? "Save changes" : "Create lead"}
                </Button>
                <ButtonLink href={leadId ? `/admin/leads/${leadId}` : "/admin/leads"} variant="outline">
                    Cancel
                </ButtonLink>
            </div>
        </form>
    );
}

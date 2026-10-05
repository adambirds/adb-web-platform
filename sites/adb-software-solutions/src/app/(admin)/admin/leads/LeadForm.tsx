"use client";

import {
    Button,
    ButtonLink,
    DataLoading,
    Input,
    Select,
    Textarea,
} from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useMemo, useState } from "react";

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

export function LeadForm({
    leadId,
    onSaved,
    onCancel,
}: {
    leadId?: number;
    onSaved?: (lead: LeadResponse) => void;
    onCancel?: () => void;
}) {
    const router = useRouter();
    const { hasPermission } = useAuth();
    const [form, setForm] = useState<LeadFormState>(EMPTY_FORM);
    const [brands, setBrands] = useState<Brand[]>([]);
    const [options, setOptions] = useState<LeadOptions>({
        statuses: [],
        sources: [],
    });
    const [addingOption, setAddingOption] = useState<
        "status" | "source" | null
    >(null);
    const [optionName, setOptionName] = useState("");
    const [optionOutcome, setOptionOutcome] = useState<"open" | "won" | "lost">(
        "open",
    );
    const [optionSaving, setOptionSaving] = useState(false);
    const [optionError, setOptionError] = useState<string | null>(null);
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
                        ? (fetchAPI(
                              AdminAPI.leads.get(leadId),
                          ) as Promise<LeadResponse>)
                        : Promise.resolve(null),
                ]);
                setBrands(brandRows);
                setOptions(optionRows);
                if (!lead) {
                    const initialStatus = optionRows.statuses.find(
                        (status) => status.name.toLowerCase() === "new",
                    );
                    setForm({
                        ...EMPTY_FORM,
                        status_id: initialStatus?.id ?? null,
                    });
                }
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
                setError(
                    loadError instanceof Error
                        ? loadError.message
                        : "Unable to load lead details.",
                );
            } finally {
                setIsLoading(false);
            }
        }

        void load();
    }, [leadId]);

    const visibleBrands = useMemo(
        () =>
            brands.filter(
                (brand) => brand.is_active || brand.id === form.brand_id,
            ),
        [brands, form.brand_id],
    );

    function update<K extends keyof LeadFormState>(
        key: K,
        value: LeadFormState[K],
    ) {
        setForm((current) => ({ ...current, [key]: value }));
    }

    function startOption(kind: "status" | "source") {
        setAddingOption(kind);
        setOptionName("");
        setOptionOutcome("open");
        setOptionError(null);
    }

    async function createOption() {
        if (!addingOption || !optionName.trim()) return;
        setOptionSaving(true);
        setOptionError(null);
        try {
            const created = (await fetchAPI(
                addingOption === "status"
                    ? AdminAPI.leads.createStatus()
                    : AdminAPI.leads.createSource(),
                {
                    method: "POST",
                    body: JSON.stringify({
                        name: optionName.trim(),
                        ...(addingOption === "status"
                            ? { outcome: optionOutcome }
                            : {}),
                    }),
                },
            )) as Lookup;
            setOptions((current) => ({
                ...current,
                ...(addingOption === "status"
                    ? { statuses: [...current.statuses, created] }
                    : {
                          sources: [...current.sources, created].sort((a, b) =>
                              a.name.localeCompare(b.name),
                          ),
                      }),
            }));
            update(
                addingOption === "status" ? "status_id" : "source_id",
                created.id,
            );
            setAddingOption(null);
        } catch (failure) {
            setOptionError(
                failure instanceof Error
                    ? failure.message
                    : "Unable to add this option.",
            );
        } finally {
            setOptionSaving(false);
        }
    }

    async function save(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setIsSaving(true);
        setError(null);

        try {
            const lead = (await fetchAPI(
                leadId
                    ? AdminAPI.leads.update(leadId)
                    : AdminAPI.leads.create(),
                {
                    method: leadId ? "PUT" : "POST",
                    body: JSON.stringify(form),
                },
            )) as LeadResponse;
            if (onSaved) {
                onSaved(lead);
            } else {
                router.push(`/admin/leads/${lead.id}`);
                router.refresh();
            }
        } catch (saveError) {
            setError(
                saveError instanceof Error
                    ? saveError.message
                    : "Unable to save the lead.",
            );
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
                        onChange={(event) =>
                            update("company", event.target.value)
                        }
                        autoComplete="organization"
                        maxLength={200}
                    />
                </label>
                <label className={labelClasses}>
                    <span>Email</span>
                    <Input
                        type="email"
                        value={form.email}
                        onChange={(event) =>
                            update("email", event.target.value)
                        }
                        autoComplete="email"
                        required
                    />
                </label>
                <label className={labelClasses}>
                    <span>Phone</span>
                    <Input
                        type="tel"
                        value={form.phone}
                        onChange={(event) =>
                            update("phone", event.target.value)
                        }
                        autoComplete="tel"
                        maxLength={20}
                    />
                </label>
                <label className={labelClasses}>
                    <span>Brand</span>
                    <Select
                        value={form.brand_id ?? ""}
                        onChange={(event) =>
                            update("brand_id", optionalId(event.target.value))
                        }
                    >
                        <option value="">Unassigned</option>
                        {visibleBrands.map((brand) => (
                            <option key={brand.id} value={brand.id}>
                                {brand.name}
                                {brand.is_active ? "" : " (inactive)"}
                            </option>
                        ))}
                    </Select>
                </label>
                <div className={labelClasses}>
                    <div className="flex items-center justify-between">
                        <label htmlFor="lead-status">Sales stage</label>
                        {hasPermission("crm.add_leadstatus") ? (
                            <Button
                                type="button"
                                variant="ghost"
                                disabled={isSaving || optionSaving}
                                onClick={() => startOption("status")}
                            >
                                Add stage
                            </Button>
                        ) : null}
                    </div>
                    <Select
                        id="lead-status"
                        value={form.status_id ?? ""}
                        onChange={(event) =>
                            update("status_id", optionalId(event.target.value))
                        }
                    >
                        <option value="">No sales stage</option>
                        {options.statuses.map((status) => (
                            <option key={status.id} value={status.id}>
                                {status.name}
                            </option>
                        ))}
                    </Select>
                    <p className="text-xs font-normal text-slate-400">
                        Where this lead is in your sales process, from New to
                        Won or Lost.
                    </p>
                </div>
                <div className={labelClasses}>
                    <div className="flex items-center justify-between">
                        <label htmlFor="lead-source">Source</label>
                        {hasPermission("crm.add_leadsource") ? (
                            <Button
                                type="button"
                                variant="ghost"
                                disabled={isSaving || optionSaving}
                                onClick={() => startOption("source")}
                            >
                                Add source
                            </Button>
                        ) : null}
                    </div>
                    <Select
                        id="lead-source"
                        value={form.source_id ?? ""}
                        onChange={(event) =>
                            update("source_id", optionalId(event.target.value))
                        }
                    >
                        <option value="">Unknown</option>
                        {options.sources.map((source) => (
                            <option key={source.id} value={source.id}>
                                {source.name}
                            </option>
                        ))}
                    </Select>
                    <p className="text-xs font-normal text-slate-400">
                        How the lead found or contacted you.
                    </p>
                </div>
            </div>

            {addingOption ? (
                <fieldset
                    disabled={optionSaving || isSaving}
                    className="space-y-4 rounded-lg border border-slate-800 bg-slate-900 p-4"
                >
                    <legend className="px-2 text-sm text-white">
                        {addingOption === "status"
                            ? "Add sales stage"
                            : "Add lead source"}
                    </legend>
                    <label className={labelClasses}>
                        <span>
                            {addingOption === "status"
                                ? "Stage name"
                                : "Source name"}
                        </span>
                        <Input
                            value={optionName}
                            onChange={(event) =>
                                setOptionName(event.target.value)
                            }
                            maxLength={100}
                        />
                    </label>
                    {addingOption === "status" ? (
                        <label className={labelClasses}>
                            <span>Outcome</span>
                            <Select
                                value={optionOutcome}
                                onChange={(event) =>
                                    setOptionOutcome(
                                        event.target.value as
                                            "open" | "won" | "lost",
                                    )
                                }
                            >
                                <option value="open">
                                    Open — still pursuing
                                </option>
                                <option value="won">
                                    Won — successful sale
                                </option>
                                <option value="lost">
                                    Lost — no longer pursuing
                                </option>
                            </Select>
                        </label>
                    ) : null}
                    <p className="text-xs text-slate-400">
                        This option will be available to everyone using Leads.
                    </p>
                    {optionError ? (
                        <p role="alert" className="text-sm text-red-300">
                            {optionError}
                        </p>
                    ) : null}
                    <div className="flex gap-2">
                        <Button
                            type="button"
                            disabled={!optionName.trim() || optionSaving}
                            onClick={() => void createOption()}
                        >
                            {optionSaving ? "Adding…" : "Add and select"}
                        </Button>
                        <Button
                            type="button"
                            variant="ghost"
                            onClick={() => setAddingOption(null)}
                        >
                            Cancel option
                        </Button>
                    </div>
                </fieldset>
            ) : null}

            <div className="border-t border-slate-800 pt-6">
                <label className={labelClasses}>
                    <span>Original enquiry / opportunity</span>
                    <Textarea
                        value={form.message}
                        onChange={(event) =>
                            update("message", event.target.value)
                        }
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
                        onChange={(event) =>
                            update("notes", event.target.value)
                        }
                        rows={6}
                        placeholder="Follow-ups, qualification notes, commercial context and next steps."
                    />
                </label>
            </div>

            <div className="flex flex-wrap gap-3 border-t border-slate-800 pt-6">
                <Button
                    type="submit"
                    disabled={isSaving || optionSaving || addingOption !== null}
                >
                    {isSaving
                        ? "Saving..."
                        : leadId
                          ? "Save changes"
                          : "Create lead"}
                </Button>
                {onCancel ? (
                    <Button
                        type="button"
                        variant="outline"
                        onClick={onCancel}
                        disabled={isSaving}
                    >
                        Cancel
                    </Button>
                ) : (
                    <ButtonLink
                        href={
                            leadId ? `/admin/leads/${leadId}` : "/admin/leads"
                        }
                        variant="outline"
                    >
                        Cancel
                    </ButtonLink>
                )}
            </div>
        </form>
    );
}

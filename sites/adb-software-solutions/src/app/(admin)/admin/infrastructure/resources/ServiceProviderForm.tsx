"use client";

import { Button, Card, Input, Select, Textarea } from "@/components/ui";
import { fetchAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";
import { useState, type FormEvent } from "react";

export interface ServiceProviderOption {
    id: number;
    name: string;
    slug: string;
    category: string;
    website_url: string;
    support_url: string;
    status_page_url: string;
    documentation_url: string;
    notes: string;
    is_active: boolean;
}

export function ServiceProviderForm({
    onCreated,
    onCancel,
    provider: existingProvider,
}: {
    onCreated: (provider: ServiceProviderOption) => void;
    onCancel: () => void;
    provider?: ServiceProviderOption;
}) {
    const [values, setValues] = useState({
        name: "",
        slug: "",
        category: "cloud",
        website_url: "",
        support_url: "",
        status_page_url: "",
        documentation_url: "",
        notes: "",
        is_active: true,
        ...existingProvider,
    });
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    function field(key: keyof typeof values, value: string) {
        setValues((current) => ({ ...current, [key]: value }));
    }
    async function submit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setSaving(true);
        setError(null);
        try {
            const savedProvider = (await fetchAPI(
                `${API_URL}/api/admin/infrastructure/service-providers${existingProvider ? `/${existingProvider.id}` : ""}`,
                {
                    method: existingProvider ? "PATCH" : "POST",
                    body: JSON.stringify({
                        ...values,
                        slug:
                            values.slug ||
                            values.name
                                .toLowerCase()
                                .replace(/[^a-z0-9]+/g, "-")
                                .replace(/^-|-$/g, ""),
                    }),
                },
            )) as ServiceProviderOption;
            onCreated(savedProvider);
        } catch (failure) {
            setError(
                failure instanceof Error
                    ? failure.message
                    : "Unable to save service provider.",
            );
        } finally {
            setSaving(false);
        }
    }
    return (
        <Card className="p-5">
            <form
                onSubmit={(event) => void submit(event)}
                className="space-y-4"
            >
                <h2 className="text-lg font-semibold text-white">
                    {existingProvider
                        ? "Edit service provider"
                        : "Add service provider"}
                </h2>
                <p className="text-sm text-slate-400">
                    Create the vendor once, then link its accounts to your
                    resources. Store secrets in Credentials.
                </p>
                {error ? (
                    <p role="alert" className="text-sm text-red-300">
                        {error}
                    </p>
                ) : null}
                <fieldset
                    disabled={saving}
                    className="grid gap-4 sm:grid-cols-2"
                >
                    <label>
                        Provider name
                        <Input
                            required
                            value={values.name}
                            onChange={(e) => field("name", e.target.value)}
                        />
                    </label>
                    <label>
                        Slug
                        <Input
                            value={values.slug}
                            placeholder="Generated from the name"
                            onChange={(e) => field("slug", e.target.value)}
                        />
                    </label>
                    <label>
                        Provider category
                        <Select
                            value={values.category}
                            onChange={(e) => field("category", e.target.value)}
                        >
                            {[
                                "cloud",
                                "hosting",
                                "registrar",
                                "dns",
                                "cdn",
                                "saas",
                                "source_control",
                                "monitoring",
                                "hardware",
                                "other",
                            ].map((value) => (
                                <option key={value} value={value}>
                                    {value.replaceAll("_", " ")}
                                </option>
                            ))}
                        </Select>
                    </label>
                    {(
                        [
                            ["website_url", "Website URL"],
                            ["support_url", "Support URL"],
                            ["status_page_url", "Status page URL"],
                            ["documentation_url", "Documentation URL"],
                        ] as const
                    ).map(([key, label]) => (
                        <label key={key}>
                            {label}
                            <Input
                                type="url"
                                value={values[key]}
                                onChange={(e) => field(key, e.target.value)}
                            />
                        </label>
                    ))}
                    <label className="sm:col-span-2">
                        Provider notes
                        <Textarea
                            value={values.notes}
                            onChange={(e) => field("notes", e.target.value)}
                        />
                    </label>
                    <label>
                        <input
                            type="checkbox"
                            checked={values.is_active}
                            onChange={(e) =>
                                setValues((current) => ({
                                    ...current,
                                    is_active: e.target.checked,
                                }))
                            }
                        />{" "}
                        Active provider
                    </label>
                </fieldset>
                <div className="flex gap-2">
                    <Button type="submit" disabled={saving}>
                        {saving
                            ? "Saving…"
                            : existingProvider
                              ? "Save service provider"
                              : "Create service provider"}
                    </Button>
                    <Button
                        type="button"
                        variant="secondary"
                        disabled={saving}
                        onClick={onCancel}
                    >
                        Cancel
                    </Button>
                </div>
            </form>
        </Card>
    );
}

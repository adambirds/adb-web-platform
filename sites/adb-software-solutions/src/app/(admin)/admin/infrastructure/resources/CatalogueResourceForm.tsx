"use client";

import {
    Button,
    Card,
    DataLoading,
    Input,
    Select,
    Textarea,
} from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";
import { useEffect, useState, type FormEvent } from "react";
import {
    RESOURCE_CREATION,
    type CatalogueResourceType,
} from "./resourceCreation";
import {
    ServiceProviderForm,
    type ServiceProviderOption,
} from "./ServiceProviderForm";

interface Options {
    clients: { id: number; name: string }[];
    providers: ServiceProviderOption[];
}
const INITIAL_VALUES = {
    name: "",
    ownership_type: "internal",
    client_id: "",
    lifecycle_status: "active",
    environment: "not_applicable",
    criticality: "normal",
    description: "",
    provider_id: "",
    account_identifier: "",
    tenant_id: "",
    project_id: "",
    portal_url: "",
    default_region: "",
    support_plan: "",
    billing_reference: "",
};
type Values = typeof INITIAL_VALUES;
interface Detail {
    name: string;
    ownership_type: string;
    client_id: number | null;
    lifecycle_status: string;
    environment: string;
    criticality: string;
    description: string;
    provider_id?: number;
    provider_name?: string;
    account_identifier?: string;
    tenant_id?: string;
    project_id?: string;
    portal_url?: string;
    default_region?: string;
    support_plan?: string;
    billing_reference?: string;
}

export function CatalogueResourceForm({
    type,
    editResourceId,
    onCreated,
    onSaved,
    onCancel,
}: {
    type: CatalogueResourceType;
    editResourceId?: number;
    onCreated?: (id: number) => void;
    onSaved?: () => void;
    onCancel: () => void;
}) {
    const { hasPermission } = useAuth();
    const [options, setOptions] = useState<Options>({
        clients: [],
        providers: [],
    });
    const [values, setValues] = useState<Values>(INITIAL_VALUES);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showProvider, setShowProvider] = useState(false);
    const isAccount = type === "provider_account";
    useEffect(() => {
        let active = true;
        setLoading(true);
        setError(null);
        setValues(INITIAL_VALUES);
        async function load() {
            try {
                const [loadedOptions, detail] = await Promise.all([
                    fetchAPI(
                        `${API_URL}/api/admin/infrastructure/catalogue-options`,
                    ) as Promise<Options>,
                    editResourceId
                        ? (fetchAPI(
                              `${API_URL}/api/admin/infrastructure/${isAccount ? "provider-accounts" : "resources"}/${editResourceId}`,
                          ) as Promise<Detail>)
                        : Promise.resolve(null),
                ]);
                if (!active) return;
                if (detail) {
                    const next = { ...INITIAL_VALUES };
                    for (const key of Object.keys(next) as (keyof Values)[]) {
                        const value = detail[key as keyof Detail];
                        if (value != null) next[key] = String(value);
                    }
                    setValues(next);
                    if (
                        detail.provider_id &&
                        !loadedOptions.providers.some(
                            (provider) => provider.id === detail.provider_id,
                        )
                    ) {
                        loadedOptions.providers.push({
                            id: detail.provider_id,
                            name: detail.provider_name ?? "Current provider",
                            slug: "",
                            category: "other",
                            website_url: "",
                            support_url: "",
                            status_page_url: "",
                            documentation_url: "",
                            notes: "",
                            is_active: false,
                        });
                    }
                }
                setOptions(loadedOptions);
            } catch (failure) {
                if (active)
                    setError(
                        failure instanceof Error
                            ? failure.message
                            : "Unable to load creation options.",
                    );
            } finally {
                if (active) setLoading(false);
            }
        }
        void load();
        return () => {
            active = false;
        };
    }, [editResourceId, isAccount, type]);
    function field(key: keyof Values, value: string) {
        setValues((current) => ({
            ...current,
            [key]: value,
            ...(key === "ownership_type" ? { client_id: "" } : {}),
        }));
    }
    async function submit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setSaving(true);
        setError(null);
        const common = {
            name: values.name,
            lifecycle_status: values.lifecycle_status,
            environment: values.environment,
            criticality: values.criticality,
            description: values.description,
        };
        const body = {
            ...common,
            ...(!editResourceId
                ? {
                      ownership_type: values.ownership_type,
                      client_id:
                          values.ownership_type === "client"
                              ? Number(values.client_id)
                              : null,
                  }
                : {}),
            ...(isAccount
                ? {
                      provider_id: Number(values.provider_id),
                      account_identifier: values.account_identifier,
                      tenant_id: values.tenant_id,
                      project_id: values.project_id,
                      portal_url: values.portal_url,
                      default_region: values.default_region,
                      support_plan: values.support_plan,
                      billing_reference: values.billing_reference,
                  }
                : !editResourceId
                  ? { resource_type: type }
                  : {}),
        };
        try {
            const result = (await fetchAPI(
                `${API_URL}/api/admin/infrastructure/${isAccount ? "provider-accounts" : "resources"}${editResourceId ? `/${editResourceId}` : ""}`,
                {
                    method: editResourceId ? "PATCH" : "POST",
                    body: JSON.stringify(body),
                },
            )) as { resource_id: number };
            if (editResourceId) onSaved?.();
            else onCreated?.(result.resource_id);
        } catch (failure) {
            setError(
                failure instanceof Error
                    ? failure.message
                    : "Unable to save resource.",
            );
        } finally {
            setSaving(false);
        }
    }
    if (loading) return <DataLoading label="Loading resource options..." />;
    if (showProvider)
        return (
            <ServiceProviderForm
                onCancel={() => setShowProvider(false)}
                onCreated={(provider) => {
                    setOptions((current) => ({
                        ...current,
                        providers: [...current.providers, provider],
                    }));
                    field("provider_id", String(provider.id));
                    setShowProvider(false);
                }}
            />
        );
    return (
        <Card className="p-5">
            <form
                onSubmit={(event) => void submit(event)}
                className="space-y-5"
            >
                <h2 className="text-lg font-semibold text-white">
                    {editResourceId ? "Edit" : "Create"}{" "}
                    {RESOURCE_CREATION[type].label.toLowerCase()}
                </h2>
                <p className="text-sm text-slate-400">
                    {isAccount
                        ? "Record the account’s vendor and identifiers. Link passwords, API tokens and private keys through Credentials."
                        : "Record ownership and lifecycle here, then add credentials, documentation and relationships in its workspace."}
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
                        Resource name
                        <Input
                            required
                            maxLength={200}
                            value={values.name}
                            onChange={(e) => field("name", e.target.value)}
                        />
                    </label>
                    <label>
                        Ownership
                        <Select
                            disabled={Boolean(editResourceId)}
                            value={values.ownership_type}
                            onChange={(e) =>
                                field("ownership_type", e.target.value)
                            }
                        >
                            <option value="internal">ADB Internal</option>
                            <option value="client">Client-owned</option>
                        </Select>
                    </label>
                    {values.ownership_type === "client" ? (
                        <label>
                            Client
                            <Select
                                required
                                disabled={Boolean(editResourceId)}
                                value={values.client_id}
                                onChange={(e) =>
                                    field("client_id", e.target.value)
                                }
                            >
                                <option value="">Choose a Client</option>
                                {options.clients.map((client) => (
                                    <option key={client.id} value={client.id}>
                                        {client.name}
                                    </option>
                                ))}
                            </Select>
                        </label>
                    ) : null}
                    {(
                        [
                            [
                                "lifecycle_status",
                                "Lifecycle",
                                [
                                    "planned",
                                    "active",
                                    "maintenance",
                                    "deprecated",
                                    "retired",
                                    "archived",
                                ],
                            ],
                            [
                                "environment",
                                "Environment",
                                [
                                    "production",
                                    "staging",
                                    "development",
                                    "testing",
                                    "shared",
                                    "not_applicable",
                                ],
                            ],
                            [
                                "criticality",
                                "Criticality",
                                ["low", "normal", "high", "critical"],
                            ],
                        ] as const
                    ).map(([key, label, choices]) => (
                        <label key={key}>
                            {label}
                            <Select
                                value={values[key]}
                                onChange={(e) => field(key, e.target.value)}
                            >
                                {choices.map((value) => (
                                    <option key={value} value={value}>
                                        {value.replaceAll("_", " ")}
                                    </option>
                                ))}
                            </Select>
                        </label>
                    ))}
                    {isAccount ? (
                        <>
                            <label>
                                Service provider
                                <Select
                                    required
                                    value={values.provider_id}
                                    onChange={(e) =>
                                        field("provider_id", e.target.value)
                                    }
                                >
                                    <option value="">
                                        Choose a service provider
                                    </option>
                                    {options.providers.map((provider) => (
                                        <option
                                            key={provider.id}
                                            value={provider.id}
                                        >
                                            {provider.name}
                                        </option>
                                    ))}
                                </Select>
                            </label>
                            {hasPermission(
                                "infrastructure.add_serviceprovider",
                            ) ? (
                                <Button
                                    type="button"
                                    variant="secondary"
                                    onClick={() => setShowProvider(true)}
                                >
                                    Add service provider
                                </Button>
                            ) : null}
                            {(
                                [
                                    [
                                        "account_identifier",
                                        "Account identifier",
                                    ],
                                    ["tenant_id", "Tenant ID"],
                                    ["project_id", "Project ID"],
                                    ["portal_url", "Provider portal URL"],
                                    ["default_region", "Default region"],
                                    ["support_plan", "Support plan"],
                                    ["billing_reference", "Billing reference"],
                                ] as const
                            ).map(([key, label]) => (
                                <label key={key}>
                                    {label}
                                    <Input
                                        type={
                                            key === "portal_url"
                                                ? "url"
                                                : "text"
                                        }
                                        value={values[key]}
                                        onChange={(e) =>
                                            field(key, e.target.value)
                                        }
                                    />
                                </label>
                            ))}
                        </>
                    ) : null}
                    <label className="sm:col-span-2">
                        Description
                        <Textarea
                            value={values.description}
                            onChange={(e) =>
                                field("description", e.target.value)
                            }
                        />
                    </label>
                </fieldset>
                <div className="flex gap-2">
                    <Button
                        type="submit"
                        disabled={saving || (isAccount && !values.provider_id)}
                    >
                        {saving
                            ? "Saving…"
                            : editResourceId
                              ? "Save resource"
                              : "Create resource"}
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

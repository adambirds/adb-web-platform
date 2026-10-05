"use client";

import {
    Button,
    Card,
    DataError,
    DataLoading,
    Input,
    Select,
    Textarea,
} from "@/components/ui";
import { fetchAPI } from "@/lib/api/fetch";
import {
    CredentialCreatePayload,
    CredentialDetail,
    CredentialField,
    CredentialOptions,
    CredentialOwnership,
    CredentialResourceLinkInput,
    CredentialStatus,
    CredentialType,
    CredentialUpdatePayload,
    CredentialVaultAPI,
} from "@/lib/api/credentialVault";
import { FormEvent, useEffect, useMemo, useState } from "react";

interface CredentialFormProps {
    credential?: CredentialDetail;
    initialClientId?: number;
    initialResourceId?: number;
    onSaved: (credential: CredentialDetail) => void;
    onCancel: () => void;
}

function localDateTimeValue(value: string | null): string {
    if (!value) return "";
    const date = new Date(value);
    const offset = date.getTimezoneOffset() * 60_000;
    return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

function apiDateTimeValue(value: string): string | null {
    if (!value) return null;
    return new Date(value).toISOString();
}

function resourceLabel(
    resource: CredentialOptions["resources"][number],
): string {
    const type = resource.resource_type.replaceAll("_", " ");
    return `${resource.name} · ${type} · ${resource.client_name || "ADB Internal"}`;
}

function initialValues(
    credential: CredentialDetail,
    fields: CredentialField[],
) {
    const values: Record<string, string> = {};
    for (const field of fields) {
        if (field.storage === "username")
            values[field.key] = credential.username;
        else if (field.storage === "url") values[field.key] = credential.url;
        else if (field.storage === "metadata")
            values[field.key] = credential.metadata[field.key] ?? "";
        else values[field.key] = "";
    }
    return values;
}

export function CredentialForm({
    credential,
    initialClientId,
    initialResourceId,
    onSaved,
    onCancel,
}: CredentialFormProps) {
    const isEditing = Boolean(credential);
    const [options, setOptions] = useState<CredentialOptions | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [saveError, setSaveError] = useState<string | null>(null);

    const [name, setName] = useState(credential?.name ?? "");
    const [credentialTypeId, setCredentialTypeId] = useState(
        credential?.credential_type_id
            ? String(credential.credential_type_id)
            : "",
    );
    const [ownershipType, setOwnershipType] = useState<CredentialOwnership>(
        credential?.ownership_type ?? (initialClientId ? "client" : "internal"),
    );
    const [clientId, setClientId] = useState(
        credential?.client_id
            ? String(credential.client_id)
            : initialClientId
              ? String(initialClientId)
              : "",
    );
    const [status, setStatus] = useState<CredentialStatus>(
        credential?.status ?? "active",
    );
    const [description, setDescription] = useState(
        credential?.description ?? "",
    );
    const [expiresAt, setExpiresAt] = useState(
        localDateTimeValue(credential?.expires_at ?? null),
    );
    const [values, setValues] = useState<Record<string, string>>({});
    const [clearSecretFields, setClearSecretFields] = useState<string[]>([]);
    const [resourceSearch, setResourceSearch] = useState("");
    const [resourceLinks, setResourceLinks] = useState<
        CredentialResourceLinkInput[]
    >(
        credential?.resource_links.map((link) => ({
            resource_id: link.resource_id,
            purpose: link.purpose,
            is_primary: link.is_primary,
        })) ?? (initialResourceId ? [{ resource_id: initialResourceId }] : []),
    );

    useEffect(() => {
        let cancelled = false;
        async function loadOptions() {
            try {
                setIsLoading(true);
                setLoadError(null);
                const loaded = (await fetchAPI(
                    CredentialVaultAPI.options(),
                )) as CredentialOptions;
                if (cancelled) return;
                setOptions(loaded);
                setCredentialTypeId(
                    (current) => current || String(loaded.types[0]?.id ?? ""),
                );
            } catch (error) {
                if (!cancelled) {
                    setLoadError(
                        error instanceof Error
                            ? error.message
                            : "Unable to load credential options.",
                    );
                }
            } finally {
                if (!cancelled) setIsLoading(false);
            }
        }
        void loadOptions();
        return () => {
            cancelled = true;
        };
    }, []);

    const selectedType = useMemo<CredentialType | null>(() => {
        if (!options) return null;
        return (
            options.types.find(
                (type) => type.id === Number(credentialTypeId),
            ) ?? null
        );
    }, [credentialTypeId, options]);

    useEffect(() => {
        if (!selectedType) return;
        if (credential) {
            setValues(initialValues(credential, selectedType.fields));
        } else {
            setValues((current) => {
                const next: Record<string, string> = {};
                for (const field of selectedType.fields)
                    next[field.key] = current[field.key] ?? "";
                return next;
            });
        }
        setClearSecretFields([]);
    }, [credential, selectedType]);

    const visibleResources = useMemo(() => {
        if (!options) return [];
        if (ownershipType === "internal") return options.resources;
        const selectedClientId = Number(clientId);
        return options.resources.filter(
            (resource) => resource.client_id === selectedClientId,
        );
    }, [clientId, options, ownershipType]);

    useEffect(() => {
        if (!options) return;
        const allowed = new Set(
            visibleResources.map((resource) => resource.id),
        );
        setResourceLinks((current) =>
            current.filter((link) => allowed.has(link.resource_id)),
        );
    }, [options, visibleResources]);

    const matchingResources = useMemo(() => {
        const query = resourceSearch.trim().toLowerCase();
        return visibleResources.filter((resource) =>
            resourceLabel(resource).toLowerCase().includes(query),
        );
    }, [resourceSearch, visibleResources]);

    function updateValue(fieldKey: string, value: string) {
        setValues((current) => ({ ...current, [fieldKey]: value }));
        if (value) {
            setClearSecretFields((current) =>
                current.filter((key) => key !== fieldKey),
            );
        }
    }

    function toggleResource(resourceId: number) {
        setResourceLinks((current) => {
            if (current.some((link) => link.resource_id === resourceId)) {
                return current.filter(
                    (link) => link.resource_id !== resourceId,
                );
            }
            return [
                ...current,
                {
                    resource_id: resourceId,
                    purpose: "",
                    is_primary: current.length === 0,
                },
            ];
        });
    }

    function updateResourceLink(
        resourceId: number,
        changes: Partial<CredentialResourceLinkInput>,
    ) {
        setResourceLinks((current) =>
            current.map((link) =>
                link.resource_id === resourceId
                    ? { ...link, ...changes }
                    : link,
            ),
        );
    }

    async function submit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!selectedType) {
            setSaveError("Choose a credential type.");
            return;
        }
        if (ownershipType === "client" && !clientId) {
            setSaveError("Choose the client that owns this credential.");
            return;
        }

        try {
            setIsSaving(true);
            setSaveError(null);
            let saved: CredentialDetail;
            if (credential) {
                const payload: CredentialUpdatePayload = {
                    name: name.trim(),
                    status,
                    description: description.trim(),
                    values,
                    clear_secret_fields: clearSecretFields,
                    resource_links: resourceLinks,
                    ...(expiresAt
                        ? { expires_at: apiDateTimeValue(expiresAt) }
                        : { clear_expires_at: true }),
                };
                saved = (await fetchAPI(
                    CredentialVaultAPI.update(credential.id),
                    {
                        method: "PUT",
                        body: JSON.stringify(payload),
                    },
                )) as CredentialDetail;
            } else {
                const payload: CredentialCreatePayload = {
                    name: name.trim(),
                    credential_type_id: selectedType.id,
                    ownership_type: ownershipType,
                    client_id:
                        ownershipType === "client" ? Number(clientId) : null,
                    status,
                    description: description.trim(),
                    expires_at: apiDateTimeValue(expiresAt),
                    values,
                    resource_links: resourceLinks,
                };
                saved = (await fetchAPI(CredentialVaultAPI.create(), {
                    method: "POST",
                    body: JSON.stringify(payload),
                })) as CredentialDetail;
            }
            onSaved(saved);
        } catch (error) {
            setSaveError(
                error instanceof Error
                    ? error.message
                    : "Unable to save this credential.",
            );
        } finally {
            setIsSaving(false);
        }
    }

    if (isLoading) return <DataLoading label="Loading credential editor..." />;
    if (loadError || !options) {
        return (
            <DataError
                message={loadError || "Credential options are unavailable."}
            />
        );
    }

    return (
        <form className="space-y-6" onSubmit={submit}>
            <Card className="p-5">
                <div className="grid gap-4 md:grid-cols-2">
                    <div className="md:col-span-2">
                        <label className="mb-2 block text-xs font-medium text-slate-400">
                            Name
                        </label>
                        <Input
                            value={name}
                            onChange={(event) => setName(event.target.value)}
                            required
                            disabled={isSaving}
                        />
                    </div>
                    <div>
                        <label className="mb-2 block text-xs font-medium text-slate-400">
                            Credential type
                        </label>
                        <Select
                            value={credentialTypeId}
                            onChange={(event) =>
                                setCredentialTypeId(event.target.value)
                            }
                            disabled={isEditing || isSaving}
                        >
                            {options.types.map((type) => (
                                <option key={type.id} value={type.id}>
                                    {type.name}
                                </option>
                            ))}
                        </Select>
                        {selectedType?.description ? (
                            <p className="mt-2 text-xs leading-5 text-slate-500">
                                {selectedType.description}
                            </p>
                        ) : null}
                    </div>
                    <div>
                        <label className="mb-2 block text-xs font-medium text-slate-400">
                            Status
                        </label>
                        <Select
                            value={status}
                            onChange={(event) =>
                                setStatus(
                                    event.target.value as CredentialStatus,
                                )
                            }
                            disabled={isSaving}
                        >
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                            <option value="archived">Archived</option>
                        </Select>
                    </div>
                    <div>
                        <label className="mb-2 block text-xs font-medium text-slate-400">
                            Ownership
                        </label>
                        <Select
                            value={ownershipType}
                            onChange={(event) => {
                                const next = event.target
                                    .value as CredentialOwnership;
                                setOwnershipType(next);
                                if (next === "internal") setClientId("");
                            }}
                            disabled={isEditing || isSaving}
                        >
                            <option value="internal">ADB Internal</option>
                            <option value="client">Client</option>
                        </Select>
                    </div>
                    <div>
                        <label className="mb-2 block text-xs font-medium text-slate-400">
                            Client
                        </label>
                        <Select
                            value={clientId}
                            onChange={(event) =>
                                setClientId(event.target.value)
                            }
                            disabled={
                                ownershipType !== "client" ||
                                isEditing ||
                                isSaving
                            }
                        >
                            <option value="">Choose client</option>
                            {options.clients.map((client) => (
                                <option key={client.id} value={client.id}>
                                    {client.name}
                                </option>
                            ))}
                        </Select>
                    </div>
                    <div>
                        <label className="mb-2 block text-xs font-medium text-slate-400">
                            Expires
                        </label>
                        <Input
                            type="datetime-local"
                            value={expiresAt}
                            onChange={(event) =>
                                setExpiresAt(event.target.value)
                            }
                            disabled={isSaving}
                        />
                    </div>
                    <div className="md:col-span-2">
                        <label className="mb-2 block text-xs font-medium text-slate-400">
                            Description
                        </label>
                        <Textarea
                            value={description}
                            onChange={(event) =>
                                setDescription(event.target.value)
                            }
                            rows={3}
                            disabled={isSaving}
                        />
                    </div>
                </div>
            </Card>

            <Card className="p-5">
                <div>
                    <h2 className="text-sm font-semibold text-white">
                        Credential fields
                    </h2>
                    <p className="mt-1 text-xs leading-5 text-slate-500">
                        Secret fields are encrypted before storage. Existing
                        secret values are never loaded back into this form.
                    </p>
                </div>
                <div className="mt-5 grid gap-4 md:grid-cols-2">
                    {selectedType?.fields.map((field) => {
                        const isSecret = field.storage === "secret";
                        const existingSecret = Boolean(
                            credential?.secret_field_keys.includes(field.key),
                        );
                        const canClear =
                            isEditing &&
                            isSecret &&
                            existingSecret &&
                            !field.required;
                        const common = {
                            value: values[field.key] ?? "",
                            onChange: (
                                event: React.ChangeEvent<
                                    HTMLInputElement | HTMLTextAreaElement
                                >,
                            ) => updateValue(field.key, event.target.value),
                            disabled: isSaving,
                            required: !isEditing && field.required,
                            placeholder:
                                isEditing && isSecret && existingSecret
                                    ? "Leave blank to keep existing encrypted value"
                                    : undefined,
                        };
                        return (
                            <div
                                key={field.key}
                                className={
                                    field.kind === "textarea"
                                        ? "md:col-span-2"
                                        : ""
                                }
                            >
                                <div className="mb-2 flex items-center justify-between gap-3">
                                    <label className="text-xs font-medium text-slate-400">
                                        {field.label}
                                        {field.required ? " *" : ""}
                                    </label>
                                    {canClear ? (
                                        <label className="flex items-center gap-2 text-[11px] text-slate-500">
                                            <input
                                                type="checkbox"
                                                checked={clearSecretFields.includes(
                                                    field.key,
                                                )}
                                                onChange={(event) =>
                                                    setClearSecretFields(
                                                        (current) =>
                                                            event.target.checked
                                                                ? [
                                                                      ...current,
                                                                      field.key,
                                                                  ]
                                                                : current.filter(
                                                                      (key) =>
                                                                          key !==
                                                                          field.key,
                                                                  ),
                                                    )
                                                }
                                                disabled={isSaving}
                                            />
                                            Clear stored value
                                        </label>
                                    ) : null}
                                </div>
                                {field.kind === "textarea" ? (
                                    <Textarea
                                        {...common}
                                        rows={
                                            field.key.includes("key") ||
                                            field.key.includes("certificate")
                                                ? 8
                                                : 4
                                        }
                                    />
                                ) : (
                                    <Input
                                        {...common}
                                        type={
                                            field.kind === "password"
                                                ? "password"
                                                : field.kind === "url"
                                                  ? "url"
                                                  : "text"
                                        }
                                        autoComplete="off"
                                    />
                                )}
                                {isSecret && existingSecret ? (
                                    <p className="mt-1 text-[11px] text-emerald-400/80">
                                        Encrypted value currently stored.
                                    </p>
                                ) : null}
                            </div>
                        );
                    })}
                </div>
            </Card>

            <Card className="p-5">
                <div>
                    <h2 className="text-sm font-semibold text-white">
                        Linked infrastructure
                    </h2>
                    <p className="mt-1 text-xs leading-5 text-slate-500">
                        Link the credential to the servers, websites, databases,
                        applications or other resources that use it.
                    </p>
                </div>
                <Input
                    className="mt-4"
                    aria-label="Search infrastructure resources"
                    placeholder="Search by resource name, type or client…"
                    value={resourceSearch}
                    onChange={(event) => setResourceSearch(event.target.value)}
                    disabled={isSaving}
                />
                <p className="mt-2 text-xs text-slate-400">
                    {resourceLinks.length} linked · {matchingResources.length}{" "}
                    matching resources
                </p>
                {visibleResources.length === 0 ? (
                    <p className="mt-4 text-sm text-slate-500">
                        No eligible infrastructure resources are available for
                        this ownership scope.
                    </p>
                ) : matchingResources.length === 0 ? (
                    <p className="mt-4 text-sm text-slate-500">
                        No resources match your search.
                    </p>
                ) : (
                    <div className="mt-4 max-h-96 space-y-3 overflow-y-auto">
                        {matchingResources.map((resource) => {
                            const link = resourceLinks.find(
                                (item) => item.resource_id === resource.id,
                            );
                            return (
                                <div
                                    key={resource.id}
                                    className="rounded-lg border border-slate-800 bg-slate-950/40 p-3"
                                >
                                    <label className="flex cursor-pointer items-start gap-3">
                                        <input
                                            type="checkbox"
                                            className="mt-1"
                                            checked={Boolean(link)}
                                            onChange={() =>
                                                toggleResource(resource.id)
                                            }
                                            disabled={isSaving}
                                        />
                                        <span className="text-sm text-slate-300">
                                            {resourceLabel(resource)}
                                        </span>
                                    </label>
                                    {link ? (
                                        <div className="mt-3 grid gap-3 pl-6 md:grid-cols-[minmax(0,1fr)_auto]">
                                            <Input
                                                value={link.purpose ?? ""}
                                                onChange={(event) =>
                                                    updateResourceLink(
                                                        resource.id,
                                                        {
                                                            purpose:
                                                                event.target
                                                                    .value,
                                                        },
                                                    )
                                                }
                                                placeholder="Purpose, e.g. Production SSH login"
                                                disabled={isSaving}
                                            />
                                            <label className="flex items-center gap-2 text-xs text-slate-400">
                                                <input
                                                    type="checkbox"
                                                    checked={Boolean(
                                                        link.is_primary,
                                                    )}
                                                    onChange={(event) =>
                                                        updateResourceLink(
                                                            resource.id,
                                                            {
                                                                is_primary:
                                                                    event.target
                                                                        .checked,
                                                            },
                                                        )
                                                    }
                                                    disabled={isSaving}
                                                />
                                                Primary
                                            </label>
                                        </div>
                                    ) : null}
                                </div>
                            );
                        })}
                    </div>
                )}
            </Card>

            {saveError ? (
                <div className="rounded-lg border border-red-900/70 bg-red-950/40 px-4 py-3 text-sm text-red-200">
                    {saveError}
                </div>
            ) : null}
            <div className="flex justify-end gap-2">
                <Button
                    type="button"
                    variant="ghost"
                    onClick={onCancel}
                    disabled={isSaving}
                >
                    Cancel
                </Button>
                <Button
                    type="submit"
                    disabled={isSaving || !name.trim() || !selectedType}
                >
                    {isSaving
                        ? "Saving..."
                        : isEditing
                          ? "Save credential"
                          : "Create credential"}
                </Button>
            </div>
        </form>
    );
}

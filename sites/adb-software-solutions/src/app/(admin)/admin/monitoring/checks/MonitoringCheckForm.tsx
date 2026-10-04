"use client";

import {
    Button,
    ButtonLink,
    Card,
    DataError,
    DataLoading,
    Input,
    Select,
    Textarea,
} from "@/components/ui";
import { useAuth } from "@/contexts/AuthContext";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import { API_URL } from "@/lib/config";
import { useRouter } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";

interface ResourceOption {
    id: number;
    name: string;
    resource_type: string;
    client_id: number | null;
    client_name: string | null;
}

interface MonitoringOptions {
    resources: ResourceOption[];
}

interface MonitorCheckDetail {
    id: number;
    resource_id: number;
    resource_name: string;
    name: string;
    check_type: string;
    severity: string;
    target: string;
    port: number | null;
    expected_value: string;
    forbidden_value: string;
    interval_seconds: number;
    timeout_seconds: number;
    failure_threshold: number;
    recovery_threshold: number;
    expiry_warning_days: number;
    credential_id: number | null;
}

interface MonitorCheckResponse {
    id: number;
}

interface MonitorCheckFormState {
    resource_id: string;
    name: string;
    check_type: string;
    severity: string;
    target: string;
    port: string;
    expected_value: string;
    forbidden_value: string;
    interval_seconds: string;
    timeout_seconds: string;
    failure_threshold: string;
    recovery_threshold: string;
    expiry_warning_days: string;
    credential_id: number | null;
}

const EMPTY_FORM: MonitorCheckFormState = {
    resource_id: "",
    name: "",
    check_type: "http",
    severity: "error",
    target: "",
    port: "",
    expected_value: "",
    forbidden_value: "",
    interval_seconds: "300",
    timeout_seconds: "10",
    failure_threshold: "3",
    recovery_threshold: "2",
    expiry_warning_days: "30",
    credential_id: null,
};

const labelClasses = "space-y-1.5 text-sm font-medium text-slate-300";

function resourceLabel(resource: ResourceOption): string {
    const owner = resource.client_name ?? "ADB Internal";
    return `${resource.name} · ${resource.resource_type.replaceAll("_", " ")} · ${owner}`;
}

export function MonitoringCheckForm({
    checkId,
    initialResourceId,
}: {
    checkId?: number;
    initialResourceId?: number;
}) {
    const router = useRouter();
    const { hasPermission } = useAuth();
    const canSave = hasPermission(
        checkId
            ? "monitoring.change_monitorcheck"
            : "monitoring.add_monitorcheck",
    );
    const [form, setForm] = useState<MonitorCheckFormState>({
        ...EMPTY_FORM,
        resource_id: initialResourceId ? String(initialResourceId) : "",
    });
    const [resourceName, setResourceName] = useState("");
    const [options, setOptions] = useState<MonitoringOptions | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback(async () => {
        if (!canSave) {
            setIsLoading(false);
            return;
        }
        try {
            setIsLoading(true);
            setError(null);
            if (checkId) {
                const check = (await fetchAPI(
                    `${API_URL}/api/admin/monitoring/checks/${checkId}/configuration`,
                )) as MonitorCheckDetail;
                setResourceName(check.resource_name);
                setForm({
                    resource_id: String(check.resource_id),
                    name: check.name,
                    check_type: check.check_type,
                    severity: check.severity,
                    target: check.target,
                    port: check.port === null ? "" : String(check.port),
                    expected_value: check.expected_value,
                    forbidden_value: check.forbidden_value,
                    interval_seconds: String(check.interval_seconds),
                    timeout_seconds: String(check.timeout_seconds),
                    failure_threshold: String(check.failure_threshold),
                    recovery_threshold: String(check.recovery_threshold),
                    expiry_warning_days: String(check.expiry_warning_days),
                    credential_id: check.credential_id,
                });
            } else {
                const monitoringOptions = (await fetchAPI(
                    `${API_URL}/api/admin/monitoring/options`,
                )) as MonitoringOptions;
                setOptions(monitoringOptions);
                if (
                    initialResourceId &&
                    !monitoringOptions.resources.some(
                        (resource) => resource.id === initialResourceId,
                    )
                ) {
                    setError(
                        "The selected infrastructure resource is unavailable.",
                    );
                }
            }
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "Unable to load monitoring check configuration.",
            );
        } finally {
            setIsLoading(false);
        }
    }, [canSave, checkId, initialResourceId]);

    useEffect(() => {
        void load();
    }, [load]);

    function update<K extends keyof MonitorCheckFormState>(
        key: K,
        value: MonitorCheckFormState[K],
    ) {
        setForm((current) => ({ ...current, [key]: value }));
    }

    async function save(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!canSave) return;

        const resourceId = Number(form.resource_id);
        if (!checkId && !resourceId) {
            setError("Choose an infrastructure resource to monitor.");
            return;
        }
        if (form.check_type === "tcp" && !form.port) {
            setError("TCP checks require a port.");
            return;
        }
        if (
            form.check_type === "content" &&
            !form.expected_value.trim() &&
            !form.forbidden_value.trim()
        ) {
            setError("Content checks require expected or forbidden content.");
            return;
        }

        const payload = {
            ...(!checkId ? { resource_id: resourceId } : {}),
            name: form.name.trim(),
            check_type: form.check_type,
            severity: form.severity,
            target: form.target.trim(),
            port: form.port ? Number(form.port) : null,
            expected_value: form.expected_value,
            forbidden_value: form.forbidden_value,
            interval_seconds: Number(form.interval_seconds),
            timeout_seconds: Number(form.timeout_seconds),
            failure_threshold: Number(form.failure_threshold),
            recovery_threshold: Number(form.recovery_threshold),
            expiry_warning_days: Number(form.expiry_warning_days),
            credential_id: form.credential_id,
        };

        try {
            setIsSaving(true);
            setError(null);
            const check = (await fetchAPI(
                checkId
                    ? AdminAPI.monitoring.update(checkId)
                    : `${API_URL}/api/admin/monitoring/checks`,
                {
                    method: checkId ? "PUT" : "POST",
                    body: JSON.stringify(payload),
                },
            )) as MonitorCheckResponse;
            router.push(`/admin/monitoring/checks/${check.id}`);
            router.refresh();
        } catch (saveError) {
            setError(
                saveError instanceof Error
                    ? saveError.message
                    : "Unable to save the monitoring check.",
            );
        } finally {
            setIsSaving(false);
        }
    }

    if (!canSave) {
        return (
            <DataError message="You do not have permission to manage monitoring checks." />
        );
    }
    if (isLoading) {
        return <DataLoading label="Loading monitoring configuration..." />;
    }

    return (
        <form onSubmit={(event) => void save(event)} className="space-y-6">
            {error ? (
                <DataError message={error} onRetry={() => void load()} />
            ) : null}

            <Card className="p-5">
                <div className="grid gap-5 md:grid-cols-2">
                    {checkId ? (
                        <div className={labelClasses}>
                            <span>Infrastructure resource</span>
                            <div className="rounded-lg border border-slate-800 bg-slate-950 px-3 py-2.5 text-sm text-slate-300">
                                {resourceName}
                            </div>
                        </div>
                    ) : (
                        <label className={`${labelClasses} md:col-span-2`}>
                            <span>Infrastructure resource</span>
                            <Select
                                value={form.resource_id}
                                onChange={(event) =>
                                    update("resource_id", event.target.value)
                                }
                                required
                            >
                                <option value="">Choose resource</option>
                                {options?.resources.map((resource) => (
                                    <option
                                        key={resource.id}
                                        value={resource.id}
                                    >
                                        {resourceLabel(resource)}
                                    </option>
                                ))}
                            </Select>
                        </label>
                    )}

                    <label className={labelClasses}>
                        <span>Check name</span>
                        <Input
                            value={form.name}
                            onChange={(event) =>
                                update("name", event.target.value)
                            }
                            required
                            maxLength={200}
                            placeholder="Primary website health"
                        />
                    </label>
                    <label className={labelClasses}>
                        <span>Severity</span>
                        <Select
                            value={form.severity}
                            onChange={(event) =>
                                update("severity", event.target.value)
                            }
                        >
                            <option value="info">Info</option>
                            <option value="warning">Warning</option>
                            <option value="error">Error</option>
                            <option value="critical">Critical</option>
                        </Select>
                    </label>
                    <label className={labelClasses}>
                        <span>Check type</span>
                        <Select
                            value={form.check_type}
                            onChange={(event) =>
                                update("check_type", event.target.value)
                            }
                        >
                            <option value="icmp">ICMP / ping</option>
                            <option value="tcp">TCP port</option>
                            <option value="http">HTTP / HTTPS</option>
                            <option value="content">
                                Expected / forbidden content
                            </option>
                            <option value="tls">TLS certificate</option>
                            <option value="dns">DNS record</option>
                            <option value="certificate_expiry">
                                Stored certificate expiry
                            </option>
                            <option value="domain_expiry">
                                Domain registration expiry
                            </option>
                        </Select>
                    </label>
                    <label className={labelClasses}>
                        <span>Target</span>
                        <Input
                            value={form.target}
                            onChange={(event) =>
                                update("target", event.target.value)
                            }
                            required
                            maxLength={500}
                            placeholder="https://example.com or host.example.com"
                        />
                    </label>
                    {form.check_type === "tcp" || form.check_type === "tls" ? (
                        <label className={labelClasses}>
                            <span>
                                Port{" "}
                                {form.check_type === "tls" ? "(optional)" : ""}
                            </span>
                            <Input
                                type="number"
                                min={1}
                                max={65535}
                                value={form.port}
                                onChange={(event) =>
                                    update("port", event.target.value)
                                }
                                required={form.check_type === "tcp"}
                                placeholder={
                                    form.check_type === "tls" ? "443" : "5432"
                                }
                            />
                        </label>
                    ) : null}
                    {form.check_type === "content" ? (
                        <>
                            <label className={labelClasses}>
                                <span>Expected content</span>
                                <Textarea
                                    value={form.expected_value}
                                    onChange={(event) =>
                                        update(
                                            "expected_value",
                                            event.target.value,
                                        )
                                    }
                                    rows={3}
                                />
                            </label>
                            <label className={labelClasses}>
                                <span>Forbidden content</span>
                                <Textarea
                                    value={form.forbidden_value}
                                    onChange={(event) =>
                                        update(
                                            "forbidden_value",
                                            event.target.value,
                                        )
                                    }
                                    rows={3}
                                />
                            </label>
                        </>
                    ) : null}
                    {form.check_type === "dns" ? (
                        <label className={labelClasses}>
                            <span>Expected IP address (optional)</span>
                            <Input
                                value={form.expected_value}
                                onChange={(event) =>
                                    update("expected_value", event.target.value)
                                }
                                placeholder="203.0.113.10"
                            />
                        </label>
                    ) : null}
                </div>
            </Card>

            <Card className="p-5">
                <h2 className="text-sm font-semibold text-white">
                    Execution policy
                </h2>
                <div className="mt-4 grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
                    <label className={labelClasses}>
                        <span>Interval (seconds)</span>
                        <Input
                            type="number"
                            min={30}
                            value={form.interval_seconds}
                            onChange={(event) =>
                                update("interval_seconds", event.target.value)
                            }
                            required
                        />
                    </label>
                    <label className={labelClasses}>
                        <span>Timeout (seconds)</span>
                        <Input
                            type="number"
                            min={1}
                            max={300}
                            value={form.timeout_seconds}
                            onChange={(event) =>
                                update("timeout_seconds", event.target.value)
                            }
                            required
                        />
                    </label>
                    <label className={labelClasses}>
                        <span>Failures before incident</span>
                        <Input
                            type="number"
                            min={1}
                            value={form.failure_threshold}
                            onChange={(event) =>
                                update("failure_threshold", event.target.value)
                            }
                            required
                        />
                    </label>
                    <label className={labelClasses}>
                        <span>Successes before recovery</span>
                        <Input
                            type="number"
                            min={1}
                            value={form.recovery_threshold}
                            onChange={(event) =>
                                update("recovery_threshold", event.target.value)
                            }
                            required
                        />
                    </label>
                    {form.check_type === "tls" ||
                    form.check_type === "domain_expiry" ||
                    form.check_type === "certificate_expiry" ? (
                        <label className={labelClasses}>
                            <span>Expiry warning (days)</span>
                            <Input
                                type="number"
                                min={1}
                                value={form.expiry_warning_days}
                                onChange={(event) =>
                                    update(
                                        "expiry_warning_days",
                                        event.target.value,
                                    )
                                }
                                required
                            />
                        </label>
                    ) : null}
                </div>
            </Card>

            <Card className="border-slate-800 bg-slate-950/40 p-5">
                <h2 className="text-sm font-semibold text-white">
                    Authentication
                </h2>
                <p className="mt-2 text-xs leading-5 text-slate-500">
                    This initial operator workflow creates unauthenticated
                    probes. Vault-backed credentials remain server-side
                    references; they will be exposed here only alongside an
                    explicit authentication scheme so a saved credential can
                    never be silently ignored or interpreted incorrectly.
                </p>
            </Card>

            <div className="flex flex-wrap gap-3">
                <Button type="submit" disabled={isSaving}>
                    {isSaving
                        ? "Saving..."
                        : checkId
                          ? "Save changes"
                          : "Create check"}
                </Button>
                <ButtonLink
                    href={
                        checkId
                            ? `/admin/monitoring/checks/${checkId}`
                            : "/admin/monitoring"
                    }
                    variant="outline"
                >
                    Cancel
                </ButtonLink>
            </div>
        </form>
    );
}

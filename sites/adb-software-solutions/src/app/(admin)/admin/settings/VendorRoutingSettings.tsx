"use client";

import { Badge, Button, Card, DataError, DataLoading, Input, Select } from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import { type FormEvent, useCallback, useEffect, useMemo, useState } from "react";

interface Vendor {
    id: number;
    name: string;
    website_url: string;
    notes: string;
    enabled: boolean;
}

interface VendorRule {
    id: number;
    vendor_id: number;
    vendor_name: string;
    match_type: "email" | "domain";
    match_value: string;
    target_queue_id: number | null;
    target_queue_name: string | null;
    priority: string;
    enabled: boolean;
    ordering: number;
    notes: string;
}

interface Queue {
    id: number;
    name: string;
    key: string;
    brand_name: string | null;
    enabled: boolean;
}

function label(value: string) {
    return value
        .split("_")
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" ");
}

export function VendorRoutingSettings() {
    const [vendors, setVendors] = useState<Vendor[]>([]);
    const [rules, setRules] = useState<VendorRule[]>([]);
    const [queues, setQueues] = useState<Queue[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [vendorForm, setVendorForm] = useState({ name: "", website_url: "" });
    const [ruleForm, setRuleForm] = useState({
        vendor_id: "",
        match_type: "domain",
        match_value: "",
        target_queue_id: "",
        priority: "low",
    });

    const loadSettings = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            const [vendorRows, ruleRows, queueRows] = await Promise.all([
                fetchAPI(AdminAPI.tickets.settings.vendors()),
                fetchAPI(AdminAPI.tickets.settings.vendorRules()),
                fetchAPI(AdminAPI.tickets.queues()),
            ]);
            const loadedVendors = vendorRows as Vendor[];
            const loadedQueues = queueRows as Queue[];
            setVendors(loadedVendors);
            setRules(ruleRows as VendorRule[]);
            setQueues(loadedQueues);
            setRuleForm((current) => {
                const vendorQueue = loadedQueues.find((queue) => queue.key === "vendors-services");
                return {
                    ...current,
                    vendor_id:
                        current.vendor_id ||
                        String(loadedVendors.find((vendor) => vendor.enabled)?.id ?? ""),
                    target_queue_id:
                        current.target_queue_id || String(vendorQueue?.id ?? ""),
                };
            });
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "Unable to load vendor routing settings.",
            );
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        void loadSettings();
    }, [loadSettings]);

    const enabledVendors = useMemo(
        () => vendors.filter((vendor) => vendor.enabled),
        [vendors],
    );
    const enabledQueues = useMemo(() => queues.filter((queue) => queue.enabled), [queues]);

    async function createVendor(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!vendorForm.name.trim()) return;
        try {
            setIsSaving(true);
            setError(null);
            await fetchAPI(AdminAPI.tickets.settings.vendors(), {
                method: "POST",
                body: JSON.stringify({
                    name: vendorForm.name.trim(),
                    website_url: vendorForm.website_url.trim(),
                }),
            });
            setVendorForm({ name: "", website_url: "" });
            await loadSettings();
        } catch (saveError) {
            setError(saveError instanceof Error ? saveError.message : "Unable to add vendor.");
        } finally {
            setIsSaving(false);
        }
    }

    async function createRule(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!ruleForm.vendor_id || !ruleForm.match_value.trim()) return;
        try {
            setIsSaving(true);
            setError(null);
            await fetchAPI(AdminAPI.tickets.settings.vendorRules(), {
                method: "POST",
                body: JSON.stringify({
                    vendor_id: Number(ruleForm.vendor_id),
                    match_type: ruleForm.match_type,
                    match_value: ruleForm.match_value.trim(),
                    target_queue_id: ruleForm.target_queue_id
                        ? Number(ruleForm.target_queue_id)
                        : null,
                    priority: ruleForm.priority,
                }),
            });
            setRuleForm((current) => ({ ...current, match_value: "" }));
            await loadSettings();
        } catch (saveError) {
            setError(
                saveError instanceof Error ? saveError.message : "Unable to add sender rule.",
            );
        } finally {
            setIsSaving(false);
        }
    }

    async function setVendorEnabled(vendor: Vendor) {
        try {
            setIsSaving(true);
            setError(null);
            await fetchAPI(AdminAPI.tickets.settings.vendorEnabled(vendor.id), {
                method: "PUT",
                body: JSON.stringify({ enabled: !vendor.enabled }),
            });
            await loadSettings();
        } catch (saveError) {
            setError(
                saveError instanceof Error ? saveError.message : "Unable to update vendor.",
            );
        } finally {
            setIsSaving(false);
        }
    }

    async function setRuleEnabled(rule: VendorRule) {
        try {
            setIsSaving(true);
            setError(null);
            await fetchAPI(AdminAPI.tickets.settings.vendorRuleEnabled(rule.id), {
                method: "PUT",
                body: JSON.stringify({ enabled: !rule.enabled }),
            });
            await loadSettings();
        } catch (saveError) {
            setError(
                saveError instanceof Error ? saveError.message : "Unable to update sender rule.",
            );
        } finally {
            setIsSaving(false);
        }
    }

    if (isLoading) return <DataLoading label="Loading vendor routing settings..." />;

    return (
        <Card className="p-5">
            <div className="max-w-3xl">
                <h2 className="text-base font-semibold text-white">Vendors &amp; services</h2>
                <p className="mt-2 text-sm leading-6 text-slate-400">
                    Keep provider mail such as GitHub, DigitalOcean, PayPal and Microsoft out of
                    customer queues without discarding it. Exact-address rules take precedence over
                    domain rules. Known client senders remain client mail even when their domain also
                    matches a vendor rule.
                </p>
            </div>

            {error ? <div className="mt-4"><DataError message={error} onRetry={() => void loadSettings()} /></div> : null}

            <div className="mt-6 grid gap-6 xl:grid-cols-2">
                <div>
                    <h3 className="text-sm font-semibold text-white">Vendors</h3>
                    <div className="mt-3 divide-y divide-slate-800 overflow-hidden rounded-xl border border-slate-800">
                        {vendors.map((vendor) => (
                            <div key={vendor.id} className="flex items-center justify-between gap-3 bg-slate-950/60 p-3">
                                <div className="min-w-0">
                                    <div className="font-medium text-slate-200">{vendor.name}</div>
                                    {vendor.website_url ? (
                                        <div className="mt-1 truncate text-xs text-slate-500">{vendor.website_url}</div>
                                    ) : null}
                                </div>
                                <div className="flex items-center gap-2">
                                    <Badge>{vendor.enabled ? "Enabled" : "Disabled"}</Badge>
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="sm"
                                        disabled={isSaving}
                                        onClick={() => void setVendorEnabled(vendor)}
                                    >
                                        {vendor.enabled ? "Disable" : "Enable"}
                                    </Button>
                                </div>
                            </div>
                        ))}
                    </div>

                    <form onSubmit={(event) => void createVendor(event)} className="mt-4 rounded-xl border border-slate-800 p-4">
                        <h4 className="text-sm font-medium text-white">Add vendor</h4>
                        <div className="mt-3 grid gap-3">
                            <Input
                                required
                                value={vendorForm.name}
                                onChange={(event) =>
                                    setVendorForm((current) => ({ ...current, name: event.target.value }))
                                }
                                placeholder="Cloudflare"
                            />
                            <Input
                                type="url"
                                value={vendorForm.website_url}
                                onChange={(event) =>
                                    setVendorForm((current) => ({ ...current, website_url: event.target.value }))
                                }
                                placeholder="https://www.cloudflare.com (optional)"
                            />
                            <div className="flex justify-end">
                                <Button type="submit" size="sm" disabled={isSaving || !vendorForm.name.trim()}>
                                    Add vendor
                                </Button>
                            </div>
                        </div>
                    </form>
                </div>

                <div>
                    <h3 className="text-sm font-semibold text-white">Sender rules</h3>
                    <div className="mt-3 divide-y divide-slate-800 overflow-hidden rounded-xl border border-slate-800">
                        {rules.map((rule) => (
                            <div key={rule.id} className="bg-slate-950/60 p-3">
                                <div className="flex items-start justify-between gap-3">
                                    <div className="min-w-0">
                                        <div className="font-medium text-slate-200">{rule.vendor_name}</div>
                                        <div className="mt-1 break-all font-mono text-xs text-slate-400">
                                            {rule.match_type === "domain" ? "@" : ""}{rule.match_value}
                                        </div>
                                        <div className="mt-1 text-xs text-slate-600">
                                            {rule.target_queue_name || "Automatic vendor queue"}
                                            {rule.priority ? ` · ${label(rule.priority)}` : ""}
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Badge>{rule.enabled ? "Enabled" : "Disabled"}</Badge>
                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="sm"
                                            disabled={isSaving}
                                            onClick={() => void setRuleEnabled(rule)}
                                        >
                                            {rule.enabled ? "Disable" : "Enable"}
                                        </Button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    <form onSubmit={(event) => void createRule(event)} className="mt-4 rounded-xl border border-slate-800 p-4">
                        <h4 className="text-sm font-medium text-white">Add sender rule</h4>
                        <p className="mt-1 text-xs leading-5 text-slate-500">
                            Use a domain for the normal vendor-wide rule, or an exact address when one
                            sender should receive different routing or priority.
                        </p>
                        <div className="mt-3 grid gap-3">
                            <Select
                                required
                                value={ruleForm.vendor_id}
                                onChange={(event) =>
                                    setRuleForm((current) => ({ ...current, vendor_id: event.target.value }))
                                }
                            >
                                <option value="">Select vendor</option>
                                {enabledVendors.map((vendor) => (
                                    <option key={vendor.id} value={vendor.id}>{vendor.name}</option>
                                ))}
                            </Select>
                            <div className="grid gap-3 sm:grid-cols-[160px_minmax(0,1fr)]">
                                <Select
                                    value={ruleForm.match_type}
                                    onChange={(event) =>
                                        setRuleForm((current) => ({ ...current, match_type: event.target.value }))
                                    }
                                >
                                    <option value="domain">Domain</option>
                                    <option value="email">Exact email</option>
                                </Select>
                                <Input
                                    required
                                    value={ruleForm.match_value}
                                    onChange={(event) =>
                                        setRuleForm((current) => ({ ...current, match_value: event.target.value }))
                                    }
                                    placeholder={ruleForm.match_type === "domain" ? "cloudflare.com" : "security@cloudflare.com"}
                                />
                            </div>
                            <Select
                                value={ruleForm.target_queue_id}
                                onChange={(event) =>
                                    setRuleForm((current) => ({ ...current, target_queue_id: event.target.value }))
                                }
                            >
                                <option value="">Automatic Vendors &amp; Services queue</option>
                                {enabledQueues.map((queue) => (
                                    <option key={queue.id} value={queue.id}>
                                        {queue.name}{queue.brand_name ? ` · ${queue.brand_name}` : " · Global"}
                                    </option>
                                ))}
                            </Select>
                            <Select
                                value={ruleForm.priority}
                                onChange={(event) =>
                                    setRuleForm((current) => ({ ...current, priority: event.target.value }))
                                }
                            >
                                <option value="">Queue default priority</option>
                                <option value="low">Low</option>
                                <option value="normal">Normal</option>
                                <option value="high">High</option>
                                <option value="urgent">Urgent</option>
                            </Select>
                            <div className="flex justify-end">
                                <Button
                                    type="submit"
                                    size="sm"
                                    disabled={isSaving || !ruleForm.vendor_id || !ruleForm.match_value.trim()}
                                >
                                    Add sender rule
                                </Button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </Card>
    );
}

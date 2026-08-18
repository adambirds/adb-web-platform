"use client";

import { Card, DataError, DataLoading, StatCard } from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import {
    CircleStackIcon,
    CloudIcon,
    CodeBracketIcon,
    DevicePhoneMobileIcon,
    EnvelopeIcon,
    GlobeAltIcon,
    KeyIcon,
    ServerStackIcon,
} from "@heroicons/react/24/outline";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

interface InfrastructureSummary {
    server_count: number;
    database_count: number;
    website_count: number;
    domain_count: number;
    expiring_domain_count: number;
    ssl_certificate_count: number;
    expiring_certificate_count: number;
    licence_count: number;
    renewing_licence_count: number;
    application_count: number;
    mobile_app_count: number;
    api_count: number;
    bot_count: number;
    email_system_count: number;
}

const inventoryLinks = [
    ["Servers", "/admin/infrastructure/servers", "Physical, virtual and container hosts."],
    ["Databases", "/admin/infrastructure/databases", "Managed and self-hosted database instances."],
    ["Websites", "/admin/infrastructure/websites", "Production, staging and development web properties."],
    ["Domains", "/admin/infrastructure/domains", "Registrations, renewals and DNS-linked properties."],
    ["SSL certificates", "/admin/infrastructure/ssl-certificates", "Certificate expiry and provider inventory."],
    ["Licences", "/admin/infrastructure/licences", "Subscriptions, renewals and software licences."],
    ["Applications", "/admin/infrastructure/applications", "Logical applications spanning infrastructure components."],
    ["Technology stack", "/admin/infrastructure/tech-stack", "Technology and version inventory by website."],
] as const;

const additionalSystems = [
    ["Mobile apps", "/admin/infrastructure/mobile-apps", "mobile_app_count", DevicePhoneMobileIcon],
    ["APIs", "/admin/infrastructure/apis", "api_count", CodeBracketIcon],
    ["Bots", "/admin/infrastructure/bots", "bot_count", CloudIcon],
    ["Email systems", "/admin/infrastructure/email-systems", "email_system_count", EnvelopeIcon],
] as const;

export function InfrastructureOverview() {
    const [summary, setSummary] = useState<InfrastructureSummary | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadSummary = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);
            const data = (await fetchAPI(
                AdminAPI.infrastructure.summary(),
            )) as InfrastructureSummary;
            setSummary(data);
        } catch (loadError) {
            setError(
                loadError instanceof Error
                    ? loadError.message
                    : "An unexpected error occurred while loading infrastructure.",
            );
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        void loadSummary();
    }, [loadSummary]);

    if (isLoading) return <DataLoading label="Loading infrastructure inventory..." />;
    if (error || !summary) {
        return (
            <DataError
                message={error || "Infrastructure summary is unavailable."}
                onRetry={() => void loadSummary()}
            />
        );
    }

    return (
        <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <StatCard label="Servers" value={String(summary.server_count)} helper="Tracked compute hosts" icon={<ServerStackIcon className="h-5 w-5" />} />
                <StatCard label="Databases" value={String(summary.database_count)} helper="Database instances" icon={<CircleStackIcon className="h-5 w-5" />} />
                <StatCard label="Websites" value={String(summary.website_count)} helper="Web properties" icon={<GlobeAltIcon className="h-5 w-5" />} />
                <StatCard label="Applications" value={String(summary.application_count)} helper="Logical applications" icon={<CloudIcon className="h-5 w-5" />} />
                <StatCard label="Domains" value={String(summary.domain_count)} helper={`${summary.expiring_domain_count} expire within 45 days`} icon={<GlobeAltIcon className="h-5 w-5" />} accent={summary.expiring_domain_count > 0 ? "amber" : "cyan"} />
                <StatCard label="SSL certificates" value={String(summary.ssl_certificate_count)} helper={`${summary.expiring_certificate_count} expire within 45 days`} icon={<KeyIcon className="h-5 w-5" />} accent={summary.expiring_certificate_count > 0 ? "amber" : "green"} />
                <StatCard label="Licences" value={String(summary.licence_count)} helper={`${summary.renewing_licence_count} renew within 45 days`} icon={<KeyIcon className="h-5 w-5" />} accent={summary.renewing_licence_count > 0 ? "amber" : "cyan"} />
                <StatCard label="APIs & bots" value={String(summary.api_count + summary.bot_count)} helper={`${summary.api_count} APIs · ${summary.bot_count} bots`} icon={<CodeBracketIcon className="h-5 w-5" />} />
            </div>

            <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
                <Card className="p-5">
                    <div className="mb-4">
                        <h2 className="text-sm font-semibold text-white">Infrastructure inventory</h2>
                        <p className="mt-1 text-xs text-slate-500">Jump into a register to inspect the underlying operational records.</p>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2">
                        {inventoryLinks.map(([label, href, description]) => (
                            <Link key={href} href={href} className="rounded-xl border border-slate-800 bg-slate-950/50 p-4 transition hover:border-slate-700 hover:bg-slate-900">
                                <div className="text-sm font-medium text-slate-100">{label}</div>
                                <div className="mt-1 text-xs leading-5 text-slate-500">{description}</div>
                            </Link>
                        ))}
                    </div>
                </Card>

                <Card className="p-5">
                    <h2 className="text-sm font-semibold text-white">Additional systems</h2>
                    <div className="mt-4 space-y-2">
                        {additionalSystems.map(([label, href, countKey, Icon]) => (
                            <Link key={href} href={href} className="flex items-center justify-between rounded-lg px-2 py-2 text-sm transition hover:bg-slate-900">
                                <span className="flex items-center gap-2 text-slate-400">
                                    <Icon className="h-4 w-4" />
                                    {label}
                                </span>
                                <span className="font-medium tabular-nums text-slate-200">{summary[countKey]}</span>
                            </Link>
                        ))}
                    </div>
                </Card>
            </div>
        </div>
    );
}

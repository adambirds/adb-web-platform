"use client";

import {
    Card,
    DataError,
    DataLoading,
    StatCard,
} from "@/components/ui";
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
    {
        label: "Servers",
        href: "/admin/infrastructure/servers",
        description: "Physical, virtual and container hosts.",
    },
    {
        label: "Databases",
        href: "/admin/infrastructure/databases",
        description: "Managed and self-hosted database instances.",
    },
    {
        label: "Websites",
        href: "/admin/infrastructure/websites",
        description: "Production, staging and development web properties.",
    },
    {
        label: "Domains",
        href: "/admin/infrastructure/domains",
        description: "Registrations, renewals and DNS-linked properties.",
    },
];

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

    if (isLoading) {
        return <DataLoading label="Loading infrastructure inventory..." />;
    }

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
                <StatCard
                    label="Servers"
                    value={summary.server_count.toLocaleString()}
                    helper="Tracked compute hosts"
                    icon={<ServerStackIcon className="h-5 w-5" />}
                />
                <StatCard
                    label="Databases"
                    value={summary.database_count.toLocaleString()}
                    helper="Database instances"
                    icon={<CircleStackIcon className="h-5 w-5" />}
                />
                <StatCard
                    label="Websites"
                    value={summary.website_count.toLocaleString()}
                    helper="Web properties"
                    icon={<GlobeAltIcon className="h-5 w-5" />}
                />
                <StatCard
                    label="Applications"
                    value={summary.application_count.toLocaleString()}
                    helper="Logical applications"
                    icon={<CloudIcon className="h-5 w-5" />}
                />
                <StatCard
                    label="Domains"
                    value={summary.domain_count.toLocaleString()}
                    helper={`${summary.expiring_domain_count} expire within 45 days`}
                    icon={<GlobeAltIcon className="h-5 w-5" />}
                    accent={summary.expiring_domain_count > 0 ? "amber" : "cyan"}
                />
                <StatCard
                    label="SSL certificates"
                    value={summary.ssl_certificate_count.toLocaleString()}
                    helper={`${summary.expiring_certificate_count} expire within 45 days`}
                    icon={<KeyIcon className="h-5 w-5" />}
                    accent={
                        summary.expiring_certificate_count > 0 ? "amber" : "green"
                    }
                />
                <StatCard
                    label="Licences"
                    value={summary.licence_count.toLocaleString()}
                    helper={`${summary.renewing_licence_count} renew within 45 days`}
                    icon={<KeyIcon className="h-5 w-5" />}
                    accent={summary.renewing_licence_count > 0 ? "amber" : "cyan"}
                />
                <StatCard
                    label="APIs & bots"
                    value={(summary.api_count + summary.bot_count).toLocaleString()}
                    helper={`${summary.api_count} APIs · ${summary.bot_count} bots`}
                    icon={<CodeBracketIcon className="h-5 w-5" />}
                />
            </div>

            <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
                <Card className="p-5">
                    <div className="mb-4">
                        <h2 className="text-sm font-semibold text-white">
                            Infrastructure inventory
                        </h2>
                        <p className="mt-1 text-xs text-slate-500">
                            Jump into the main infrastructure registers.
                        </p>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2">
                        {inventoryLinks.map((item) => (
                            <Link
                                key={item.href}
                                href={item.href}
                                className="rounded-xl border border-slate-800 bg-slate-950/50 p-4 transition hover:border-slate-700 hover:bg-slate-900"
                            >
                                <div className="text-sm font-medium text-slate-100">
                                    {item.label}
                                </div>
                                <div className="mt-1 text-xs leading-5 text-slate-500">
                                    {item.description}
                                </div>
                            </Link>
                        ))}
                    </div>
                </Card>

                <Card className="p-5">
                    <h2 className="text-sm font-semibold text-white">
                        Additional systems
                    </h2>
                    <div className="mt-4 space-y-3 text-sm">
                        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                            <span className="flex items-center gap-2 text-slate-400">
                                <DevicePhoneMobileIcon className="h-4 w-4" />
                                Mobile apps
                            </span>
                            <span className="font-medium tabular-nums text-slate-200">
                                {summary.mobile_app_count}
                            </span>
                        </div>
                        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                            <span className="flex items-center gap-2 text-slate-400">
                                <CodeBracketIcon className="h-4 w-4" />
                                APIs
                            </span>
                            <span className="font-medium tabular-nums text-slate-200">
                                {summary.api_count}
                            </span>
                        </div>
                        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                            <span className="flex items-center gap-2 text-slate-400">
                                <CloudIcon className="h-4 w-4" />
                                Bots
                            </span>
                            <span className="font-medium tabular-nums text-slate-200">
                                {summary.bot_count}
                            </span>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="flex items-center gap-2 text-slate-400">
                                <EnvelopeIcon className="h-4 w-4" />
                                Email systems
                            </span>
                            <span className="font-medium tabular-nums text-slate-200">
                                {summary.email_system_count}
                            </span>
                        </div>
                    </div>
                </Card>
            </div>
        </div>
    );
}

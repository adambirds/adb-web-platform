"use client";

import { Container, PageHeader } from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { InfrastructureRegister } from "../InfrastructureRegister";

export default function WebsitesPage() {
    return (
        <Container className="py-8">
            <PageHeader title="Websites" description="Managed websites and web applications with their core infrastructure relationships." />
            <div className="mt-6">
                <InfrastructureRegister
                    endpoint={AdminAPI.infrastructure.websites()}
                    loadingLabel="Loading website inventory..."
                    emptyTitle="No websites recorded"
                    emptyDescription="Websites will appear here once they are added to the infrastructure inventory."
                    columns={[
                        { key: "name", label: "Website", render: (value) => <span className="font-medium text-slate-100">{String(value)}</span> },
                        { key: "primary_url", label: "Primary URL" },
                        { key: "environment_type", label: "Environment" },
                        { key: "database_name", label: "Database" },
                        { key: "server_count", label: "Servers" },
                        { key: "domain_count", label: "Domains" },
                    ]}
                />
            </div>
        </Container>
    );
}

"use client";

import { Container, PageHeader } from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { InfrastructureRegister } from "../InfrastructureRegister";

export default function DatabasesPage() {
    return (
        <Container className="py-8">
            <PageHeader title="Databases" description="Database services, versions, providers and host relationships." />
            <div className="mt-6">
                <InfrastructureRegister
                    endpoint={AdminAPI.infrastructure.databases()}
                    loadingLabel="Loading database inventory..."
                    emptyTitle="No databases recorded"
                    emptyDescription="Database services will appear here once they are added to the infrastructure inventory."
                    columns={[
                        { key: "name", label: "Database", render: (value) => <span className="font-medium text-slate-100">{String(value)}</span> },
                        { key: "db_type", label: "Type" },
                        { key: "provider", label: "Provider" },
                        { key: "version", label: "Version" },
                        { key: "server_hostname", label: "Server" },
                    ]}
                />
            </div>
        </Container>
    );
}

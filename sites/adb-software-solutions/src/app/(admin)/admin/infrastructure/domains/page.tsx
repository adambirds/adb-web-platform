"use client";

import { Container, PageHeader } from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { InfrastructureRegister } from "../InfrastructureRegister";

export default function DomainsPage() {
    return (
        <Container className="py-8">
            <PageHeader title="Domains" description="Domain registrations, renewal dates and website relationships." />
            <div className="mt-6">
                <InfrastructureRegister
                    endpoint={AdminAPI.infrastructure.domains()}
                    loadingLabel="Loading domain inventory..."
                    emptyTitle="No domains recorded"
                    emptyDescription="Domains will appear here once they are added to the infrastructure inventory."
                    columns={[
                        { key: "domain_name", label: "Domain", render: (value) => <span className="font-medium text-slate-100">{String(value)}</span> },
                        { key: "registrar", label: "Registrar" },
                        { key: "expiry_date", label: "Expires" },
                        { key: "auto_renew", label: "Auto renew", render: (value) => value ? "Yes" : "No" },
                        { key: "website_count", label: "Websites" },
                    ]}
                />
            </div>
        </Container>
    );
}

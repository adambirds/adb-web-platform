"use client";

import { Container, PageHeader } from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { InfrastructureRegister } from "../InfrastructureRegister";

export default function LicencesPage() {
    return (
        <Container className="py-8">
            <PageHeader title="Licences" description="Software subscriptions, renewals, costs and website assignments." />
            <div className="mt-6">
                <InfrastructureRegister
                    endpoint={AdminAPI.infrastructure.licences()}
                    loadingLabel="Loading licence inventory..."
                    emptyTitle="No licences recorded"
                    emptyDescription="Software licences will appear here once they are added to the infrastructure inventory."
                    columns={[
                        { key: "name", label: "Licence", render: (value) => <span className="font-medium text-slate-100">{String(value)}</span> },
                        { key: "vendor", label: "Vendor" },
                        { key: "licence_type", label: "Type" },
                        { key: "renewal_date", label: "Renews" },
                        { key: "renewal_cost", label: "Cost", render: (value) => value == null ? "—" : `£${Number(value).toFixed(2)}` },
                        { key: "auto_renew", label: "Auto renew", render: (value) => value ? "Yes" : "No" },
                        { key: "website_count", label: "Websites" },
                    ]}
                />
            </div>
        </Container>
    );
}

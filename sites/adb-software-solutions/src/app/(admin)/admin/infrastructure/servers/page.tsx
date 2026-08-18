"use client";

import { Container, PageHeader } from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";
import { InfrastructureRegister } from "../InfrastructureRegister";

export default function ServersPage() {
    return (
        <Container className="py-8">
            <PageHeader title="Servers" description="Physical and virtual compute inventory across ADB-managed environments." />
            <div className="mt-6">
                <InfrastructureRegister
                    endpoint={AdminAPI.infrastructure.servers()}
                    loadingLabel="Loading server inventory..."
                    emptyTitle="No servers recorded"
                    emptyDescription="Servers will appear here once they are added to the infrastructure inventory."
                    columns={[
                        { key: "hostname", label: "Hostname", render: (value) => <span className="font-medium text-slate-100">{String(value)}</span> },
                        { key: "role", label: "Role" },
                        { key: "provider", label: "Provider" },
                        { key: "region", label: "Region" },
                        { key: "os", label: "OS" },
                        { key: "public_ip", label: "Public IP" },
                        { key: "ram_gb", label: "RAM", render: (value) => value == null ? "—" : `${String(value)} GB` },
                    ]}
                />
            </div>
        </Container>
    );
}

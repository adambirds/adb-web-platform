"use client";

import { Container, PageHeader, ResourceRegister } from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";

export default function CredentialsPage() {
    return (
        <Container className="py-8">
            <PageHeader
                title="Credentials"
                description="Credential metadata available within your current client scope. Secret values are never returned by this register."
            />
            <div className="mt-6">
                <ResourceRegister
                    endpoint={AdminAPI.credentials.list()}
                    loadingLabel="Loading credential inventory..."
                    emptyTitle="No credentials in your scope"
                    emptyDescription="Credential metadata will appear here once records exist and your access profile allows them."
                    columns={[
                        {
                            key: "name",
                            label: "Credential",
                            render: (value) => (
                                <span className="font-medium text-slate-100">
                                    {String(value)}
                                </span>
                            ),
                        },
                        { key: "ownership_type", label: "Ownership" },
                        { key: "client", label: "Client" },
                        { key: "credential_type", label: "Type" },
                        { key: "username", label: "Username" },
                        { key: "url", label: "URL" },
                        { key: "expires_at", label: "Expires" },
                        { key: "last_rotated_at", label: "Last rotated" },
                    ]}
                />
            </div>
        </Container>
    );
}

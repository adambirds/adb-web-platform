"use client";

import { Container, PageHeader, ResourceRegister } from "@/components/ui";
import { AdminAPI } from "@/lib/api/endpoints";

export default function KnowledgeBasePage() {
    return (
        <Container className="py-8">
            <PageHeader
                title="Knowledge Base"
                description="Internal and client documentation available within your current access scope."
            />
            <div className="mt-6">
                <ResourceRegister
                    endpoint={AdminAPI.knowledgeBase.list()}
                    loadingLabel="Loading knowledge-base documents..."
                    emptyTitle="No documentation in your scope"
                    emptyDescription="Knowledge-base documents will appear here once documentation exists for internal operations or an accessible client."
                    columns={[
                        {
                            key: "title",
                            label: "Document",
                            render: (value) => (
                                <span className="font-medium text-slate-100">
                                    {String(value)}
                                </span>
                            ),
                        },
                        { key: "section", label: "Section" },
                        { key: "ownership_type", label: "Ownership" },
                        { key: "client", label: "Client" },
                        { key: "version_count", label: "Versions" },
                        { key: "is_portal_visible", label: "Portal visible" },
                        { key: "updated_at", label: "Updated" },
                    ]}
                />
            </div>
        </Container>
    );
}

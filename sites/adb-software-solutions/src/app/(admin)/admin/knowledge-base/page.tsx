import { Container, PageHeader } from "@/components/ui";
import { KnowledgeBaseWorkspace } from "./KnowledgeBaseWorkspace";

import { parseKnowledgeContext } from "./context";

export default async function KnowledgeBasePage({
    searchParams,
}: {
    searchParams: Promise<{
        ownership_type?: string;
        client_id?: string;
        resource_id?: string;
        section_id?: string;
    }>;
}) {
    const params = await searchParams;
    const context = parseKnowledgeContext(
        params.ownership_type,
        params.client_id,
    );
    const resourceId =
        params.resource_id &&
        Number.isSafeInteger(Number(params.resource_id)) &&
        Number(params.resource_id) > 0
            ? Number(params.resource_id)
            : undefined;
    const sectionId =
        params.section_id &&
        Number.isSafeInteger(Number(params.section_id)) &&
        Number(params.section_id) > 0
            ? Number(params.section_id)
            : null;
    return (
        <Container className="py-8">
            <PageHeader
                title="Knowledge Base"
                description="Open a Client or Internal Knowledge Base to maintain its documentation."
            />
            <div className="mt-6">
                <KnowledgeBaseWorkspace
                    context={context}
                    resourceId={resourceId}
                    sectionId={sectionId}
                />
            </div>
        </Container>
    );
}

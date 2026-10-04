import { redirect } from "next/navigation";
import { parseKnowledgeContext } from "../../context";
import { Container, PageHeader } from "@/components/ui";
import { KnowledgeDocumentForm } from "../../KnowledgeDocumentForm";

export default async function NewKnowledgeDocumentPage({
    searchParams,
}: {
    searchParams: Promise<{
        ownership_type?: string;
        client_id?: string;
        section_id?: string;
    }>;
}) {
    const params = await searchParams;
    const context = parseKnowledgeContext(
        params.ownership_type,
        params.client_id,
    );
    if (!context) redirect("/admin/knowledge-base");
    const sectionId = params.section_id ? Number(params.section_id) : undefined;

    return (
        <Container className="py-8">
            <PageHeader
                eyebrow="Knowledge Base"
                title="New document"
                description="Create scoped operational documentation with immutable Markdown revision history."
            />
            <div className="mt-6">
                <KnowledgeDocumentForm
                    key={`${context.ownership_type}:${context.client_id}`}
                    initialContext={context}
                    initialSectionId={sectionId}
                />
            </div>
        </Container>
    );
}

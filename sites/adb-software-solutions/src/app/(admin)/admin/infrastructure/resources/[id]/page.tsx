import { KnowledgeBasePanel } from "@/components/admin/KnowledgeBasePanel";
import { MonitoringHealthPanel } from "@/components/admin/MonitoringHealthPanel";
import { Container } from "@/components/ui";
import { InfrastructureResourceWorkspace } from "./InfrastructureResourceWorkspace";
import { OperationalNestedPanel } from "./OperationalNestedPanel";

export default async function InfrastructureResourcePage({
    params,
}: {
    params: Promise<{ id: string }>;
}) {
    const { id } = await params;
    const resourceId = Number(id);

    return (
        <Container className="py-8">
            <div className="space-y-6">
                <InfrastructureResourceWorkspace resourceId={resourceId} />
                <OperationalNestedPanel resourceId={resourceId} />
                <MonitoringHealthPanel
                    resourceId={resourceId}
                    title="Resource technical health"
                    description="Current monitoring state for this infrastructure resource."
                />
                <KnowledgeBasePanel
                    resourceId={resourceId}
                    title="Resource documentation"
                    description="Current runbooks and Knowledge Base documents linked to this resource."
                />
            </div>
        </Container>
    );
}

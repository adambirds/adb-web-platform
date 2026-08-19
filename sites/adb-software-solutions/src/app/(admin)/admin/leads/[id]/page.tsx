import { Container } from "@/components/ui";
import { LeadWorkspace } from "./LeadWorkspace";

export default async function LeadPage({
    params,
}: {
    params: Promise<{ id: string }>;
}) {
    const { id } = await params;
    return (
        <Container className="py-8">
            <LeadWorkspace leadId={Number(id)} />
        </Container>
    );
}

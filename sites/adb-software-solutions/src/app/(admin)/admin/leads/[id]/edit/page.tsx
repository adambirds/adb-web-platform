import { Card, Container, PageHeader } from "@/components/ui";
import { LeadForm } from "../../LeadForm";

export const metadata = {
    title: "Edit Lead",
};

export default async function EditLeadPage({
    params,
}: {
    params: Promise<{ id: string }>;
}) {
    const { id } = await params;
    return (
        <Container className="py-8">
            <PageHeader
                eyebrow="Leads"
                title="Edit lead"
                description="Update contact details, pipeline position and internal follow-up notes."
            />
            <Card className="mt-6 p-6">
                <LeadForm leadId={Number(id)} />
            </Card>
        </Container>
    );
}

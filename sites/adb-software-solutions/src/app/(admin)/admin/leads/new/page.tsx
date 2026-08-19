import { Card, Container, PageHeader } from "@/components/ui";
import { LeadForm } from "../LeadForm";

export const metadata = {
    title: "New Lead",
};

export default function NewLeadPage() {
    return (
        <Container className="py-8">
            <PageHeader
                eyebrow="Leads"
                title="Create lead"
                description="Add a sales opportunity or enquiry to the shared CRM pipeline."
            />
            <Card className="mt-6 p-6">
                <LeadForm />
            </Card>
        </Container>
    );
}

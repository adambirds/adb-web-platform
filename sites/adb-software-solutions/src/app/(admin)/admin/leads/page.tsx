import { Container, PageHeader } from "@/components/ui";
import { LeadList } from "./LeadList";

export const metadata = {
    title: "Leads",
};

export default function LeadsPage() {
    return (
        <Container className="py-8">
            <PageHeader
                title="Leads"
                description="Sales enquiries across the ADB brands in one shared pipeline."
            />
            <div className="mt-6">
                <LeadList />
            </div>
        </Container>
    );
}

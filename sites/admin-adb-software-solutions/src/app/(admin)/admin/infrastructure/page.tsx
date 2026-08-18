import { Container, PageHeader } from "@/components/ui";
import { InfrastructureOverview } from "./InfrastructureOverview";

export const metadata = {
    title: "Infrastructure",
};

export default function InfrastructurePage() {
    return (
        <Container className="py-8">
            <PageHeader
                title="Infrastructure"
                description="Operational inventory for servers, databases, websites, domains, certificates, licences and applications."
            />
            <div className="mt-6">
                <InfrastructureOverview />
            </div>
        </Container>
    );
}

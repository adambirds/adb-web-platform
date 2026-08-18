import { Container, PageHeader } from "@/components/ui";
import { TicketingSettings } from "./TicketingSettings";

export const metadata = {
    title: "Settings",
};

export default function SettingsPage() {
    return (
        <Container className="py-8">
            <PageHeader
                title="Settings"
                description="Configure shared platform services, integrations and operational routing."
            />
            <div className="mt-6">
                <TicketingSettings />
            </div>
        </Container>
    );
}

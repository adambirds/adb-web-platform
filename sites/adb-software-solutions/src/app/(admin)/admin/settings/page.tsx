import { Container, PageHeader } from "@/components/ui";
import { TicketingSettings } from "./TicketingSettings";
import { VendorRoutingSettings } from "./VendorRoutingSettings";

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
            <div className="mt-6 space-y-6">
                <TicketingSettings />
                <VendorRoutingSettings />
            </div>
        </Container>
    );
}

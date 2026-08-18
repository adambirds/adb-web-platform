import { Container, PageHeader } from "@/components/ui";
import { TicketList } from "./TicketList";

export const metadata = {
    title: "Tickets",
};

export default function TicketsPage() {
    return (
        <Container className="py-8">
            <PageHeader
                title="Tickets"
                description="Customer, sales, accounts and operational conversations across every ADB brand."
            />
            <div className="mt-6">
                <TicketList />
            </div>
        </Container>
    );
}

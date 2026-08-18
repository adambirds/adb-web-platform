import { Container } from "@/components/ui";
import { TicketWorkspace } from "./TicketWorkspace";

export default async function TicketPage({
    params,
}: {
    params: Promise<{ id: string }>;
}) {
    const { id } = await params;

    return (
        <Container className="py-8">
            <TicketWorkspace ticketId={Number(id)} />
        </Container>
    );
}

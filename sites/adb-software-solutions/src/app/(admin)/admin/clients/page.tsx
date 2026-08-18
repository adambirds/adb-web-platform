import { Container, PageHeader } from "@/components/ui";
import { ClientList } from "./ClientList";

export const metadata = {
    title: "Clients",
};

export default function ClientsPage() {
    return (
        <Container className="py-8">
            <PageHeader
                title="Clients"
                description="Client accounts available within your current access scope."
            />
            <div className="mt-6">
                <ClientList />
            </div>
        </Container>
    );
}

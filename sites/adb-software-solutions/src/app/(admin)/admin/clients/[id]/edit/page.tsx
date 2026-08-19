import { Card, Container, PageHeader } from "@/components/ui";
import { ClientForm } from "../../ClientForm";

export const metadata = {
    title: "Edit Client",
};

export default async function EditClientPage({
    params,
}: {
    params: Promise<{ id: string }>;
}) {
    const { id } = await params;
    const clientId = Number(id);

    return (
        <Container className="py-8">
            <PageHeader
                eyebrow="Clients"
                title="Edit client"
                description="Update the client account details used across tickets, projects, infrastructure and reporting."
            />
            <Card className="mt-6 p-6">
                <ClientForm clientId={clientId} />
            </Card>
        </Container>
    );
}

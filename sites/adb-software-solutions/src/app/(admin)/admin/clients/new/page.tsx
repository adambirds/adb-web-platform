import { Card, Container, PageHeader } from "@/components/ui";
import { ClientForm } from "../ClientForm";

export const metadata = {
    title: "New Client",
};

export default function NewClientPage() {
    return (
        <Container className="py-8">
            <PageHeader
                eyebrow="Clients"
                title="Create client"
                description="Add a client account to the operational platform. Contacts and related work can be added after the account is created."
            />
            <Card className="mt-6 p-6">
                <ClientForm />
            </Card>
        </Container>
    );
}

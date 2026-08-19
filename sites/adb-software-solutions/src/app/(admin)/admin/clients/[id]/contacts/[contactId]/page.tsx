import { Card, Container, PageHeader } from "@/components/ui";
import { ClientContactForm } from "../../../ClientContactForm";

export const metadata = {
    title: "Manage Client Contact",
};

export default async function ClientContactPage({
    params,
}: {
    params: Promise<{ id: string; contactId: string }>;
}) {
    const { id, contactId } = await params;
    const clientId = Number(id);

    return (
        <Container className="py-8">
            <PageHeader
                eyebrow="Client contacts"
                title="Manage contact"
                description="Update contact details, responsibilities or deactivate this contact while retaining account history."
            />
            <Card className="mt-6 p-6">
                <ClientContactForm clientId={clientId} contactId={Number(contactId)} />
            </Card>
        </Container>
    );
}

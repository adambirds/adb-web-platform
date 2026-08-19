import { Card, Container, PageHeader } from "@/components/ui";
import { ClientContactForm } from "../../../ClientContactForm";

export const metadata = {
    title: "New Client Contact",
};

export default async function NewClientContactPage({
    params,
}: {
    params: Promise<{ id: string }>;
}) {
    const { id } = await params;
    const clientId = Number(id);

    return (
        <Container className="py-8">
            <PageHeader
                eyebrow="Client contacts"
                title="Add contact"
                description="Add a person to this client account and record their operational responsibilities."
            />
            <Card className="mt-6 p-6">
                <ClientContactForm clientId={clientId} />
            </Card>
        </Container>
    );
}

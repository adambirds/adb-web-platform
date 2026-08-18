import { Container } from "@/components/ui";
import { ContactWorkspace } from "./ContactWorkspace";

export default async function ContactPage({
    params,
}: {
    params: Promise<{ id: string; contactId: string }>;
}) {
    const { id, contactId } = await params;

    return (
        <Container className="py-8">
            <ContactWorkspace clientId={Number(id)} contactId={Number(contactId)} />
        </Container>
    );
}

import { ButtonLink, Container } from "@/components/ui";
import { ClientWorkspace } from "./ClientWorkspace";

export default async function ClientPage({
    params,
}: {
    params: Promise<{ id: string }>;
}) {
    const { id } = await params;
    const clientId = Number(id);

    return (
        <Container className="py-8">
            <div className="mb-4 flex flex-wrap justify-end gap-2">
                <ButtonLink href={`/admin/clients/${clientId}/contacts/new`}>
                    Add contact
                </ButtonLink>
                <ButtonLink href={`/admin/clients/${clientId}/edit`} variant="secondary">
                    Edit client
                </ButtonLink>
            </div>
            <ClientWorkspace clientId={clientId} />
        </Container>
    );
}

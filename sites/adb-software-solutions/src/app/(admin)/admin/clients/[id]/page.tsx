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
            <div className="mb-4 flex justify-end">
                <ButtonLink href={`/admin/clients/${clientId}/edit`} variant="secondary">
                    Edit client
                </ButtonLink>
            </div>
            <ClientWorkspace clientId={clientId} />
        </Container>
    );
}

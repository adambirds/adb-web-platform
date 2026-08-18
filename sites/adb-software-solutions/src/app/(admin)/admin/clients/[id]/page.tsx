import { Container } from "@/components/ui";
import { ClientWorkspace } from "./ClientWorkspace";

export default async function ClientPage({
    params,
}: {
    params: Promise<{ id: string }>;
}) {
    const { id } = await params;

    return (
        <Container className="py-8">
            <ClientWorkspace clientId={Number(id)} />
        </Container>
    );
}

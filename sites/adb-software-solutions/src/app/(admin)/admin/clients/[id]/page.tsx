import { ClientWorkspace } from "./ClientWorkspace";

export default async function ClientPage({
    params,
}: {
    params: Promise<{ id: string }>;
}) {
    const { id } = await params;
    return <ClientWorkspace clientId={Number(id)} />;
}

import { Container, PageHeader } from "@/components/ui";
import {
    InfrastructureRegister,
    RegisterColumn,
} from "./InfrastructureRegister";

interface InfrastructureRegisterPageProps {
    title: string;
    description: string;
    endpoint: string;
    columns: RegisterColumn[];
    emptyTitle: string;
    emptyDescription: string;
    loadingLabel: string;
}

export function InfrastructureRegisterPage({
    title,
    description,
    endpoint,
    columns,
    emptyTitle,
    emptyDescription,
    loadingLabel,
}: InfrastructureRegisterPageProps) {
    return (
        <Container className="py-8">
            <PageHeader title={title} description={description} />
            <div className="mt-6">
                <InfrastructureRegister
                    endpoint={endpoint}
                    columns={columns}
                    emptyTitle={emptyTitle}
                    emptyDescription={emptyDescription}
                    loadingLabel={loadingLabel}
                />
            </div>
        </Container>
    );
}

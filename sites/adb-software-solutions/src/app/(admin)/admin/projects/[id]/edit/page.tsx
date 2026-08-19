import { Card, Container, PageHeader } from "@/components/ui";
import { ProjectForm } from "../../ProjectForm";

export const metadata = {
    title: "Edit Project",
};

export default async function EditProjectPage({
    params,
}: {
    params: Promise<{ id: string }>;
}) {
    const { id } = await params;
    return (
        <Container className="py-8">
            <PageHeader
                eyebrow="Projects"
                title="Edit project"
                description="Update ownership, delivery dates, commercial details and project status."
            />
            <Card className="mt-6 p-6">
                <ProjectForm projectId={Number(id)} />
            </Card>
        </Container>
    );
}

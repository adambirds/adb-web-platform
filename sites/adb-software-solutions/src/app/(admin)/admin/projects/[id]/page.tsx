import { Container } from "@/components/ui";
import { ProjectWorkspace } from "./ProjectWorkspace";

export const metadata = {
    title: "Project",
};

export default async function ProjectPage({
    params,
}: {
    params: Promise<{ id: string }>;
}) {
    const { id } = await params;
    return (
        <Container className="py-8">
            <ProjectWorkspace projectId={Number(id)} />
        </Container>
    );
}

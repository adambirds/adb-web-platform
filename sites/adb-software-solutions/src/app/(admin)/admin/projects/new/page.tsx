import { Card, Container, PageHeader } from "@/components/ui";
import { ProjectForm } from "../ProjectForm";

export const metadata = {
    title: "New Project",
};

export default function NewProjectPage() {
    return (
        <Container className="py-8">
            <PageHeader
                eyebrow="Projects"
                title="Create project"
                description="Create a client delivery project or an internal ADB project."
            />
            <Card className="mt-6 p-6">
                <ProjectForm />
            </Card>
        </Container>
    );
}

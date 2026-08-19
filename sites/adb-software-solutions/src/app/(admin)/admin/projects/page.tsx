import { ButtonLink, Container, PageHeader } from "@/components/ui";
import { ProjectList } from "./ProjectList";

export const metadata = {
    title: "Projects",
};

export default function ProjectsPage() {
    return (
        <Container className="py-8">
            <PageHeader
                title="Projects"
                description="Client-owned and internal work visible to your staff account."
                actions={<ButtonLink href="/admin/projects/new">Add project</ButtonLink>}
            />
            <div className="mt-6">
                <ProjectList />
            </div>
        </Container>
    );
}

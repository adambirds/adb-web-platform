import { Container, PageHeader } from "@/components/ui";
import { TaskList } from "./TaskList";

export const metadata = {
    title: "Tasks",
};

export default function TasksPage() {
    return (
        <Container className="py-8">
            <PageHeader
                title="Tasks"
                description="Standalone internal work and client or project tasks across the platform."
            />
            <div className="mt-6">
                <TaskList />
            </div>
        </Container>
    );
}

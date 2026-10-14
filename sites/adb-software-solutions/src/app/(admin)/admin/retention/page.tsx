import { Container, PageHeader } from "@/components/ui";
import { RetentionWorkspace } from "./RetentionWorkspace";
export const metadata = { title: "Retention review" };
export default function RetentionPage() {
    return (
        <Container className="py-8">
            <PageHeader
                title="Retention review"
                description="Review unsuccessful leads after 36 months without activity. Nothing is deleted without approval."
            />
            <RetentionWorkspace />
        </Container>
    );
}

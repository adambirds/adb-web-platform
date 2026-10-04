import { Container } from "@/components/ui";
import { TechnologyWorkspace } from "./TechnologyWorkspace";

export const metadata = { title: "Technology Stack" };

export default function TechnologyStackPage() {
    return (
        <Container className="py-8">
            <TechnologyWorkspace />
        </Container>
    );
}

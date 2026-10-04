import { Container } from "@/components/ui";
import { InfrastructureResourcesWorkspace } from "./InfrastructureResourcesWorkspace";

export const metadata = {
    title: "Infrastructure Resources",
};

export default function InfrastructureResourcesPage() {
    return (
        <Container className="py-8">
            <InfrastructureResourcesWorkspace />
        </Container>
    );
}

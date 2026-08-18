import { AdminAPI } from "@/lib/api/endpoints";
import { InfrastructureRegisterPage } from "../InfrastructureRegisterPage";

export const metadata = { title: "Technology Stack" };

export default function TechnologyStackPage() {
    return (
        <InfrastructureRegisterPage
            title="Technology Stack"
            description="Technology inventory mapped to the websites that depend on it."
            endpoint={AdminAPI.infrastructure.techStack()}
            columns={[
                { key: "website", label: "Website" },
                { key: "technology", label: "Technology" },
                { key: "category", label: "Category" },
                { key: "version", label: "Version" },
            ]}
            emptyTitle="No technology stack records tracked"
            emptyDescription="Website technologies will appear here once they are recorded in the infrastructure inventory."
            loadingLabel="Loading technology stack..."
        />
    );
}

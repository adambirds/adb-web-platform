import { AdminAPI } from "@/lib/api/endpoints";
import { InfrastructureRegisterPage } from "../InfrastructureRegisterPage";

export const metadata = { title: "Applications" };

export default function ApplicationsPage() {
    return (
        <InfrastructureRegisterPage
            title="Applications"
            description="Logical applications and the infrastructure components they span."
            endpoint={AdminAPI.infrastructure.applications()}
            columns={[
                { key: "name", label: "Application" },
                { key: "app_type", label: "Type" },
                { key: "status", label: "Status" },
                { key: "website_count", label: "Websites" },
                { key: "server_count", label: "Servers" },
                { key: "database_count", label: "Databases" },
            ]}
            emptyTitle="No applications tracked"
            emptyDescription="Logical applications will appear here once they are linked to infrastructure components."
            loadingLabel="Loading applications..."
        />
    );
}

import { AdminAPI } from "@/lib/api/endpoints";
import { InfrastructureRegisterPage } from "../InfrastructureRegisterPage";

export const metadata = { title: "Bots" };

export default function BotsPage() {
    return (
        <InfrastructureRegisterPage
            title="Bots"
            description="Automation and chat-bot inventory with runtime and hosting context."
            endpoint={AdminAPI.infrastructure.bots()}
            columns={[
                { key: "name", label: "Bot" },
                { key: "platform", label: "Platform" },
                { key: "bot_type", label: "Type" },
                { key: "runtime", label: "Runtime" },
                { key: "hosting_location", label: "Hosting" },
            ]}
            emptyTitle="No bots tracked"
            emptyDescription="Bots and automations will appear here once they are added to the infrastructure inventory."
            loadingLabel="Loading bots..."
        />
    );
}

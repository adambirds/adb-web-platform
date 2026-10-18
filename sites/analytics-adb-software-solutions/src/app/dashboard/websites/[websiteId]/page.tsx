import {WebsiteDashboard} from "../../../../components/experience/WebsiteDashboard";
export default async function WebsitePage({
    params,
}: {
    params: Promise<{websiteId: string}>;
}) {
    const {websiteId} = await params;
    return <WebsiteDashboard websiteId={Number(websiteId)} />;
}

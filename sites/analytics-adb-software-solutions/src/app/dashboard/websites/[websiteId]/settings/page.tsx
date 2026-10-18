import {SettingsPage} from "../../../../../components/experience/SettingsPage";
export default async function Page({
    params,
}: {
    params: Promise<{websiteId: string}>;
}) {
    const {websiteId} = await params;
    return <SettingsPage websiteId={Number(websiteId)} />;
}

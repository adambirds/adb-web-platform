import {ExplorerPage} from "../../../../../components/experience/ExplorerPage";
export default async function Page({
    params,
}: {
    params: Promise<{websiteId: string}>;
}) {
    const {websiteId} = await params;
    return <ExplorerPage websiteId={Number(websiteId)} />;
}

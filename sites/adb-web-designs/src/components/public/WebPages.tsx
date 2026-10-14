import { BusinessPages } from "@adb/ui/public/BusinessPages";
import { site } from "@/content/site";
import { webPageCopy } from "@/content/page-design";
import { websitePolicies, policyDetails } from "@/content/policies";
export function WebPages({
    path,
    search,
}: {
    path: string[];
    search: Record<string, string | string[] | undefined>;
}) {
    return (
        <BusinessPages
            site={site}
            pageCopy={webPageCopy}
            policies={websitePolicies}
            policyDetails={policyDetails}
            path={path}
            search={search}
        />
    );
}

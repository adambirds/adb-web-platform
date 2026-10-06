import { MarketingPage } from "@/components/public/MarketingPage";
import { routeMetadata } from "@adb/ui/public/server";
import { site } from "@/content/site";
import type { Metadata } from "next";

type Props = {
    params: Promise<{ path: string[] }>;
    searchParams: Promise<Record<string, string | string[] | undefined>>;
};
export async function generateMetadata({
    params,
    searchParams,
}: Props): Promise<Metadata> {
    return routeMetadata(site, (await params).path, await searchParams);
}
export default async function Page({ params, searchParams }: Props) {
    return (
        <MarketingPage path={(await params).path} search={await searchParams} />
    );
}

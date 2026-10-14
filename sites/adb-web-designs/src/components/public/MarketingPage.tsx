import { notFound, permanentRedirect } from "next/navigation";
import {
    getBlogPost,
    getPortfolio,
    getCategories,
    PublicContentError,
} from "@adb/api-client/public";
import { apiOptions, optionalCollection } from "@adb/ui/public/server";
import { legacyAliases } from "@/content/legacy-aliases";
import { WebPages } from "./WebPages";
import { site } from "@/content/site";
export async function MarketingPage({
    path,
    search,
}: {
    path: string[];
    search: Record<string, string | string[] | undefined>;
}) {
    await legacyDestination(path);
    return <WebPages path={path} search={search} />;
}

export async function legacyDestination(path: string[]) {
    const destination = legacyAliases[`/${path.join("/")}`];
    if (!destination) return;
    try {
        if (destination.startsWith("/portfolio/")) {
            await getPortfolio(destination.split("/")[2], apiOptions(site));
        } else if (destination.startsWith("/blog/category/")) {
            const slug = destination.split("/")[3];
            const categories = await getCategories(apiOptions(site));
            if (!categories.some((item) => item.slug === slug)) notFound();
            const content = await optionalCollection("blog", site, {
                category: slug,
                page_size: 1,
            });
            if (!content.available) throw new Error("Content is unavailable");
            if (!content.total) notFound();
        } else {
            await getBlogPost(destination.split("/")[2], apiOptions(site));
        }
    } catch (failure) {
        if (failure instanceof PublicContentError && failure.status === 404)
            notFound();
        throw failure;
    }
    permanentRedirect(destination);
}

import { notFound, permanentRedirect } from "next/navigation";
import redirects from "../../../redirects.json";
import wordpressURLs from "@/content/wordpress-urls.json";
import { legacyAliases } from "@/content/legacy-aliases";
import { site } from "@/content/site";
import { legacyDestination } from "./MarketingPage";

const entries: Record<string, string> = wordpressURLs;
const identifiers = ["p", "page_id", "attachment_id"];
const retainedPaths = new Set([
    "/",
    "/blog/",
    "/services/",
    "/contact/",
    "/testimonials/",
    ...site.pages.map((page) => `/${page.slug}/`),
    ...site.areas.map((area) => `/${area.slug}/`),
]);

/** Old WordPress ID links must resolve to their content, never the homepage. */
export async function redirectWordPressEntry(
    search: Record<string, string | string[] | undefined>,
) {
    const keys = identifiers.filter((key) => search[key] !== undefined);
    if (!keys.length) return;
    if (keys.length !== 1) notFound();
    const key = keys[0];
    const id = search[key];
    if (typeof id !== "string" || !/^\d+$/.test(id)) notFound();
    const source = entries[`${key}:${id}`];
    if (!source) notFound();
    const normalised = source.replace(/\/$/, "");
    const rule = redirects.find((entry) => entry.source === normalised);
    if (rule) permanentRedirect(rule.destination);
    if (legacyAliases[normalised]) {
        await legacyDestination(source.split("/").filter(Boolean));
    }
    if (retainedPaths.has(source)) permanentRedirect(source);
    notFound();
}

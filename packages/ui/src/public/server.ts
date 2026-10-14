import {cache} from "react";
import type {Metadata, MetadataRoute} from "next";
import {notFound} from "next/navigation";
import {
    getCollection,
    getCategories,
    getBlogPost,
    getPortfolio,
    PublicContentError,
    type PublicApiOptions,
    type CollectionQuery,
    type PublicResources,
} from "@adb/api-client/public";
import type {PublicSite} from "./types";

export function apiOptions(site: PublicSite): PublicApiOptions {
    return {
        brand: site.brand,
        baseUrl:
            process.env.API_INTERNAL_URL ||
            process.env.NEXT_PUBLIC_API_URL ||
            (process.env.NODE_ENV === "production"
                ? "https://api.adbsoftwaresolutions.co.uk"
                : "http://localhost:8000"),
    };
}
export async function optionalCollection<K extends keyof PublicResources>(
    resource: K,
    site: PublicSite,
    query: CollectionQuery = {},
) {
    try {
        return {
            available: true,
            ...(await getCollection(resource, apiOptions(site), query)),
        };
    } catch {
        return {
            available: false,
            items: [] as PublicResources[K][],
            total: 0,
            page: query.page || 1,
            page_size: query.page_size || 9,
        };
    }
}
type HomeContent = {
    work: Awaited<ReturnType<typeof optionalCollection<"portfolio">>>;
    articles: Awaited<ReturnType<typeof optionalCollection<"blog">>>;
    testimonials: Awaited<
        ReturnType<typeof optionalCollection<"testimonials">>
    >;
    faqs: Awaited<ReturnType<typeof optionalCollection<"faqs">>>;
};
export const homeContent: (site: PublicSite) => Promise<HomeContent> = cache(
    async (site: PublicSite) => {
        const [work, articles, testimonials, faqs] = await Promise.all([
            optionalCollection("portfolio", site, {
                page_size: 2,
                featured: true,
            }).then(async (result) =>
                result.total
                    ? result
                    : optionalCollection("portfolio", site, {page_size: 2}),
            ),
            optionalCollection("blog", site, {page_size: 2}),
            optionalCollection("testimonials", site, {page_size: 2}),
            optionalCollection("faqs", site, {page_size: 4}),
        ]);
        return {work, articles, testimonials, faqs};
    },
);

export function pageMetadata(
    site: PublicSite,
    title: string,
    description: string,
    path: string,
    noindex = false,
): Metadata {
    const canonical = `${site.domain}${path}`;
    const social = `${site.domain}/social?title=${encodeURIComponent(title)}`;
    return {
        title,
        description,
        alternates: {canonical},
        robots: {index: !noindex, follow: true},
        openGraph: {
            type: "website",
            locale: "en_GB",
            url: canonical,
            siteName: site.name,
            title,
            description,
            images: [
                {
                    url: social,
                    width: 1200,
                    height: 630,
                    alt: `${title} — ${site.name}`,
                },
            ],
        },
        twitter: {
            card: "summary_large_image",
            title,
            description,
            images: [social],
        },
    };
}
export function siteMetadata(site: PublicSite): Metadata {
    return {
        ...pageMetadata(site, site.name, site.description, "/"),
        title: {default: site.name, template: `%s | ${site.name}`},
        metadataBase: new URL(site.domain),
        applicationName: site.name,
    };
}
export function businessSchema(site: PublicSite): Record<string, unknown> {
    return {
        "@context": "https://schema.org",
        "@type": "ProfessionalService",
        "@id": `${site.domain}/#business`,
        name: site.name,
        url: site.domain,
        description: site.description,
        image: `${site.domain}/social`,
        logo: `${site.domain}/brand/logo-light.png`,
        areaServed: [
            {"@type": "City", name: "Manchester"},
            {"@type": "Country", name: "United Kingdom"},
            {"@type": "Country", name: "Australia"},
            {"@type": "Country", name: "United States"},
        ],
        founder: {"@type": "Person", name: "Adam Birds"},
    };
}
export function breadcrumbSchema(
    site: PublicSite,
    title: string,
    path: string,
): Record<string, unknown> {
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        itemListElement: [
            {"@type": "ListItem", position: 1, name: "Home", item: site.domain},
            {
                "@type": "ListItem",
                position: 2,
                name: title,
                item: `${site.domain}${path}`,
            },
        ],
    };
}

export const detailContent = cache(
    async (site: PublicSite, resource: "blog" | "portfolio", slug: string) => {
        try {
            return resource === "blog"
                ? await getBlogPost(slug, apiOptions(site))
                : await getPortfolio(slug, apiOptions(site));
        } catch (failure) {
            if (failure instanceof PublicContentError && failure.status === 404)
                notFound();
            throw failure;
        }
    },
);

export async function routeMetadata(
    site: PublicSite,
    path: string[],
    search: Record<string, string | string[] | undefined>,
): Promise<Metadata> {
    const route = `/${path.join("/")}/`;
    const service =
        path[0] === "services" && path.length === 2
            ? site.services.find((item) => item.slug === path[1])
            : undefined;
    if (service)
        return pageMetadata(site, service.title, service.description, route);
    const area =
        path.length === 1
            ? site.areas.find((item) => item.slug === path[0])
            : undefined;
    if (area) return pageMetadata(site, area.title, area.description, route);
    const page =
        path.length === 1
            ? site.pages.find((item) => item.slug === path[0])
            : undefined;
    if (page)
        return pageMetadata(
            site,
            page.title,
            page.description,
            route,
            page.noindex,
        );
    if (path.length === 2 && (path[0] === "blog" || path[0] === "portfolio")) {
        const item = await detailContent(site, path[0], path[1]);
        const description =
            "excerpt" in item
                ? item.meta_description || item.excerpt
                : item.meta_description || item.description;
        const result = pageMetadata(
            site,
            item.title,
            description.slice(0, 160),
            route,
            false,
        );
        if ("excerpt" in item)
            result.openGraph = {
                ...result.openGraph,
                type: "article",
                publishedTime: item.published_at || undefined,
                modifiedTime: item.updated_at,
            };
        return result;
    }
    const special: Record<string, [string, string]> = {
        services: ["Services", site.description],
        contact: [site.contact.title, site.contact.introduction],
        "contact/thank-you": [
            "Enquiry received",
            "Your enquiry has been received.",
        ],
        portfolio: [
            "Portfolio",
            `Projects and case studies from ${site.name}.`,
        ],
        blog: ["Blog", `Articles and practical notes from ${site.name}.`],
        testimonials: ["Client feedback", `Client feedback for ${site.name}.`],
        faqs: [
            "Frequently asked questions",
            `Questions about ${site.name} services and working arrangements.`,
        ],
    };
    if (path[0] === "blog" && path[1] === "category" && path.length === 3) {
        const categories = await getCategories(apiOptions(site));
        const category = categories.find((item) => item.slug === path[2]);
        if (!category) notFound();
        const content = await optionalCollection("blog", site, {
            category: category.slug,
            page_size: 1,
        });
        return pageMetadata(
            site,
            category.name,
            category.description ||
                `Articles about ${category.name} from ${site.name}.`,
            Number(search.page) > 1
                ? `${route}?page=${Number(search.page)}`
                : route,
            !content.total || Boolean(search.q),
        );
    }
    const entry = special[path.join("/")];
    if (!entry) notFound();
    const resource = ["portfolio", "blog", "testimonials", "faqs"].includes(
        path[0],
    )
        ? (path[0] as keyof PublicResources)
        : null;
    const content = resource
        ? await optionalCollection(resource, site, {page_size: 1})
        : null;
    const pageNumber = Number(search.page);
    const canonical =
        Number.isInteger(pageNumber) && pageNumber > 1
            ? `${route}?page=${pageNumber}`
            : route;
    return pageMetadata(
        site,
        entry[0],
        entry[1],
        canonical,
        path.join("/") === "contact/thank-you" ||
            Boolean(search.q) ||
            Boolean(content && !content.total),
    );
}

export async function publicSitemap(
    site: PublicSite,
): Promise<MetadataRoute.Sitemap> {
    const routes = [
        "/",
        "/services/",
        "/contact/",
        ...site.pages
            .filter((page) => !page.noindex)
            .map((page) => `/${page.slug}/`),
        ...site.services.map((service) => `/services/${service.slug}/`),
        ...site.areas.map((area) => `/${area.slug}/`),
    ];
    const result: MetadataRoute.Sitemap = routes.map((route) => ({
        url: `${site.domain}${route}`,
    }));
    for (const resource of [
        "portfolio",
        "blog",
        "testimonials",
        "faqs",
    ] as const) {
        const first = await optionalCollection(resource, site, {page_size: 50});
        if (!first.available || !first.total) continue;
        result.push({url: `${site.domain}/${resource}/`});
        if (resource !== "portfolio" && resource !== "blog") continue;
        for (let page = 1; page <= Math.ceil(first.total / 50); page++) {
            const collection =
                page === 1
                    ? first
                    : await optionalCollection(resource, site, {
                          page_size: 50,
                          page,
                      });
            for (const item of collection.items)
                if ("slug" in item)
                    result.push({
                        url: `${site.domain}/${resource}/${item.slug}/`,
                        lastModified: new Date(item.updated_at),
                    });
        }
    }
    try {
        const categories = await getCategories(apiOptions(site));
        for (const category of categories) {
            const collection = await optionalCollection("blog", site, {
                category: category.slug,
                page_size: 1,
            });
            if (collection.total)
                result.push({
                    url: `${site.domain}/blog/category/${category.slug}/`,
                });
        }
    } catch {
        /* An unavailable CMS does not hide the code-owned site. */
    }
    return result;
}

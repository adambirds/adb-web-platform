/** Shared, brand-scoped public CMS contracts. No browser credentials are sent. */
export type PublicBrand =
    "adb-software-solutions" | "adb-web-designs" | "adb-technology";
export interface Taxonomy {
    id: number;
    name: string;
    slug: string;
    description?: string;
}
export interface Portfolio {
    id: number;
    title: string;
    slug: string;
    description: string;
    challenge: string;
    solution: string;
    results: string;
    technologies: string[];
    published: boolean;
    featured: boolean;
    service_slugs: string[];
    meta_description: string;
    image_url: string | null;
    featured_image_url: string | null;
    image_alt: string;
    featured_image_alt: string;
    project_url: string | null;
    github_url: string | null;
    created_at: string;
    updated_at: string;
}
export interface BlogPost {
    id: number;
    title: string;
    slug: string;
    excerpt: string;
    content: string;
    author: string;
    published_at: string | null;
    updated_at: string;
    featured_image_url: string | null;
    featured_image_alt: string;
    meta_description: string;
    categories: Taxonomy[];
    tags: Taxonomy[];
}
export interface Testimonial {
    id: number;
    quote: string;
    client_name: string;
    company: string;
    job_title: string;
    image_url: string | null;
    image_alt: string;
}
export interface FAQ {
    id: number;
    question: string;
    answer: string;
    category: Taxonomy;
    service_slugs: string[];
}
export interface Collection<T> {
    items: T[];
    total: number;
    page: number;
    page_size: number;
}
export interface PublicResources {
    portfolio: Portfolio;
    blog: BlogPost;
    testimonials: Testimonial;
    faqs: FAQ;
}
export interface PublicApiOptions {
    baseUrl: string;
    brand: PublicBrand;
}
export interface CollectionQuery {
    page?: number;
    page_size?: number;
    category?: string;
    q?: string;
    service?: string;
    featured?: boolean;
}

export class PublicContentError extends Error {
    constructor(public readonly status: number) {
        super(`Public content request failed (${status}).`);
        this.name = "PublicContentError";
    }
}

export function publicApiUrl(
    path: string,
    options: PublicApiOptions,
    query: Record<string, string> = {},
): URL {
    const base = options.baseUrl.replace(/\/$/, "");
    const url = new URL(`${base}/api/public/${path}`);
    url.searchParams.set("brand", options.brand);
    for (const [key, value] of Object.entries(query))
        url.searchParams.set(key, value);
    return url;
}

export async function fetchPublicContent<T>(url: URL): Promise<T> {
    let response: Response;
    try {
        response = await fetch(url, {
            cache: "no-store",
            signal: AbortSignal.timeout(6000),
            credentials: "omit",
        });
    } catch {
        throw new PublicContentError(503);
    }
    if (!response.ok) throw new PublicContentError(response.status);
    return response.json() as Promise<T>;
}

export function getCollection<K extends keyof PublicResources>(
    resource: K,
    options: PublicApiOptions,
    query: CollectionQuery = {},
): Promise<Collection<PublicResources[K]>> {
    const params = Object.fromEntries(
        Object.entries(query)
            .filter(([, value]) => value !== undefined)
            .map(([key, value]) => [key, String(value)]),
    );
    return fetchPublicContent(
        publicApiUrl(`collections/${resource}`, options, params),
    );
}
export function getBlogPost(
    slug: string,
    options: PublicApiOptions,
): Promise<BlogPost> {
    return fetchPublicContent(
        publicApiUrl(`blog/posts/${encodeURIComponent(slug)}`, options),
    );
}
export function getPortfolio(
    slug: string,
    options: PublicApiOptions,
): Promise<Portfolio> {
    return fetchPublicContent(
        publicApiUrl(`portfolio/${encodeURIComponent(slug)}`, options),
    );
}
export function getCategories(options: PublicApiOptions): Promise<Taxonomy[]> {
    return fetchPublicContent(publicApiUrl("blog/categories", options));
}

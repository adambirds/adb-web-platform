const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export interface PortfolioItem {
    id: number;
    title: string;
    slug: string;
    description: string;
    challenge: string;
    solution: string;
    results: string;
    technologies: string[];
    project_url?: string | null;
    github_url?: string | null;
    image_url?: string | null;
    featured_image_url?: string | null;
    featured: boolean;
}

export interface TestimonialItem {
    id: number;
    quote: string;
    client_name: string;
    company: string;
    job_title: string;
    rating: number;
    featured: boolean;
}

export interface BlogCategoryItem {
    id: number;
    name: string;
    slug: string;
    description: string;
}

export interface BlogTagItem {
    id: number;
    name: string;
    slug: string;
}

export interface BlogPostItem {
    id: number;
    title: string;
    slug: string;
    excerpt: string;
    content: string;
    featured_image_url?: string | null;
    author: string;
    published: boolean;
    featured: boolean;
    categories: BlogCategoryItem[];
    tags: BlogTagItem[];
    meta_description: string;
    meta_keywords: string;
    created_at: string;
    published_at?: string | null;
    updated_at: string;
}

export interface FAQCategoryItem {
    id: number;
    name: string;
    slug: string;
    description: string;
    order: number;
}

export interface FAQItem {
    id: number;
    question: string;
    answer: string;
    category: FAQCategoryItem;
    order: number;
    created_at: string;
    updated_at: string;
}

async function fetchPublic<T>(url: string): Promise<T> {
    const response = await fetch(url, {
        next: { revalidate: 60 },
    });

    if (!response.ok) {
        throw new Error(`Public API error: ${response.status}`);
    }

    return response.json();
}

export function getPortfolio(featured?: boolean): Promise<PortfolioItem[]> {
    const url = new URL(`${API_BASE_URL}/public/portfolio/`);
    if (featured !== undefined) {
        url.searchParams.set("featured", String(featured));
    }
    return fetchPublic<PortfolioItem[]>(url.toString());
}

export function getPortfolioBySlug(slug: string): Promise<PortfolioItem> {
    return fetchPublic<PortfolioItem>(
        `${API_BASE_URL}/public/portfolio/${slug}/`,
    );
}

export function getTestimonials(
    featured?: boolean,
): Promise<TestimonialItem[]> {
    const url = new URL(`${API_BASE_URL}/public/testimonials/`);
    if (featured !== undefined) {
        url.searchParams.set("featured", String(featured));
    }
    return fetchPublic<TestimonialItem[]>(url.toString());
}

export function getBlogPosts(featured?: boolean): Promise<BlogPostItem[]> {
    const url = new URL(`${API_BASE_URL}/public/blog/posts/`);
    if (featured !== undefined) {
        url.searchParams.set("featured", String(featured));
    }
    return fetchPublic<BlogPostItem[]>(url.toString());
}

export function getBlogPostBySlug(slug: string): Promise<BlogPostItem> {
    return fetchPublic<BlogPostItem>(
        `${API_BASE_URL}/public/blog/posts/${slug}/`,
    );
}

export function getFaqs(category?: string): Promise<FAQItem[]> {
    const url = new URL(`${API_BASE_URL}/public/faqs/`);
    if (category) {
        url.searchParams.set("category", category);
    }
    return fetchPublic<FAQItem[]>(url.toString());
}

export function getFaqCategories(): Promise<FAQCategoryItem[]> {
    return fetchPublic<FAQCategoryItem[]>(
        `${API_BASE_URL}/public/faqs/categories/`,
    );
}

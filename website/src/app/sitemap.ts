import { getBlogPosts, getPortfolio } from "@/lib/api/public";
import type { MetadataRoute } from "next";

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
    // Static pages
    const staticPages: MetadataRoute.Sitemap = [
        {
            url: BASE_URL,
            lastModified: new Date(),
            changeFrequency: "daily",
            priority: 1.0,
        },
        {
            url: `${BASE_URL}/about`,
            lastModified: new Date(),
            changeFrequency: "monthly",
            priority: 0.8,
        },
        {
            url: `${BASE_URL}/services`,
            lastModified: new Date(),
            changeFrequency: "monthly",
            priority: 0.9,
        },
        {
            url: `${BASE_URL}/portfolio`,
            lastModified: new Date(),
            changeFrequency: "monthly",
            priority: 0.8,
        },
        {
            url: `${BASE_URL}/blog`,
            lastModified: new Date(),
            changeFrequency: "weekly",
            priority: 0.7,
        },
        {
            url: `${BASE_URL}/faqs`,
            lastModified: new Date(),
            changeFrequency: "monthly",
            priority: 0.6,
        },
        {
            url: `${BASE_URL}/contact`,
            lastModified: new Date(),
            changeFrequency: "monthly",
            priority: 0.6,
        },
    ];
    let portfolioEntries: MetadataRoute.Sitemap = [];
    let blogEntries: MetadataRoute.Sitemap = [];

    try {
        const [portfolio, posts] = await Promise.all([
            getPortfolio(),
            getBlogPosts(),
        ]);
        portfolioEntries = portfolio.map((item: { slug: string }) => ({
            url: `${BASE_URL}/portfolio/${item.slug}`,
            lastModified: new Date(),
            changeFrequency: "monthly",
            priority: 0.6,
        }));
        blogEntries = posts.map((post: { slug: string }) => ({
            url: `${BASE_URL}/blog/${post.slug}`,
            lastModified: new Date(),
            changeFrequency: "weekly",
            priority: 0.6,
        }));
    } catch (error) {
        console.error("Sitemap API fetch failed", error);
    }

    return [...staticPages, ...portfolioEntries, ...blogEntries];
}

import Image from "next/image";
import Link from "next/link";
import {notFound} from "next/navigation";
import {
    getCategories,
    type Portfolio,
    type BlogPost,
    type Testimonial,
    type FAQ,
} from "@adb/api-client/public";
import type {PublicSite} from "./types";
import {
    apiOptions,
    optionalCollection,
    detailContent,
    breadcrumbSchema,
} from "./server";
import {Markdown} from "./Markdown";
import {JsonLd} from "./JsonLd";

export function EditorialImage({
    src,
    alt,
    priority = false,
}: {
    src: string;
    alt: string;
    priority?: boolean;
}) {
    return (
        <Image
            src={src}
            alt={alt}
            width={1200}
            height={800}
            className="editorial-image"
            priority={priority}
            unoptimized
        />
    );
}
export function WorkCard({item}: {item: Portfolio}) {
    const image = item.featured_image_url || item.image_url;
    return (
        <article className="work-card">
            {image ? (
                <Link href={`/portfolio/${item.slug}/`}>
                    <EditorialImage
                        src={image}
                        alt={
                            item.featured_image_alt ||
                            item.image_alt ||
                            item.title
                        }
                    />
                </Link>
            ) : null}
            <div>
                <h3>
                    <Link href={`/portfolio/${item.slug}/`}>{item.title}</Link>
                </h3>
                <p>{item.description}</p>
                <span className="content-tags">
                    {item.technologies.join(" · ")}
                </span>
            </div>
        </article>
    );
}
export function ArticleCard({item}: {item: BlogPost}) {
    return (
        <article className="article-card">
            {item.featured_image_url ? (
                <Link href={`/blog/${item.slug}/`}>
                    <EditorialImage
                        src={item.featured_image_url}
                        alt={item.featured_image_alt || item.title}
                    />
                </Link>
            ) : null}
            <div>
                <p className="content-tags">
                    {item.categories
                        .map((category) => category.name)
                        .join(" / ")}
                </p>
                <h3>
                    <Link href={`/blog/${item.slug}/`}>{item.title}</Link>
                </h3>
                <p>{item.excerpt}</p>
                <Link className="text-link" href={`/blog/${item.slug}/`}>
                    Read article →
                </Link>
            </div>
        </article>
    );
}
export function Quote({item}: {item: Testimonial}) {
    return (
        <figure className="client-quote">
            {item.image_url ? (
                <Image
                    src={item.image_url}
                    alt={item.image_alt || item.client_name}
                    width={64}
                    height={64}
                    unoptimized
                    className="quote-portrait"
                />
            ) : null}
            <blockquote>
                <p>{item.quote}</p>
            </blockquote>
            <figcaption>
                {item.client_name}
                {item.company ? ` · ${item.company}` : ""}
                {item.job_title ? <span>{item.job_title}</span> : null}
            </figcaption>
        </figure>
    );
}
export function Questions({items}: {items: FAQ[]}) {
    return (
        <div>
            {items.length ? (
                <JsonLd
                    data={{
                        "@context": "https://schema.org",
                        "@type": "FAQPage",
                        mainEntity: items.map((item) => ({
                            "@type": "Question",
                            name: item.question,
                            acceptedAnswer: {
                                "@type": "Answer",
                                text: item.answer,
                            },
                        })),
                    }}
                />
            ) : null}
            {items.map((item) => (
                <details className="faq-row" key={item.id}>
                    <summary>{item.question}</summary>
                    <Markdown>{item.answer}</Markdown>
                </details>
            ))}
        </div>
    );
}
function collectionNumber(value: string | string[] | undefined) {
    const number = Number(value || 1);
    return Number.isInteger(number) && number > 0 ? number : 1;
}
export async function EditorialCollection({
    site,
    resource,
    search,
    category,
}: {
    site: PublicSite;
    resource: "blog" | "portfolio" | "testimonials" | "faqs";
    search: Record<string, string | string[] | undefined>;
    category?: string;
}) {
    const page = collectionNumber(search.page);
    const q = typeof search.q === "string" ? search.q.slice(0, 200) : "";
    const response = await optionalCollection(resource, site, {
        page,
        page_size: 9,
        q,
        category,
    });
    if (response.available && page > 1 && !response.items.length) notFound();
    const title = {
        blog: "From the blog",
        portfolio: "Selected work",
        testimonials: "Client feedback",
        faqs: "Frequently asked questions",
    }[resource];
    const description = {
        blog: "Practical articles from the work, and notes on the decisions behind it.",
        portfolio:
            "Real projects, their starting point and the work delivered.",
        testimonials: "Feedback from people who have worked with the business.",
        faqs: "Questions about the services and working arrangements.",
    }[resource];
    const categories =
        resource === "blog"
            ? await getCategories(apiOptions(site)).catch(() => [])
            : [];
    const path = category ? `/blog/category/${category}/` : `/${resource}/`;
    return (
        <>
            <header className="page-heading">
                <p className="business-label">{site.name}</p>
                <h1>
                    {category
                        ? categories.find((item) => item.slug === category)
                              ?.name || title
                        : title}
                </h1>
                <p>{description}</p>
            </header>
            <section className="shell collection-section">
                {resource === "blog" || resource === "portfolio" ? (
                    <form action={path} className="collection-search">
                        <label htmlFor="content-search">
                            Search{" "}
                            {resource === "blog" ? "articles" : "projects"}
                        </label>
                        <div>
                            <input
                                id="content-search"
                                name="q"
                                defaultValue={q}
                                maxLength={200}
                                type="search"
                            />
                            <button className="angled-button" type="submit">
                                Search
                            </button>
                        </div>
                    </form>
                ) : null}
                {categories.length ? (
                    <nav
                        className="category-links"
                        aria-label="Article categories"
                    >
                        <Link href="/blog/">All articles</Link>
                        {categories.map((item) => (
                            <Link
                                key={item.id}
                                href={`/blog/category/${item.slug}/`}
                                aria-current={
                                    category === item.slug ? "page" : undefined
                                }
                            >
                                {item.name}
                            </Link>
                        ))}
                    </nav>
                ) : null}
                {!response.available ? (
                    <div className="public-empty">
                        <h2>Content is temporarily unavailable</h2>
                        <p>
                            Please try again, or{" "}
                            <Link href="/contact/">get in touch</Link> about
                            your project.
                        </p>
                    </div>
                ) : !response.items.length ? (
                    <div className="public-empty">
                        <h2>
                            {q
                                ? "No matching results"
                                : "Have a project in mind?"}
                        </h2>
                        <p>
                            {q
                                ? "Try another search or browse the collection."
                                : "You can get in touch to discuss the work you need."}
                        </p>
                        <Link
                            href={q ? path : "/contact/"}
                            className="text-link"
                        >
                            {q ? "Clear search" : "Discuss your project"} →
                        </Link>
                    </div>
                ) : (
                    <div
                        className={
                            resource === "faqs"
                                ? "faq-collection"
                                : "collection-grid"
                        }
                    >
                        {response.items.map((item) =>
                            resource === "portfolio" ? (
                                <WorkCard
                                    key={item.id}
                                    item={item as Portfolio}
                                />
                            ) : resource === "blog" ? (
                                <ArticleCard
                                    key={item.id}
                                    item={item as BlogPost}
                                />
                            ) : resource === "testimonials" ? (
                                <Quote
                                    key={item.id}
                                    item={item as Testimonial}
                                />
                            ) : (
                                <Questions
                                    key={item.id}
                                    items={[item as FAQ]}
                                />
                            ),
                        )}
                    </div>
                )}
                {response.total > 9 ? (
                    <nav className="pagination" aria-label="Pagination">
                        {page > 1 ? (
                            <Link
                                href={`${path}?${new URLSearchParams({page: String(page - 1), ...(q ? {q} : {})})}`}
                            >
                                ← Previous
                            </Link>
                        ) : (
                            <span />
                        )}
                        <span>
                            Page {page} of {Math.ceil(response.total / 9)}
                        </span>
                        {page * 9 < response.total ? (
                            <Link
                                href={`${path}?${new URLSearchParams({page: String(page + 1), ...(q ? {q} : {})})}`}
                            >
                                Next →
                            </Link>
                        ) : (
                            <span />
                        )}
                    </nav>
                ) : null}
            </section>
        </>
    );
}
export async function EditorialDetail({
    site,
    resource,
    slug,
}: {
    site: PublicSite;
    resource: "blog" | "portfolio";
    slug: string;
}) {
    const item = await detailContent(site, resource, slug);
    const path = `/${resource}/${slug}/`;
    const image =
        item.featured_image_url ||
        ("image_url" in item ? item.image_url : null);
    const schema: Record<string, unknown> = {
        "@context": "https://schema.org",
        "@type": "excerpt" in item ? "BlogPosting" : "CreativeWork",
        headline: item.title,
        name: item.title,
        url: `${site.domain}${path}`,
        description: "excerpt" in item ? item.excerpt : item.description,
        dateModified: item.updated_at,
        publisher: {"@id": `${site.domain}/#business`},
    };
    if ("excerpt" in item) {
        schema.author = {"@type": "Person", name: item.author};
        if (item.published_at) schema.datePublished = item.published_at;
    }
    if (image) schema.image = image;
    return (
        <>
            <JsonLd data={schema} />
            <JsonLd data={breadcrumbSchema(site, item.title, path)} />
            <header className="page-heading">
                <Link className="business-label" href={`/${resource}/`}>
                    ← {resource === "blog" ? "All articles" : "All projects"}
                </Link>
                <h1>{item.title}</h1>
                <p>{"excerpt" in item ? item.excerpt : item.description}</p>
                {"excerpt" in item ? (
                    <p className="article-byline">
                        By {item.author}
                        {item.published_at
                            ? ` · ${new Date(item.published_at).toLocaleDateString("en-GB", {day: "numeric", month: "long", year: "numeric", timeZone: "Europe/London"})}`
                            : ""}
                    </p>
                ) : null}
            </header>
            <article className="shell detail-article">
                {image ? (
                    <EditorialImage
                        src={image}
                        alt={
                            item.featured_image_alt ||
                            ("image_alt" in item ? item.image_alt : "") ||
                            item.title
                        }
                        priority
                    />
                ) : null}
                {"excerpt" in item ? (
                    <Markdown>{item.content}</Markdown>
                ) : (
                    <>
                        <section>
                            <h2>The starting point</h2>
                            <Markdown>{item.challenge}</Markdown>
                        </section>
                        <section>
                            <h2>The work</h2>
                            <Markdown>{item.solution}</Markdown>
                        </section>
                        <section>
                            <h2>The outcome</h2>
                            <Markdown>{item.results}</Markdown>
                        </section>
                        <p className="content-tags">
                            {item.technologies.join(" · ")}
                        </p>
                        {item.project_url ? (
                            <a
                                className="text-link"
                                href={item.project_url}
                                rel="noopener noreferrer"
                            >
                                Visit the project ↗
                            </a>
                        ) : null}
                        {item.github_url ? (
                            <a
                                className="text-link"
                                href={item.github_url}
                                rel="noopener noreferrer"
                            >
                                Source repository ↗
                            </a>
                        ) : null}
                    </>
                )}
                <aside className="detail-enquiry">
                    <h2>Discuss a related project</h2>
                    <Link href="/contact/" className="angled-button">
                        Get in touch →
                    </Link>
                </aside>
            </article>
        </>
    );
}

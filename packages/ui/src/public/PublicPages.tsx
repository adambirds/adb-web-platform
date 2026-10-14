import Link from "next/link";
import Image from "next/image";
import {notFound} from "next/navigation";
import type {PublicSite} from "./types";
import {ContentSections} from "@adb/ui/public/ContentSections";
import {ContactForm} from "@adb/ui/public/ContactForm";
import {JsonLd} from "@adb/ui/public/JsonLd";
import {
    EditorialCollection,
    EditorialDetail,
    Questions,
    WorkCard,
} from "@adb/ui/public/Editorial";
import {optionalCollection, breadcrumbSchema} from "@adb/ui/public/server";
import type {ServiceCopy, AreaCopy, PageCopy} from "@adb/ui/public/types";

export async function PublicPages({
    site,
    path,
    search,
}: {
    site: PublicSite;
    path: string[];
    search: Record<string, string | string[] | undefined>;
}) {
    const key = path.join("/");
    if (path[0] === "services" && path.length === 2) {
        const service = site.services.find((item) => item.slug === path[1]);
        if (!service) notFound();
        return <ServicePage site={site} service={service} />;
    }
    if (path.length === 1) {
        const area = site.areas.find((item) => item.slug === path[0]);
        if (area) return <AreaPage site={site} area={area} />;
        const page = site.pages.find((item) => item.slug === path[0]);
        if (page) return <InfoPage site={site} page={page} />;
    }
    if (key === "services") return <ServicesPage site={site} />;
    if (key === "contact")
        return (
            <>
                <header className="page-heading">
                    <p className="business-label">{site.name}</p>
                    <h1>{site.contact.title}</h1>
                    <p>{site.contact.introduction}</p>
                </header>
                <section className="shell contact-page">
                    <aside>
                        <h2>A useful starting point</h2>
                        <p>{site.contact.guidance}</p>
                        <p>
                            Tell me about your existing setup and what you want
                            to change. If you have a real deadline, include it
                            in the message.
                        </p>
                        <Link href="/working-together/" className="text-link">
                            How the work is arranged →
                        </Link>
                    </aside>
                    <ContactForm services={site.services} />
                </section>
            </>
        );
    if (key === "contact/thank-you")
        return (
            <section className="shell thank-you">
                <p className="business-label">{site.name}</p>
                <h1>Your enquiry has been received</h1>
                <p>
                    Thank you for getting in touch. I’ll review your message and
                    respond to discuss the next step.
                </p>
                <Link href="/" className="angled-button">
                    Back to the homepage →
                </Link>
            </section>
        );
    if (
        path.length === 1 &&
        (path[0] === "blog" ||
            path[0] === "portfolio" ||
            path[0] === "faqs" ||
            path[0] === "testimonials")
    )
        return (
            <EditorialCollection
                site={site}
                resource={path[0]}
                search={search}
            />
        );
    if (path.length === 2 && (path[0] === "blog" || path[0] === "portfolio"))
        return (
            <EditorialDetail site={site} resource={path[0]} slug={path[1]} />
        );
    if (path[0] === "blog" && path[1] === "category" && path.length === 3)
        return (
            <EditorialCollection
                site={site}
                resource="blog"
                category={path[2]}
                search={search}
            />
        );
    notFound();
}

function ServicesPage({site}: {site: PublicSite}) {
    return (
        <>
            <header className="page-heading">
                <p className="business-label">{site.name}</p>
                <h1>Services</h1>
                <p>{site.description}</p>
            </header>
            <section className="shell service-directory">
                <div className="service-index">
                    {site.services.map((service) => (
                        <article key={service.slug}>
                            <h2>
                                <Link href={`/services/${service.slug}/`}>
                                    {service.title}
                                </Link>
                            </h2>
                            <p>{service.introduction}</p>
                            <Link
                                className="text-link"
                                href={`/services/${service.slug}/`}
                            >
                                Explore this service →
                            </Link>
                        </article>
                    ))}
                </div>
                <div className="enquiry-band">
                    <h2>Not sure where your project fits?</h2>
                    <p>
                        Describe the work you need and the systems already
                        involved.
                    </p>
                    <Link className="angled-button" href="/contact/">
                        Discuss your project →
                    </Link>
                </div>
            </section>
        </>
    );
}

async function ServicePage({
    site,
    service,
}: {
    site: PublicSite;
    service: ServiceCopy;
}) {
    const [questions, work] = await Promise.all([
        optionalCollection("faqs", site, {service: service.slug, page_size: 6}),
        optionalCollection("portfolio", site, {
            service: service.slug,
            page_size: 2,
        }),
    ]);
    const path = `/services/${service.slug}/`;
    return (
        <>
            <JsonLd
                data={{
                    "@context": "https://schema.org",
                    "@type": "Service",
                    name: service.title,
                    description: service.description,
                    url: `${site.domain}${path}`,
                    provider: {"@id": `${site.domain}/#business`},
                    serviceType: service.title,
                }}
            />
            <JsonLd data={breadcrumbSchema(site, service.title, path)} />
            <header className="page-heading service-heading">
                <Link className="business-label" href="/services/">
                    ← Services / {site.shortName}
                </Link>
                <h1>{service.title}</h1>
                <p>{service.introduction}</p>
                <Link className="angled-button" href="/contact/">
                    Discuss this service →
                </Link>
            </header>
            <section className="shell service-body">
                <ContentSections sections={service.sections} />
                <aside className="scope-aside">
                    <h2>Work we can discuss</h2>
                    <ul>
                        {service.included.map((item) => (
                            <li key={item}>{item}</li>
                        ))}
                    </ul>
                    <p>
                        Scope, delivery dates and ongoing responsibilities are
                        agreed for the project.
                    </p>
                    <Link className="text-link" href="/working-together/">
                        Working together →
                    </Link>
                </aside>
            </section>
            {work.items.length ? (
                <section className="shell related-content">
                    <h2>Related work</h2>
                    <div className="collection-grid">
                        {work.items.map((item) => (
                            <WorkCard key={item.id} item={item} />
                        ))}
                    </div>
                </section>
            ) : null}
            {questions.items.length ? (
                <section className="shell related-content">
                    <h2>Questions about this service</h2>
                    <Questions items={questions.items} />
                </section>
            ) : null}
            <section className="shell related-services">
                <h2>Related services</h2>
                <nav>
                    {service.related.map((item) => (
                        <Link href={item.href} key={item.href}>
                            {item.title} <span aria-hidden="true">↗</span>
                        </Link>
                    ))}
                </nav>
            </section>
            <section className="shell enquiry-band">
                <h2>Tell me about the work you need</h2>
                <Link className="angled-button" href="/contact/">
                    Make an enquiry →
                </Link>
            </section>
        </>
    );
}

function AreaPage({site, area}: {site: PublicSite; area: AreaCopy}) {
    return (
        <>
            <JsonLd
                data={breadcrumbSchema(site, area.title, `/${area.slug}/`)}
            />
            <header className="page-heading area-heading">
                <Link href="/areas-served/" className="business-label">
                    ← Areas served
                </Link>
                <h1>{area.title}</h1>
                <p>{area.introduction}</p>
            </header>
            <section className="shell area-body">
                <ContentSections sections={area.sections} />
                <aside>
                    <h2>Relevant services</h2>
                    <nav>
                        {area.services.map((slug) => {
                            const service = site.services.find(
                                (item) => item.slug === slug,
                            );
                            return service ? (
                                <Link href={`/services/${slug}/`} key={slug}>
                                    {service.title} →
                                </Link>
                            ) : null;
                        })}
                    </nav>
                    <p>
                        Manchester is the business base. These pages describe
                        areas served, not additional offices.
                    </p>
                    <Link className="angled-button" href="/contact/">
                        Discuss your project →
                    </Link>
                </aside>
            </section>
        </>
    );
}

function InfoPage({site, page}: {site: PublicSite; page: PageCopy}) {
    return (
        <>
            <JsonLd
                data={breadcrumbSchema(site, page.title, `/${page.slug}/`)}
            />
            <header className="page-heading">
                <p className="business-label">{site.name}</p>
                <h1>{page.title}</h1>
                <p>{page.introduction}</p>
            </header>
            <section className="shell information-page">
                {page.slug === "about" ? (
                    <Image
                        src="/images/adam-birds.jpg"
                        alt="Adam Birds"
                        width={130}
                        height={158}
                        className="about-portrait"
                    />
                ) : null}
                <ContentSections sections={page.sections} />
                {page.slug === "areas-served" ? (
                    <nav className="area-directory" aria-label="Service areas">
                        {site.areas.map((area) => (
                            <Link key={area.slug} href={`/${area.slug}/`}>
                                {area.title} →
                            </Link>
                        ))}
                    </nav>
                ) : null}
                {!page.noindex ? (
                    <Link href="/contact/" className="angled-button">
                        Discuss your project →
                    </Link>
                ) : null}
            </section>
        </>
    );
}

import { websitePolicies } from "@/content/policies";
import { PolicyPage } from "./PolicyPage";
import { webPageCopy } from "@/content/page-design";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ContactForm } from "@adb/ui/public/ContactForm";
import {
    EditorialCollection,
    EditorialDetail,
    Questions,
    WorkCard,
} from "@adb/ui/public/Editorial";
import { JsonLd } from "@adb/ui/public/JsonLd";
import { breadcrumbSchema, optionalCollection } from "@adb/ui/public/server";
import type {
    AreaCopy,
    CopySection,
    PageCopy,
    ServiceCopy,
} from "@adb/ui/public/types";
import { site } from "@/content/site";

function Heading({
    title,
    introduction,
    label = site.name,
    back,
}: {
    title: string;
    introduction: string;
    label?: string;
    back?: string;
}) {
    return (
        <header className="shell web-page-heading">
            <p className="business-label">
                {back ? <Link href={back}>← {label}</Link> : label}
            </p>
            <h1>{title}</h1>
            <div className="web-heading-bottom">
                <p>{introduction}</p>
                <Link href="/contact/" className="text-link">
                    {webPageCopy.discussYourProject}
                </Link>
            </div>
        </header>
    );
}

function Copy({ sections }: { sections: CopySection[] }) {
    return (
        <div className="web-copy">
            {sections.map((section, index) => (
                <section key={section.heading} id={`section-${index + 1}`}>
                    <span className="web-section-number" aria-hidden="true">
                        {String(index + 1).padStart(2, "0")}
                    </span>
                    <div>
                        <h2>{section.heading}</h2>
                        {section.paragraphs.map((paragraph) => (
                            <p key={paragraph}>{paragraph}</p>
                        ))}
                        {section.bullets ? (
                            <ul>
                                {section.bullets.map((item) => (
                                    <li key={item}>{item}</li>
                                ))}
                            </ul>
                        ) : null}
                    </div>
                </section>
            ))}
        </div>
    );
}

function Enquiry({
    title = webPageCopy.haveAWebsiteInMind,
}: {
    title?: string;
}) {
    return (
        <section className="shell web-enquiry">
            <p className="business-label">{webPageCopy.aUsefulNextStep}</p>
            <h2>{title}</h2>
            <Link href="/contact/" className="angled-button">
                {webPageCopy.tellMeAboutIt}
                <span aria-hidden="true">↗</span>
            </Link>
        </section>
    );
}

async function Service({ service }: { service: ServiceCopy }) {
    const path = `/services/${service.slug}/`;
    const [questions, work] = await Promise.all([
        optionalCollection("faqs", site, {
            service: service.slug,
            page_size: 6,
        }),
        optionalCollection("portfolio", site, {
            service: service.slug,
            page_size: 2,
        }),
    ]);
    return (
        <>
            <JsonLd
                data={{
                    "@context": "https://schema.org",
                    "@type": "Service",
                    name: service.title,
                    description: service.description,
                    url: site.domain + path,
                    provider: { "@id": `${site.domain}/#business` },
                    serviceType: service.title,
                }}
            />
            <JsonLd data={breadcrumbSchema(site, service.title, path)} />
            <Heading
                title={service.title}
                introduction={service.introduction}
                label={webPageCopy.servicesWebDesigns}
                back="/services/"
            />
            <section className="web-scope">
                <div className="shell">
                    <header>
                        <p className="business-label">{webPageCopy.theScope}</p>
                        <h2>{webPageCopy.workWeCanDiscuss}</h2>
                        <p>{webPageCopy.serviceScopeIntroduction}</p>
                    </header>
                    <ul>
                        {service.included.map((item) => (
                            <li key={item}>{item}</li>
                        ))}
                    </ul>
                </div>
            </section>
            <section className="shell web-service-body">
                <Copy sections={service.sections} />
            </section>
            {work.items.length ? (
                <section className="shell web-related">
                    <header>
                        <p className="business-label">
                            {webPageCopy.inPractice}
                        </p>
                        <h2>{webPageCopy.relatedWork}</h2>
                    </header>
                    <div className="collection-grid">
                        {work.items.map((item) => (
                            <WorkCard key={item.id} item={item} />
                        ))}
                    </div>
                </section>
            ) : null}
            {questions.items.length ? (
                <section className="shell web-questions">
                    <header>
                        <p className="business-label">
                            {webPageCopy.beforeWeStart}
                        </p>
                        <h2>{webPageCopy.aFewUsefulAnswers}</h2>
                    </header>
                    <Questions items={questions.items} />
                </section>
            ) : null}
            <section className="shell web-related-services">
                <p className="business-label">{webPageCopy.keepExploring}</p>
                <h2>{webPageCopy.relatedServices}</h2>
                <nav>
                    {service.related.map((item) => (
                        <Link key={item.href} href={item.href}>
                            {item.title}
                            <span aria-hidden="true">↗</span>
                        </Link>
                    ))}
                </nav>
            </section>
            <Enquiry title={webPageCopy.whatNeedsBuildingFixingOrImproving} />
        </>
    );
}

function Services() {
    return (
        <>
            <Heading
                title={webPageCopy.fromBuildToUpkeep}
                label={webPageCopy.websiteServices}
                introduction={site.description}
            />
            <section className="shell web-service-directory">
                {site.services.map((service, index) => (
                    <article key={service.slug}>
                        <span
                            className="web-directory-number"
                            aria-hidden="true"
                        >
                            {String(index + 1).padStart(2, "0")}
                        </span>
                        <div>
                            <h2>
                                <Link href={`/services/${service.slug}/`}>
                                    {service.title}
                                </Link>
                            </h2>
                            <p>{service.introduction}</p>
                        </div>
                        <Link
                            className="web-directory-link"
                            href={`/services/${service.slug}/`}
                            aria-label={`Explore ${service.title}`}
                        >
                            <span aria-hidden="true">↗</span>
                        </Link>
                    </article>
                ))}
            </section>
            <Enquiry title={webPageCopy.notSureWhereYourProjectFits} />
        </>
    );
}

function Area({ area }: { area: AreaCopy }) {
    return (
        <>
            <JsonLd
                data={breadcrumbSchema(site, area.title, `/${area.slug}/`)}
            />
            <Heading
                title={area.title}
                introduction={area.introduction}
                label={webPageCopy.areasServed}
                back="/areas-served/"
            />
            <section className="shell web-area-content">
                <Copy sections={area.sections} />
                <aside>
                    <p className="business-label">{webPageCopy.theWork}</p>
                    <h2>{webPageCopy.relevantServices}</h2>
                    <nav>
                        {area.services.map((slug) => {
                            const service = site.services.find(
                                (item) => item.slug === slug,
                            );
                            return service ? (
                                <Link key={slug} href={`/services/${slug}/`}>
                                    {service.title} ↗
                                </Link>
                            ) : null;
                        })}
                    </nav>
                    <p>{webPageCopy.locationBaseNote}</p>
                </aside>
            </section>
            <Enquiry />
        </>
    );
}

function Information({ page }: { page: PageCopy }) {
    const policy = websitePolicies.find((item) => item.slug === page.slug);
    if (policy) return <PolicyPage policy={policy} />;
    const legal = Boolean(page.noindex);
    return (
        <div
            className={
                legal
                    ? "web-policy"
                    : `web-information web-information-${page.slug}`
            }
        >
            <JsonLd
                data={breadcrumbSchema(site, page.title, `/${page.slug}/`)}
            />
            {page.slug === "about" ? (
                <header className="shell web-about-heading">
                    <div>
                        <p className="business-label">
                            {webPageCopy.theBusinessBehindTheWebsite}
                        </p>
                        <h1>{page.title}</h1>
                        <p>{page.introduction}</p>
                        <Link className="angled-button" href="/contact/">
                            {webPageCopy.letsDiscussYourWebsite}
                        </Link>
                    </div>
                    <figure>
                        <Image
                            src="/images/adam-birds.jpg"
                            alt="Adam Birds, the freelance developer behind ADB Web Designs"
                            width={620}
                            height={931}
                            priority
                            sizes="(max-width: 767px) 90vw, 35vw"
                        />
                        <figcaption>
                            {webPageCopy.adamBirdsManchester}
                        </figcaption>
                    </figure>
                </header>
            ) : (
                <Heading title={page.title} introduction={page.introduction} />
            )}
            <section className="shell web-information-body">
                <Copy sections={page.sections} />
            </section>
            {page.slug === "areas-served" ? (
                <section className="shell web-area-directory">
                    <p className="business-label">{webPageCopy.localRemote}</p>
                    <nav aria-label="Service areas">
                        {site.areas.map((area) => (
                            <Link key={area.slug} href={`/${area.slug}/`}>
                                {area.title}
                                <span aria-hidden="true">↗</span>
                            </Link>
                        ))}
                    </nav>
                </section>
            ) : null}
            {!legal ? <Enquiry /> : null}
        </div>
    );
}

function Contact() {
    return (
        <>
            <header className="shell web-page-heading web-contact-heading">
                <p className="business-label">
                    {webPageCopy.startAConversation}
                </p>
                <h1>{site.contact.title}</h1>
                <p>{site.contact.introduction}</p>
            </header>
            <section className="shell web-contact">
                <aside>
                    <p className="business-label">
                        {webPageCopy.yourStartingPoint}
                    </p>
                    <h2>{webPageCopy.tellMeWhatYouHaveInMind}</h2>
                    <p>{site.contact.guidance}</p>
                    <p>{webPageCopy.tellMeAboutYourExistingSetupAndWhat}</p>
                    <Link href="/working-together/" className="text-link">
                        {webPageCopy.howTheWorkIsArranged}
                    </Link>
                </aside>
                <ContactForm services={site.services} />
            </section>
        </>
    );
}

export async function WebPages({
    path,
    search,
}: {
    path: string[];
    search: Record<string, string | string[] | undefined>;
}) {
    const key = path.join("/");
    if (path[0] === "services" && path.length === 2) {
        const service = site.services.find((item) => item.slug === path[1]);
        if (!service) notFound();
        return <Service service={service} />;
    }
    if (key === "services") return <Services />;
    if (key === "contact") return <Contact />;
    if (key === "contact/thank-you")
        return (
            <section className="shell web-thank-you">
                <p className="business-label">{webPageCopy.thankYou}</p>
                <h1>{webPageCopy.yourEnquiryHasBeenReceived}</h1>
                <p>{webPageCopy.illReviewYourMessageAndRespondToDiscuss}</p>
                <Link href="/" className="angled-button">
                    {webPageCopy.backToTheHomepage}
                </Link>
            </section>
        );
    if (path.length === 1) {
        const area = site.areas.find((item) => item.slug === key);
        if (area) return <Area area={area} />;
        const page = site.pages.find((item) => item.slug === key);
        if (page) return <Information page={page} />;
    }
    if (
        path.length === 1 &&
        (key === "blog" ||
            key === "portfolio" ||
            key === "testimonials" ||
            key === "faqs")
    )
        return (
            <div className={`web-editorial web-collection-${key}`}>
                <EditorialCollection
                    site={site}
                    resource={key}
                    search={search}
                />
            </div>
        );
    if (path.length === 2 && (path[0] === "blog" || path[0] === "portfolio"))
        return (
            <div className={`web-editorial web-detail-${path[0]}`}>
                <EditorialDetail
                    site={site}
                    resource={path[0]}
                    slug={path[1]}
                />
            </div>
        );
    if (path[0] === "blog" && path[1] === "category" && path.length === 3)
        return (
            <div className="web-editorial web-collection-blog">
                <EditorialCollection
                    site={site}
                    resource="blog"
                    category={path[2]}
                    search={search}
                />
            </div>
        );
    notFound();
}

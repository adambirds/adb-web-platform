import { homeCopy } from "@/content/home";
import Link from "next/link";
import { site } from "@/content/site";
import { homeContent } from "@adb/ui/public/server";
import { WorkCard, ArticleCard, Quote } from "@adb/ui/public/Editorial";

export async function HomePage() {
    const content = await homeContent(site);
    return (
        <>
            <section className="software-cover shell">
                <div className="software-hero-copy">
                    <p className="business-label">{homeCopy.heroLabel}</p>
                    <h1>
                        {homeCopy.softwareHeadingH11}
                        <br />
                        <em>{homeCopy.softwareHeadingSpan1}</em>
                    </h1>
                    <p className="software-introduction">
                        {homeCopy.softwareIntroP1}
                    </p>
                    <Link href="/contact/" className="angled-button">
                        {homeCopy.angledButtonLink1}
                    </Link>
                    <p className="software-location">{homeCopy.location}</p>
                </div>
                <figure className="software-product-study">
                    <figcaption>
                        <span>{homeCopy.study.label}</span>
                        <span>{homeCopy.study.type}</span>
                    </figcaption>
                    <div className="product-paper">
                        <div className="product-paper-header">
                            <span>{homeCopy.study.title}</span>
                            <span aria-hidden="true">↗</span>
                        </div>
                        <p className="product-context">
                            {homeCopy.study.introduction}
                        </p>
                        {homeCopy.study.stages.map((stage, index) => (
                            <div className="product-stage" key={stage.title}>
                                <span className="stage-marker">
                                    {String(index + 1).padStart(2, "0")}
                                </span>
                                <div>
                                    <h2>{stage.title}</h2>
                                    <p>{stage.description}</p>
                                    {stage.systems.length ? (
                                        <div className="system-tags">
                                            {stage.systems.map((system) => (
                                                <span key={system}>
                                                    {system}
                                                </span>
                                            ))}
                                        </div>
                                    ) : null}
                                </div>
                            </div>
                        ))}
                        <div className="product-paper-footer">
                            <span>{homeCopy.study.sequence}</span>
                            <span aria-hidden="true">[ ]</span>
                        </div>
                    </div>
                    <p className="product-annotation">
                        {homeCopy.study.caption}
                    </p>
                </figure>
            </section>
            <nav
                className="software-service-strip shell"
                aria-label="Software services"
            >
                <Link href="/services/web-applications/">
                    Web applications <span aria-hidden="true">↗</span>
                </Link>
                <Link href="/services/api-integrations/">
                    Integrations <span aria-hidden="true">↗</span>
                </Link>
                <Link href="/services/automation/">
                    Automation <span aria-hidden="true">↗</span>
                </Link>
                <Link href="/services/mobile-applications/">
                    Mobile apps <span aria-hidden="true">↗</span>
                </Link>
            </nav>
            <section className="shell software-review-feature">
                <div>
                    <p className="business-label">{homeCopy.businessLabelP1}</p>
                    <h2>
                        {homeCopy.shellH21}
                        <br />
                        {homeCopy.shellH22}
                    </h2>
                </div>
                <div>
                    <p>{homeCopy.shellP1}</p>
                    <Link
                        className="angled-button"
                        href="/services/ai-code-review/"
                    >
                        {homeCopy.angledButtonLink2}
                    </Link>
                </div>
            </section>
            <section className="shell home-services">
                <header>
                    <p className="business-label">{homeCopy.businessLabelP2}</p>
                    <h2>{homeCopy.shellH23}</h2>
                    <p>{homeCopy.shellP2}</p>
                </header>
                <div className="home-service-list">
                    {site.services.map((service) => (
                        <article key={service.slug}>
                            <h3>
                                <Link href={`/services/${service.slug}/`}>
                                    {service.title}
                                </Link>
                            </h3>
                            <p>{service.description}</p>
                            <Link
                                className="text-link"
                                href={`/services/${service.slug}/`}
                            >
                                {homeCopy.textLinkLink1}
                            </Link>
                        </article>
                    ))}
                </div>
            </section>
            {content.work.items.length ? (
                <section className="shell homepage-editorial">
                    <header>
                        <h2>{homeCopy.shellH24}</h2>
                        <Link className="text-link" href="/portfolio/">
                            {homeCopy.textLinkLink2}
                        </Link>
                    </header>
                    <div className="collection-grid">
                        {content.work.items.map((item) => (
                            <WorkCard key={item.id} item={item} />
                        ))}
                    </div>
                </section>
            ) : null}
            {content.testimonials.items.length ? (
                <section className="shell homepage-editorial">
                    <h2>{homeCopy.shellH25}</h2>
                    <div className="collection-grid">
                        {content.testimonials.items.map((item) => (
                            <Quote key={item.id} item={item} />
                        ))}
                    </div>
                </section>
            ) : null}
            <section className="software-about">
                <div className="shell">
                    <h2>
                        {homeCopy.softwareAboutH21}
                        <br />
                        {homeCopy.softwareAboutH22}
                        <br />
                        {homeCopy.softwareAboutH23}
                    </h2>
                    <div>
                        <p>{homeCopy.softwareAboutP1}</p>
                        <Link className="text-link" href="/about/">
                            {homeCopy.textLinkLink3}
                        </Link>
                        <Link className="text-link" href="/working-together/">
                            {homeCopy.textLinkLink4}
                        </Link>
                    </div>
                </div>
            </section>
            {content.articles.items.length ? (
                <section className="shell homepage-editorial">
                    <header>
                        <h2>{homeCopy.shellH26}</h2>
                        <Link className="text-link" href="/blog/">
                            {homeCopy.textLinkLink5}
                        </Link>
                    </header>
                    <div className="collection-grid">
                        {content.articles.items.map((item) => (
                            <ArticleCard key={item.id} item={item} />
                        ))}
                    </div>
                </section>
            ) : null}
            <section className="shell enquiry-band">
                <h2>{homeCopy.shellH27}</h2>
                <p>{homeCopy.shellP3}</p>
                <Link className="angled-button" href="/contact/">
                    {homeCopy.angledButtonLink3}
                </Link>
            </section>
        </>
    );
}

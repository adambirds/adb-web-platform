import { homeCopy } from "@/content/home";
import Link from "next/link";
import { site } from "@/content/site";
import { homeContent } from "@adb/ui/public/server";
import { WorkCard, ArticleCard, Quote } from "@adb/ui/public/Editorial";

export async function HomePage() {
    const content = await homeContent(site);
    return (
        <>
            <section className="technology-cover shell">
                <div className="technology-title-row">
                    <p className="business-label">{homeCopy.heroLabel}</p>
                    <p className="technology-coordinate">{homeCopy.location}</p>
                </div>
                <div className="technology-heading">
                    <h1>
                        {homeCopy.technologyCopyH11}
                        <br />
                        <span>{homeCopy.technologyCopyH12}</span>
                        <br />
                        {homeCopy.technologyCopyH13}
                    </h1>
                    <div>
                        <p>{homeCopy.technologyDescriptionP1}</p>
                        <Link href="/contact/" className="angled-button">
                            {homeCopy.angledButtonLink1}
                        </Link>
                    </div>
                </div>
                <div className="delivery-sheet">
                    <div className="delivery-sheet-title">
                        <span>{homeCopy.delivery.title}</span>
                        <span>{homeCopy.delivery.label}</span>
                    </div>
                    <ol className="delivery-flow">
                        {homeCopy.delivery.stages.map((stage) => (
                            <li key={stage.label}>
                                <span className="delivery-number">
                                    {stage.label}
                                </span>
                                <Link href={stage.href}>
                                    <h2>{stage.title}</h2>
                                    <p>{stage.description}</p>
                                    <span aria-hidden="true">↗</span>
                                </Link>
                            </li>
                        ))}
                    </ol>
                    <div className="delivery-sheet-footer">
                        <p>{homeCopy.delivery.note}</p>
                        <Link href="/working-together/">
                            {homeCopy.delivery.link}
                        </Link>
                    </div>
                </div>
            </section>
            <section className="shell home-services">
                <header>
                    <p className="business-label">{homeCopy.businessLabelP1}</p>
                    <h2>
                        {homeCopy.shellH21}
                        <br />
                        {homeCopy.shellH22}
                    </h2>
                    <p>{homeCopy.shellP1}</p>
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
            <section className="technology-launch">
                <div className="shell">
                    <p className="business-label">{homeCopy.businessLabelP2}</p>
                    <h2>
                        {homeCopy.technologyLaunchH21}
                        <br />
                        {homeCopy.technologyLaunchH22}
                    </h2>
                    <div>
                        <p>{homeCopy.technologyLaunchP1}</p>
                        <Link
                            href="/services/app-deployment/"
                            className="angled-button"
                        >
                            {homeCopy.angledButtonLink2}
                        </Link>
                    </div>
                </div>
            </section>
            {content.work.items.length ? (
                <section className="shell homepage-editorial">
                    <header>
                        <h2>{homeCopy.shellH23}</h2>
                        <Link href="/portfolio/" className="text-link">
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
                    <h2>{homeCopy.shellH24}</h2>
                    <div className="collection-grid">
                        {content.testimonials.items.map((item) => (
                            <Quote key={item.id} item={item} />
                        ))}
                    </div>
                </section>
            ) : null}
            <section className="shell technology-about">
                <h2>
                    {homeCopy.shellH25}
                    <br />
                    {homeCopy.shellH26}
                </h2>
                <div>
                    <p>{homeCopy.shellP2}</p>
                    <Link href="/about/" className="text-link">
                        {homeCopy.textLinkLink3}
                    </Link>
                </div>
            </section>
            {content.articles.items.length ? (
                <section className="shell homepage-editorial">
                    <header>
                        <h2>{homeCopy.shellH27}</h2>
                        <Link href="/blog/" className="text-link">
                            {homeCopy.textLinkLink4}
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
                <h2>{homeCopy.shellH28}</h2>
                <p>{homeCopy.shellP3}</p>
                <Link href="/contact/" className="angled-button">
                    {homeCopy.angledButtonLink3}
                </Link>
            </section>
        </>
    );
}

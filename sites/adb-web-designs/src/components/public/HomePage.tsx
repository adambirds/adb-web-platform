import { homeCopy } from "@/content/home";
import Link from "next/link";
import { site } from "@/content/site";
import { homeContent } from "@adb/ui/public/server";
import { ArticleCard, Quote } from "@adb/ui/public/Editorial";
import { FeaturedWork } from "./FeaturedWork";

export async function HomePage() {
    const content = await homeContent(site);
    return (
        <>
            <section className="web-cover">
                <div className="shell">
                    <div className="cover-topline">
                        <p>{site.name}</p>
                        <span>{homeCopy.coverToplineSpan1}</span>
                    </div>
                    <div className="web-heading">
                        <h1>
                            {homeCopy.webHeadingH11}
                            <br />
                            <span>{homeCopy.webHeadingSpan1}</span>
                        </h1>
                        <div>
                            <p>
                                {homeCopy.webHeadingP1}
                                <br />
                                {homeCopy.webHeadingP2}
                            </p>
                            <Link href="/contact/" className="angled-button">
                                {homeCopy.angledButtonLink1}
                            </Link>
                        </div>
                    </div>
                    <FeaturedWork items={content.work.items} />
                    <div className="web-cover-foot">
                        <p>{homeCopy.webCoverFootP1}</p>
                        <Link href="/services/">
                            {homeCopy.webCoverFootLink1}
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
                    {site.services
                        .filter((service) =>
                            [
                                "web-design",
                                "website-rescue",
                                "ecommerce",
                                "website-maintenance",
                                "search-engine-optimisation",
                            ].includes(service.slug),
                        )
                        .map((service) => (
                            <article key={service.slug}>
                                <h3>
                                    <Link href={`/services/${service.slug}/`}>
                                        {service.title}
                                    </Link>
                                </h3>
                                <p>{service.description}</p>
                                <Link
                                    href={`/services/${service.slug}/`}
                                    className="text-link"
                                >
                                    {homeCopy.textLinkLink1}
                                </Link>
                            </article>
                        ))}
                    <Link href="/services/" className="text-link">
                        {homeCopy.textLinkLink2}
                    </Link>
                </div>
            </section>
            <section className="home-about">
                <div className="shell">
                    <p className="business-label">{homeCopy.businessLabelP2}</p>
                    <h2>
                        {homeCopy.homeAboutH21}
                        <br />
                        {homeCopy.homeAboutH22}
                    </h2>
                    <div>
                        <p>{homeCopy.homeAboutP1}</p>
                        <Link href="/about/" className="text-link">
                            {homeCopy.textLinkLink3}
                        </Link>
                    </div>
                </div>
            </section>
            {content.testimonials.items.length ? (
                <section className="shell homepage-editorial">
                    <h2>{homeCopy.shellH23}</h2>
                    <div className="collection-grid">
                        {content.testimonials.items.map((item) => (
                            <Quote key={item.id} item={item} />
                        ))}
                    </div>
                    <Link href="/testimonials/" className="text-link">
                        {homeCopy.textLinkLink4}
                    </Link>
                </section>
            ) : null}
            {content.articles.items.length ? (
                <section className="shell homepage-editorial">
                    <header>
                        <h2>{homeCopy.shellH24}</h2>
                        <Link href="/blog/" className="text-link">
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
                <h2>{homeCopy.shellH25}</h2>
                <p>{homeCopy.shellP2}</p>
                <Link href="/contact/" className="angled-button">
                    {homeCopy.angledButtonLink2}
                </Link>
            </section>
        </>
    );
}

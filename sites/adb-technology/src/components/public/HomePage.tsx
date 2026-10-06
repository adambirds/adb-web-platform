import { homeCopy } from "@/content/home";
import Link from "next/link";
import { site } from "@/content/site";
import { homeContent } from "@adb/ui/public/server";
import { WorkCard, ArticleCard, Quote } from "@adb/ui/public/Editorial";

export async function HomePage() {
    const content = await homeContent(site);
    return (
        <>
            <section className="technology-cover">
                <div className="shell">
                    <div className="cover-topline">
                        <p>{site.name}</p>
                        <span>{homeCopy.coverToplineSpan1}</span>
                    </div>
                    <div className="technology-layout">
                        <div className="technology-copy">
                            <p className="technology-kicker">
                                {homeCopy.technologyKickerP1}
                            </p>
                            <h1>
                                {homeCopy.technologyCopyH11}
                                <br />
                                {homeCopy.technologyCopyH12}
                                <br />
                                {homeCopy.technologyCopyH13}
                            </h1>
                            <p className="technology-description">
                                {homeCopy.technologyDescriptionP1}
                            </p>
                            <Link href="/contact/" className="angled-button">
                                {homeCopy.angledButtonLink1}
                            </Link>
                            <p className="technology-caption">
                                {homeCopy.technologyCaptionP1}
                                <br />
                                {homeCopy.technologyCaptionP2}
                            </p>
                        </div>
                        <div
                            className="technology-map"
                            aria-label="Explore technical services"
                        >
                            <svg
                                viewBox="0 0 650 600"
                                fill="none"
                                aria-hidden="true"
                            >
                                <path
                                    className="map-trace-muted"
                                    d="M55 0V120L205 270V400L405 600M620 0L420 200V360L180 600M0 460H150L350 260H650M0 75H170L360 265V600"
                                />
                                <path
                                    className="map-trace"
                                    d="M650 55H470L290 235H0M650 550H510L200 240V0M650 345H430L305 470H0"
                                />
                                <circle cx="470" cy="55" r="12" />
                                <circle cx="200" cy="240" r="12" />
                                <circle cx="305" cy="470" r="12" />
                            </svg>
                            <Link
                                href="/services/cloud-infrastructure/"
                                className="map-label map-cloud"
                            >
                                <span>{homeCopy.mapLabelSpan1}</span>
                                <h2>
                                    {homeCopy.mapLabelH21}
                                    <br />
                                    {homeCopy.mapLabelH22}
                                </h2>
                                <span className="map-link">
                                    {homeCopy.mapLinkSpan1}
                                </span>
                            </Link>
                            <Link
                                href="/services/deployment-pipelines/"
                                className="map-label map-delivery"
                            >
                                <span>{homeCopy.mapLabelSpan2}</span>
                                <h2>
                                    {homeCopy.mapLabelH23}
                                    <br />
                                    {homeCopy.mapLabelH24}
                                </h2>
                                <span className="map-link">
                                    {homeCopy.mapLinkSpan2}
                                </span>
                            </Link>
                            <Link
                                href="/services/server-management/"
                                className="map-label map-support"
                            >
                                <span>{homeCopy.mapLabelSpan3}</span>
                                <h2>
                                    {homeCopy.mapLabelH25}
                                    <br />
                                    {homeCopy.mapLabelH26}
                                </h2>
                                <span className="map-link">
                                    {homeCopy.mapLinkSpan3}
                                </span>
                            </Link>
                            <div className="map-edge" aria-hidden="true">
                                {homeCopy.mapEdgeDiv1}
                            </div>
                        </div>
                    </div>
                    <div className="technology-cover-foot">
                        <p>{homeCopy.technologyCoverFootP1}</p>
                        <Link href="/services/">
                            {homeCopy.technologyCoverFootLink1}
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

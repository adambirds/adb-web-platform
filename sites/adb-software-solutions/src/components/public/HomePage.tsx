import { homeCopy } from "@/content/home";
import Link from "next/link";
import { site } from "@/content/site";
import { homeContent } from "@adb/ui/public/server";
import { WorkCard, ArticleCard, Quote } from "@adb/ui/public/Editorial";

export async function HomePage() {
    const content = await homeContent(site);
    return (
        <>
            <section className="software-cover">
                <div className="shell">
                    <div className="cover-topline">
                        <p>{site.name}</p>
                        <span>{homeCopy.coverToplineSpan1}</span>
                    </div>
                    <div className="software-heading">
                        <p className="software-side-label">
                            {homeCopy.softwareSideLabelP1}
                            <br />
                            {homeCopy.softwareSideLabelP2}
                        </p>
                        <h1>
                            {homeCopy.softwareHeadingH11}
                            <br />
                            <span>{homeCopy.softwareHeadingSpan1}</span>
                        </h1>
                        <div className="software-intro">
                            <p>{homeCopy.softwareIntroP1}</p>
                            <Link href="/contact/" className="angled-button">
                                {homeCopy.angledButtonLink1}
                            </Link>
                        </div>
                    </div>
                    <div
                        className="software-assembly"
                        aria-label="Explore software services"
                    >
                        <Link
                            href="/services/web-applications/"
                            className="assembly-part assembly-app"
                        >
                            <span className="assembly-caption">
                                {homeCopy.assemblyCaptionSpan1}
                            </span>
                            <h2>{homeCopy.assemblyPartH21}</h2>
                            <span
                                className="assembly-symbol"
                                aria-hidden="true"
                            >
                                [ ]
                            </span>
                            <span className="assembly-tail">
                                {homeCopy.assemblyTailSpan1}
                            </span>
                        </Link>
                        <Link
                            href="/services/api-integrations/"
                            className="assembly-part assembly-connect"
                        >
                            <span className="assembly-caption">
                                {homeCopy.assemblyCaptionSpan2}
                            </span>
                            <h2>{homeCopy.assemblyPartH22}</h2>
                            <svg
                                className="integration-art"
                                viewBox="0 0 400 130"
                                fill="none"
                                aria-hidden="true"
                            >
                                <path
                                    d="M0 25H130L180 75H250L300 25H400M0 105H130L180 55H250L300 105H400"
                                    stroke="currentColor"
                                    strokeWidth="18"
                                />
                                <circle
                                    cx="215"
                                    cy="65"
                                    r="27"
                                    fill="var(--page)"
                                    stroke="currentColor"
                                    strokeWidth="10"
                                />
                            </svg>
                            <span className="assembly-tail">
                                {homeCopy.assemblyTailSpan2}
                            </span>
                        </Link>
                        <Link
                            href="/services/automation/"
                            className="assembly-part assembly-auto"
                        >
                            <span className="assembly-caption">
                                {homeCopy.assemblyCaptionSpan3}
                            </span>
                            <h2>{homeCopy.assemblyPartH23}</h2>
                            <div className="automation-art" aria-hidden="true">
                                <i />
                                <i />
                                <i />
                                <i />
                            </div>
                            <span className="assembly-tail">
                                {homeCopy.assemblyTailSpan3}
                            </span>
                        </Link>
                    </div>
                    <div className="software-cover-foot">
                        <p>
                            {homeCopy.softwareCoverFootP1}
                            <br />
                            {homeCopy.softwareCoverFootP2}
                        </p>
                        <Link href="/working-together/">
                            {homeCopy.softwareCoverFootLink1}
                        </Link>
                    </div>
                </div>
            </section>
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

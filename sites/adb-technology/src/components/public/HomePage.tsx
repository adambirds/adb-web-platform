import { homeCopy } from "@/content/home";
import Link from "next/link";
import Image from "next/image";
import { site } from "@/content/site";
import { homeContent } from "@adb/ui/public/server";
import {
    ArticleCard,
    Quote,
    WorkCard,
    Questions,
} from "@adb/ui/public/Editorial";

export async function HomePage() {
    const content = await homeContent(site);
    return (
        <>
            <section className="web-cover shell">
                <div className="web-intro-line">
                    <p className="business-label">{homeCopy.hero.label}</p>
                    <p>{homeCopy.hero.location}</p>
                </div>
                <h1 className="web-display">
                    {homeCopy.hero.headline}
                    <span>{homeCopy.hero.headlineSecondLine}</span>
                </h1>
                <div className="web-introduction">
                    <p>
                        {homeCopy.hero.introduction} {homeCopy.hero.description}
                    </p>
                    <Link href="/contact/" className="angled-button">
                        {homeCopy.hero.contactLink}
                    </Link>
                    <a href="#services" className="web-scroll">
                        {homeCopy.services.allServicesLink}
                        <span aria-hidden="true">↓</span>
                    </a>
                </div>
            </section>
            <section className="brand-feature">
                <div className="shell">
                    <header>
                        <p className="business-label">
                            {homeCopy.feature.label}
                        </p>
                        <h2>{homeCopy.feature.heading}</h2>
                        <p>{homeCopy.feature.introduction}</p>
                        <Link
                            className="text-link"
                            href={homeCopy.feature.href}
                        >
                            {homeCopy.feature.link}
                        </Link>
                    </header>
                    <ol>
                        {homeCopy.feature.steps.map((step, index) => (
                            <li key={step.title}>
                                <span aria-hidden="true">
                                    {String(index + 1).padStart(2, "0")}
                                </span>
                                <div>
                                    <h3>{step.title}</h3>
                                    <p>{step.text}</p>
                                </div>
                            </li>
                        ))}
                    </ol>
                </div>
            </section>
            <section id="services" className="shell home-services">
                <header>
                    <p className="business-label">{homeCopy.services.label}</p>
                    <h2>
                        {homeCopy.services.heading}
                        <br />
                        {homeCopy.services.headingSecondLine}
                    </h2>
                    <p>{homeCopy.services.introduction}</p>
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
                                href={`/services/${service.slug}/`}
                                className="text-link"
                            >
                                {homeCopy.services.serviceLink}
                            </Link>
                        </article>
                    ))}
                    <Link href="/services/" className="text-link">
                        {homeCopy.services.allServicesLink}
                    </Link>
                </div>
            </section>
            <section className="shell brand-focus">
                <div>
                    <p className="business-label">{homeCopy.focus.label}</p>
                    <h2>{homeCopy.focus.heading}</h2>
                </div>
                <div>
                    <p>{homeCopy.focus.introduction}</p>
                    <Link href={homeCopy.focus.href} className="angled-button">
                        {homeCopy.focus.link}
                    </Link>
                </div>
            </section>
            <section className="home-about">
                <div className="shell">
                    <Image
                        className="home-portrait"
                        src="/images/adam-birds.jpg"
                        alt={`Adam Birds, the engineer behind ${site.name}`}
                        width={310}
                        height={465}
                    />
                    <p className="business-label">{homeCopy.about.label}</p>
                    <h2>
                        {homeCopy.about.heading}
                        <br />
                        {homeCopy.about.headingSecondLine}
                    </h2>
                    <div>
                        <p>{homeCopy.about.introduction}</p>
                        <Link href="/about/" className="text-link">
                            {homeCopy.about.link}
                        </Link>
                    </div>
                </div>
            </section>
            {content.work.items.length ? (
                <section className="shell homepage-editorial">
                    <header>
                        <h2>{homeCopy.work.heading}</h2>
                        <Link href="/portfolio/" className="text-link">
                            {homeCopy.work.link}
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
                    <header>
                        <h2>{homeCopy.testimonials.heading}</h2>
                        <Link href="/testimonials/" className="text-link">
                            {homeCopy.testimonials.link}
                        </Link>
                    </header>
                    <div className="collection-grid">
                        {content.testimonials.items.map((item) => (
                            <Quote key={item.id} item={item} />
                        ))}
                    </div>
                </section>
            ) : null}
            {content.articles.items.length ? (
                <section className="shell homepage-editorial">
                    <header>
                        <h2>{homeCopy.journal.heading}</h2>
                        <Link href="/blog/" className="text-link">
                            {homeCopy.journal.link}
                        </Link>
                    </header>
                    <div className="collection-grid">
                        {content.articles.items.map((item) => (
                            <ArticleCard key={item.id} item={item} />
                        ))}
                    </div>
                </section>
            ) : null}
            {content.faqs.items.length ? (
                <section className="shell homepage-editorial homepage-questions">
                    <header>
                        <h2>{homeCopy.faqs.heading}</h2>
                        <Link href="/faqs/" className="text-link">
                            {homeCopy.faqs.link}
                        </Link>
                    </header>
                    <Questions items={content.faqs.items} />
                </section>
            ) : null}
            <section className="shell enquiry-band">
                <h2>{homeCopy.contact.heading}</h2>
                <p>{homeCopy.contact.introduction}</p>
                <Link href="/contact/" className="angled-button">
                    {homeCopy.contact.link}
                </Link>
            </section>
        </>
    );
}

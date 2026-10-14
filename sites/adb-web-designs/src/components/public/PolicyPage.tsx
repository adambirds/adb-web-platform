import Link from "next/link";
import type { WebsitePolicy } from "@/content/policies";
import { policyDetails } from "@/content/policies";
import { site } from "@/content/site";
import { JsonLd } from "@adb/ui/public/JsonLd";
import { breadcrumbSchema } from "@adb/ui/public/server";
import { PrivacyPreferences } from "./PrivacyPreferences";

export function PolicyPage({ policy }: { policy: WebsitePolicy }) {
    const choices = policy.slug !== "terms";
    return (
        <article className="web-policy">
            <JsonLd
                data={breadcrumbSchema(site, policy.title, `/${policy.slug}/`)}
            />
            <header className="shell web-page-heading">
                <p className="business-label">ADB Web Designs</p>
                <h1>{policy.title}</h1>
                <p>{policy.introduction}</p>
                <p className="policy-date">
                    Last updated: {policyDetails.updated}
                </p>
            </header>
            <div className="shell web-information-body">
                <nav className="policy-contents" aria-label="Policy contents">
                    {policy.sections.map((section, index) => (
                        <Link
                            key={section.heading}
                            href={`#policy-section-${index + 1}`}
                        >
                            {section.heading}
                        </Link>
                    ))}
                    {choices ? (
                        <Link href="#privacy-preferences-heading">
                            Your privacy choices
                        </Link>
                    ) : null}
                </nav>
                <div className="web-copy">
                    {policy.sections.map((section, index) => (
                        <section
                            key={section.heading}
                            id={`policy-section-${index + 1}`}
                        >
                            <span
                                className="web-section-number"
                                aria-hidden="true"
                            >
                                {String(index + 1).padStart(2, "0")}
                            </span>
                            <div>
                                <h2>{section.heading}</h2>
                                {section.paragraphs.map((paragraph) => (
                                    <p key={paragraph}>{paragraph}</p>
                                ))}
                                {section.links ? (
                                    <ul className="policy-links">
                                        {section.links.map((link) => (
                                            <li key={link.href}>
                                                <Link href={link.href}>
                                                    {link.title} ↗
                                                </Link>
                                            </li>
                                        ))}
                                    </ul>
                                ) : null}
                                {policy.slug === "cookie-policy" &&
                                index === 1 ? (
                                    <div className="policy-table-wrap">
                                        <table>
                                            <caption>
                                                Public website storage inventory
                                            </caption>
                                            <thead>
                                                <tr>
                                                    <th scope="col">
                                                        Name / type
                                                    </th>
                                                    <th scope="col">Purpose</th>
                                                    <th scope="col">
                                                        Duration
                                                    </th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                <tr>
                                                    <th scope="row">
                                                        _ga and _ga_* /
                                                        first-party cookies
                                                    </th>
                                                    <td>
                                                        Google Analytics
                                                        website-usage
                                                        measurement. Disabled
                                                        through the privacy
                                                        controls.
                                                    </td>
                                                    <td>
                                                        Up to 12 months with the
                                                        website tag’s
                                                        configuration.
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <th scope="row">
                                                        adb-public-theme / local
                                                        storage
                                                    </th>
                                                    <td>
                                                        Remember a light or dark
                                                        display choice after
                                                        using the theme switch.
                                                    </td>
                                                    <td>
                                                        No automatic expiry;
                                                        until cleared or
                                                        remembering is switched
                                                        off.
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <th scope="row">
                                                        adb-public-privacy /
                                                        first-party cookie
                                                    </th>
                                                    <td>
                                                        Remember that you
                                                        switched analytics or
                                                        display-preference
                                                        storage off.
                                                    </td>
                                                    <td>
                                                        12 months after saving a
                                                        restrictive choice.
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                ) : null}
                            </div>
                        </section>
                    ))}
                </div>
                {choices ? <PrivacyPreferences /> : null}
            </div>
        </article>
    );
}

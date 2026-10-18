import type {Metadata} from "next";
import Link from "next/link";
import {LegalPage} from "../legal-page";

export const metadata: Metadata = {title: "Terms | ADB Analytics"};

export default function TermsPage() {
    return (
        <LegalPage title="Terms of use">
            <h2>Current scope</h2>
            <p>
                ADB Analytics is a private website reporting and configuration
                tool operated by ADB Software Solutions. It is currently for the
                operator's own use, with no public registration, paid plans or
                customer service commitment. Publishing these terms does not
                grant anyone access to the application or connected data.
            </p>
            <h2>Authorised use</h2>
            <p>
                Connect only Google accounts and properties you own or are
                authorised to manage. Keep account credentials and exported
                reports secure. Do not bypass permissions, access another
                workspace without authorisation, misuse provider APIs, or send
                prohibited personal or sensitive information in tracking data.
                Website tracking and any required visitor notices or consent
                remain the website operator's responsibility.
            </p>
            <h2>Google connections and configuration changes</h2>
            <p>
                Google services remain subject to their own terms, property
                permissions and quotas. Reporting consent permits reading data;
                optional administration consent permits supported configuration
                changes after confirmation. Check the selected property and
                intended effect before creating or removing definitions or key
                events. Such changes affect Google configuration and may affect
                future reporting; they do not rewrite historical data.
            </p>
            <h2>Reports and availability</h2>
            <p>
                Reports depend on Google's processing, privacy thresholds,
                aggregation, timezone rules and API availability. Results may be
                delayed, incomplete or unavailable. GA4 and Search Console
                measure different activity and should not be treated as
                interchangeable. Insights are indicators for investigation, not
                guarantees of traffic, rankings or commercial outcomes.
            </p>
            <p>
                This personal-use tool may change or be unavailable without a
                service-level commitment. Review important decisions against the
                source properties and retain any exports you need. Nothing in
                these terms removes rights or responsibilities that cannot be
                excluded under applicable law.
            </p>
            <h2>Privacy, ending access and contact</h2>
            <p>
                The <Link href="/privacy">privacy notice</Link> explains data
                use, retention, exports and deletion. Disconnect Google or
                revoke access in your Google account to stop further authorised
                API access; remove synced reports separately. Contact the
                operator through the{" "}
                <a href="https://www.adbsoftwaresolutions.co.uk/contact/">
                    ADB Software Solutions contact page
                </a>{" "}
                with questions. These terms and the operating arrangements must
                be reviewed before inviting other users or offering the service
                commercially.
            </p>
        </LegalPage>
    );
}

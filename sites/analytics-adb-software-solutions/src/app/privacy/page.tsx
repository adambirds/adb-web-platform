import type {Metadata} from "next";
import Link from "next/link";
import {LegalPage} from "../legal-page";

export const metadata: Metadata = {title: "Privacy | ADB Analytics"};

export default function PrivacyPage() {
    return (
        <LegalPage title="Privacy notice">
            <h2>Who operates this application</h2>
            <p>
                ADB Software Solutions operates ADB Analytics as a private tool
                currently used only by its operator to review websites they own
                or are authorised to manage. It is not currently offered for
                public registration or as a customer subscription service. These
                policy pages are public so they can be read before a Google
                connection is authorised.
            </p>
            <h2>Information accessed and stored</h2>
            <p>
                The shared ADB account system handles account identity,
                authentication and security sessions. Analytics stores workspace
                and website details, preferences, connection status, and
                synchronisation and audit records. Connecting Google provides
                the selected Google account identifier and email address,
                granted permissions, and access and refresh tokens.
            </p>
            <p>
                With permission, the application retrieves GA4 and Search
                Console property metadata and aggregate reports: traffic,
                engagement, events, key events, pages and URLs, search queries,
                acquisition, device, browser and country statistics. URLs,
                queries or event values can contain personal information if the
                source website sends it. Do not send sensitive or personally
                identifying information in tracking parameters.
            </p>
            <h2>How information is used</h2>
            <p>
                Information is used to display reports, compare performance,
                identify website improvements, export selected reports, and
                maintain the connection and background synchronisation. Separate
                administration consent allows explicitly requested changes to
                GA4 custom definitions and key events. Google access does not
                replace ADB sign-in or grant access to unrelated workspaces.
            </p>
            <p>
                Google API data is used only to provide these features. It is
                not sold, used for advertising or credit decisions, or used to
                train general-purpose AI models. Use and transfer of information
                received from Google APIs adheres to the{" "}
                <a href="https://developers.google.com/terms/api-services-user-data-policy">
                    Google API Services User Data Policy
                </a>
                , including its Limited Use requirements.
            </p>
            <h2>Access, storage and essential cookies</h2>
            <p>
                Reports and operational records are stored in the shared ADB
                backend, with cached results used to serve reports efficiently.
                Google tokens are encrypted using the platform credential
                service. Access is restricted by account permissions and
                workspace membership. The operator and authorised infrastructure
                providers may process information to operate, secure and support
                the service; Google processes API and consent requests. Data may
                also be disclosed where required by law.
            </p>
            <p>
                Essential session and security cookies support ADB login and
                protection against forged requests. These public policy pages do
                not load advertising or Google Analytics tracking scripts.
                Tracking installed on a connected website is separate and is
                governed by that website's own privacy and consent arrangements.
            </p>
            <h2>Retention, disconnection and deletion</h2>
            <p>
                Synced reports are retained until removed by the operator or the
                associated property is unlinked. In Integrations, unlinking a
                property removes its stored reports and configuration records.
                Disconnecting a Google connection revokes its token and clears
                stored token secrets after successful revocation; it does not
                automatically delete previously synced reports. You can also
                remove access through{" "}
                <a href="https://myaccount.google.com/connections">
                    your Google account connections
                </a>
                .
            </p>
            <p>
                Request remaining account, connection metadata or report
                deletion through the contact below. Security/audit records and
                backup copies may remain where needed for security, recovery or
                legal obligations; this service does not promise an automatic
                deletion deadline. Exported files remain under the control of
                whoever downloaded them. Removing local data does not delete
                data held in GA4 or Search Console.
            </p>
            <h2>Questions and changes</h2>
            <p>
                Contact the operator through the{" "}
                <a href="https://www.adbsoftwaresolutions.co.uk/contact/">
                    ADB Software Solutions contact page
                </a>{" "}
                for privacy questions or access, correction and deletion
                requests. This notice will be reviewed before access is expanded
                beyond the current operator. See also the{" "}
                <Link href="/terms">terms of use</Link>.
            </p>
        </LegalPage>
    );
}

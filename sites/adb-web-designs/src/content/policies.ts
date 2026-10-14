import type { CopySection, PageCopy, RelatedLink } from "@adb/ui/public/types";

/** Public business facts. Complete the unconfirmed items before launch. */
export const policyDetails = {
    updated: "6 October 2026",
    operator: "Adam Birds, trading as ADB Web Designs",
    correspondenceAddress: null as string | null,
    privacyEmail: null as string | null,
    unsuccessfulEnquiryRetention:
        "unsuccessful enquiries are reviewed for deletion after 36 months without meaningful activity or correspondence. Deletion currently requires a manual review and approval. A record may be kept for longer where there is a documented reason, with a further review date. Active enquiries and client records are handled separately",
    processingLocations:
        "The website and enquiry platform are hosted on DigitalOcean infrastructure in London, United Kingdom. Google Analytics processes website-usage information through Google’s service, which may involve processing outside the UK. Business email is handled separately through Microsoft 365.",
    transferSafeguards: null as string | null,
};

export interface PolicySection extends CopySection {
    links?: RelatedLink[];
}
export interface WebsitePolicy extends PageCopy {
    sections: PolicySection[];
}
const contactLinks = [
    { title: "Contact ADB Web Designs", href: "/contact/" },
    ...(policyDetails.privacyEmail
        ? [
              {
                  title: policyDetails.privacyEmail,
                  href: `mailto:${policyDetails.privacyEmail}`,
              },
          ]
        : []),
];
const identity = [
    `${policyDetails.operator} is based in Manchester, United Kingdom. This policy covers adbwebdesigns.co.uk and enquiries made through this website.`,
    ...(policyDetails.correspondenceAddress
        ? [`Correspondence address: ${policyDetails.correspondenceAddress}.`]
        : []),
];

export const websitePolicies: WebsitePolicy[] = [
    {
        slug: "privacy-policy",
        title: "Privacy policy",
        description:
            "How ADB Web Designs handles website enquiries and personal information, including why it is used, sharing, retention and your rights.",
        introduction:
            "This policy explains what happens to your personal information when you browse this website, send an enquiry or contact me about a project.",
        noindex: true,
        sections: [
            {
                heading: "Who is responsible and how to get in touch",
                paragraphs: [
                    ...identity,
                    "For privacy questions or to exercise your data protection rights, use the contact form and mention privacy in your message. You can use the same route to raise a complaint about how your information has been handled.",
                ],
                links: contactLinks,
            },
            {
                heading: "The information collected",
                paragraphs: [
                    "If you use the enquiry form, I receive your name, email address, business or project name if supplied, selected service, message and the website page from which you submitted it. Follow-up conversations may include further contact information and details of the work you want to discuss.",
                    "The website and its infrastructure also process technical information such as your IP address, request time, requested page and browser information to deliver pages, investigate errors and protect the service. Your IP address is used to limit repeated form submissions.",
                    "Providing an enquiry is optional. A name, email address and message are needed to respond through the form; the business name and service selection are optional. Please do not include passwords, payment-card information or sensitive personal information in your message.",
                ],
            },
            {
                heading: "Why the information is used",
                paragraphs: [
                    "I use enquiries to answer your questions, discuss a potential project, prepare proposals and keep track of the conversation. If you become a client, relevant correspondence becomes part of the project and customer records.",
                    "Technical information is used to operate and secure the website, troubleshoot faults and prevent spam and misuse. Google Analytics is also used to understand visits, pages viewed, engagement and broad device and referral information so I can improve the website. It is not used for advertising profiles.",
                    "Sending an enquiry does not subscribe you to a mailing list. I do not sell enquiry information or use the contact form to enrol you in unrelated marketing.",
                ],
            },
            {
                heading: "The lawful bases for processing",
                paragraphs: [
                    "When you enquire about services for yourself, processing needed to respond and prepare for a possible agreement is based on taking steps at your request before entering into a contract. Information needed to deliver an agreed service is processed to perform that contract.",
                    "When you contact me on behalf of a business or another person, I rely on legitimate interests in communicating with business contacts, assessing enquiries and managing customer relationships. Legitimate interests also support proportionate website security, spam prevention and the handling of complaints. These uses must be balanced against your rights and reasonable expectations.",
                    "I also rely on legitimate interests in using aggregate website-usage statistics to improve this website. You can object using the privacy controls on this page. Some records may need to be kept to comply with legal obligations, such as applicable tax or accounting requirements. If a separate use requires consent, I will explain that use and ask first; you can withdraw that consent without affecting processing that was lawful before withdrawal.",
                ],
            },
            {
                heading: "Where an enquiry goes and who can access it",
                paragraphs: [
                    "Enquiries are stored in the shared ADB business system, identified as enquiries for ADB Web Designs. The information may also be recorded as a support or sales conversation so replies and related work stay together. The shared system also supports ADB Software Solutions and ADB Technology.",
                    "Access is limited to people authorised to handle the enquiry or operate the business systems. Service providers used for hosting, data storage, backups and business email may process information to deliver those services. Professional advisers may receive relevant information where needed, and information may be disclosed when required by law.",
                    "Using a shared system does not mean your information is published on the other ADB websites. Portfolio entries and testimonials are separate public content; submitting an enquiry does not authorise publication of your name or message.",
                ],
            },
            {
                heading: "Storage and international processing",
                paragraphs: [
                    "Working with overseas clients does not by itself mean their enquiry data is transferred to their country. Website-usage information sent to Google Analytics is separate from the content of enquiry forms. Names, email addresses, messages and notes are not deliberately sent to Analytics.",
                    ...(policyDetails.processingLocations
                        ? [policyDetails.processingLocations]
                        : []),
                    ...(policyDetails.transferSafeguards
                        ? [policyDetails.transferSafeguards]
                        : []),
                    "You can contact me for information about the service providers and processing locations relevant to your enquiry.",
                ],
                links: contactLinks,
            },
            {
                heading: "How long information is kept",
                paragraphs: [
                    ...(policyDetails.unsuccessfulEnquiryRetention
                        ? [
                              `Enquiries that do not become client projects: ${policyDetails.unsuccessfulEnquiryRetention}.`,
                          ]
                        : [
                              "An enquiry is kept while the conversation is active and for a period afterwards where needed to follow up, understand previous correspondence or resolve a complaint. The period depends on whether the enquiry is ongoing, has led to a project or is connected to a dispute.",
                          ]),
                    "If you become a client, relevant project and business records may be retained for longer to deliver the service, meet legal record-keeping obligations or establish, exercise or defend legal claims. Technical security records and backups follow the retention arrangements of the systems that hold them.",
                    "Information should be deleted or anonymised when it is no longer needed. A justified legal hold may require particular records to be kept longer. You can ask about the retention of your enquiry or request erasure, subject to the rights and exceptions described below.",
                ],
            },
            {
                heading: "Your data protection rights",
                paragraphs: [
                    "Depending on the circumstances, you can request access to your personal information, correction of inaccurate information, erasure, restriction of processing or a portable copy. You can object to processing based on legitimate interests. These rights are subject to the conditions and exceptions in data protection law.",
                    "Contact me to make a request. I may need enough information to confirm your identity and locate the records. Requests are normally answered within one month; where a lawful extension applies, I will explain the reason. Making a request is normally free.",
                    "Enquiries are reviewed by a person. This website does not use your enquiry to make solely automated decisions with legal or similarly significant effects.",
                ],
                links: contactLinks,
            },
            {
                heading: "Complaints",
                paragraphs: [
                    "You can raise a privacy concern with me using the contact details above. You also have the right to complain to the Information Commissioner’s Office, the UK supervisory authority. You do not have to contact me first to exercise that right.",
                ],
                links: [
                    {
                        title: "Make a data protection complaint to the ICO",
                        href: "https://ico.org.uk/make-a-complaint/",
                    },
                ],
            },
            {
                heading: "Browser storage, other websites and updates",
                paragraphs: [
                    "The cookie policy explains Google Analytics and the display preference stored by this website. The privacy controls on this page let you switch off analytics and stop remembering your theme. Links to other websites take you to services with their own privacy and storage arrangements.",
                    "This policy may be updated when the website or its use of information changes. The date shown above identifies the latest version. If a material change affects information you have already supplied, additional notice will be provided where required.",
                ],
                links: [
                    {
                        title: "Read the cookie policy",
                        href: "/cookie-policy/",
                    },
                ],
            },
        ],
    },
    {
        slug: "cookie-policy",
        title: "Cookie policy",
        description:
            "The cookies and browser storage used by ADB Web Designs, their purpose and duration, and how to manage the theme preference.",
        introduction:
            "This website uses Google Analytics for website-usage statistics and remembers your display preference. You can switch analytics off or stop the website remembering your theme.",
        noindex: true,
        sections: [
            {
                heading: "Cookies and similar technologies",
                paragraphs: [
                    "Cookies are small pieces of information stored by your browser and sent with requests to the website that set them. Local storage is another way to remember information on your device; unlike a cookie, its contents are not automatically sent with each request. Both are covered here.",
                ],
            },
            {
                heading: "What this website stores",
                paragraphs: [
                    "The storage inventory below describes the public website. Google Analytics is active by default for aggregate website-usage statistics. The theme preference is saved only after you use the light/dark switch. It contains a display choice, not your name, email address or enquiry.",
                    "Analytics is used to understand how this website is used and improve it, rather than for advertising, remarketing or cross-site audience profiling. You can object using the controls below without paying or installing an extension. Your display preference is used solely to change the website’s appearance.",
                ],
            },
            {
                heading: "Manage analytics and display preferences",
                paragraphs: [
                    "Use the controls below to switch off Google Analytics or choose whether this website remembers your display preference. Disabling analytics stops further Analytics page-view collection on this browser and removes its accessible first-party cookies. Switching off remembering removes the saved theme and stops the theme switch from saving a new one.",
                    "You can also remove website data in your browser settings or block storage through your browser. Clearing all website data removes both the theme choice and the choice not to remember it, so you may need to switch remembering off again. Blocking storage does not stop you browsing the public pages or sending an enquiry.",
                ],
            },
            {
                heading: "Analytics, advertising and third-party services",
                paragraphs: [
                    "Google Analytics is used for website-usage statistics. Advertising storage and personalisation are disabled in the website tag. I do not use it for remarketing, advertising audiences or cross-site advertising profiles. Fonts are served by the website rather than loaded from an external font service; no social media tracking pixels or embedded social feeds are added.",
                    "Following a link to GitHub, a related ADB website or another external service takes you to that service, which may use its own cookies. The separate account and operations applications use authentication storage for signed-in services; those functions are not part of browsing these public pages.",
                    "If the purpose or configuration changes, this policy and the website’s storage controls will be updated. Any additional storage that requires consent will be kept off until the appropriate permission has been given.",
                ],
            },
            {
                heading: "Questions and changes",
                paragraphs: [
                    "Contact me if you have questions about the storage used by this website. For information about enquiries, technical request data and your data protection rights, read the privacy policy. The date above shows when this policy was last updated.",
                ],
                links: [
                    ...contactLinks,
                    {
                        title: "Read the privacy policy",
                        href: "/privacy-policy/",
                    },
                ],
            },
        ],
    },
    {
        slug: "terms",
        title: "Website terms",
        description:
            "Terms for using the ADB Web Designs website, including enquiries, intellectual property, acceptable use and links to other services.",
        introduction:
            "These terms apply to using this website. A proposal or agreement for website design, hosting, maintenance or other paid work will set out the terms of that service separately.",
        noindex: true,
        sections: [
            {
                heading: "About this website",
                paragraphs: [
                    ...identity,
                    "You may use this website to learn about the services, read published content and send genuine enquiries. If you have a question about these terms, please get in touch.",
                ],
                links: contactLinks,
            },
            {
                heading: "Enquiries and service agreements",
                paragraphs: [
                    "Sending an enquiry does not place an order, reserve availability or create an agreement for paid work. I will discuss your requirements and, where appropriate, provide a proposal covering the work, price and timing.",
                    "A project or ongoing service is governed by its own agreed terms. Those terms take precedence for that service. General descriptions on this website do not replace a proposal or change an existing agreement.",
                ],
            },
            {
                heading: "Using website content",
                paragraphs: [
                    "Website text, branding, designs, code and images are owned by or licensed to the relevant rights holder. Client names, trademarks and portfolio materials may belong to their respective owners.",
                    "You may view the pages and save or print extracts for your own reference when considering the services. Keep copyright notices and attribution with those extracts. Please ask before republishing substantial content, using the branding or reusing artwork commercially. Nothing here limits uses permitted by applicable copyright law.",
                    "Illustrative concepts and sample content marked as demos are fictional. They should not be treated as real client projects, testimonials or evidence of results.",
                ],
            },
            {
                heading: "Acceptable use",
                paragraphs: [
                    "Use the website lawfully and without interfering with other visitors or the service. Do not attempt unauthorised access, introduce malicious software, disrupt the website or use forms for spam, harassment, impersonation or unlawful content.",
                    "When submitting a form, provide contact details you are entitled to use and information you are entitled to share. Keep passwords, access tokens and other secrets out of the enquiry form. Automated misuse and excessive requests may be restricted to protect the service.",
                ],
            },
            {
                heading: "Accuracy and availability",
                paragraphs: [
                    "I aim to keep the website accurate and working, but pages may be updated and the service may occasionally be interrupted by maintenance or technical faults. If a description is unclear or you need to confirm availability, please ask before relying on it for a business decision.",
                    "Blog articles and general website information are provided for information, not as advice tailored to your particular website or business. Any recommendation for your project will depend on reviewing its requirements.",
                ],
            },
            {
                heading: "Links to other websites",
                paragraphs: [
                    "Links may lead to related ADB businesses or external websites. Each website has its own content, terms and privacy arrangements. An external link does not transfer responsibility for that service to ADB Web Designs or give permission to reuse its content.",
                ],
            },
            {
                heading: "Responsibility and your legal rights",
                paragraphs: [
                    "Nothing in these terms excludes or limits liability for death or personal injury caused by negligence, fraud or fraudulent misrepresentation, or any liability that cannot lawfully be excluded or limited. Your statutory rights remain unaffected.",
                    "These terms do not add a blanket exclusion of responsibility for paid services. The responsibilities and remedies for a project or ongoing service are covered by the relevant service agreement and applicable law.",
                ],
            },
            {
                heading: "Privacy, cookies and changes to these terms",
                paragraphs: [
                    "The privacy policy explains how personal information is handled; the cookie policy explains browser storage and display preferences.",
                    "These website terms may be updated. The version displayed when you use the website applies to that use. Updating this page does not change an existing service agreement.",
                ],
                links: [
                    { title: "Privacy policy", href: "/privacy-policy/" },
                    { title: "Cookie policy", href: "/cookie-policy/" },
                ],
            },
            {
                heading: "Governing law and resolving questions",
                paragraphs: [
                    "These website terms are governed by the law of England and Wales. The courts of England and Wales have jurisdiction, subject to any mandatory rights or protections that allow you to bring proceedings elsewhere. This does not remove any mandatory consumer rights that apply to you.",
                    "If you have a concern about the website, please contact me so I can look into it.",
                ],
                links: contactLinks,
            },
        ],
    },
];

import { createWebsitePolicies } from "@adb/ui/public/policies";
export type { WebsitePolicy } from "@adb/ui/public/policies";
export const policyDetails = {
    updated: "14 October 2026",
    operator: "Adam Birds, trading as ADB Software Solutions",
    correspondenceAddress: null as string | null,
    privacyEmail: null as string | null,
    unsuccessfulEnquiryRetention:
        "unsuccessful enquiries are reviewed for deletion after 36 months without meaningful activity or correspondence. Deletion currently requires a manual review and approval. A record may be kept for longer where there is a documented reason, with a further review date. Active enquiries and client records are handled separately",
    processingLocations:
        "The website and enquiry platform are hosted on DigitalOcean infrastructure in London, United Kingdom. Google Analytics processes website-usage information through Google’s service, which may involve processing outside the UK. Business email is handled separately through Microsoft 365.",
    transferSafeguards: null as string | null,
};

export const websitePolicies = createWebsitePolicies(
    {
        name: "ADB Software Solutions",
        hostname: "adbsoftwaresolutions.co.uk",
        paidWork: "software development, integration or code review",
        subject: "software",
        hasOperations: true,
    },
    policyDetails,
);

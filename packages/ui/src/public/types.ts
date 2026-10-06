import type {PublicBrand} from "@adb/api-client/public";

export interface CopySection {
    heading: string;
    paragraphs: string[];
    bullets?: string[];
}
export interface RelatedLink {
    title: string;
    href: string;
}
export interface ServiceCopy {
    slug: string;
    title: string;
    description: string;
    introduction: string;
    sections: CopySection[];
    included: string[];
    related: RelatedLink[];
}
export interface AreaCopy {
    slug: string;
    title: string;
    description: string;
    introduction: string;
    sections: CopySection[];
    services: string[];
}
export interface PageCopy {
    slug: string;
    title: string;
    description: string;
    introduction: string;
    sections: CopySection[];
    noindex?: boolean;
}
export interface PublicSite {
    brand: PublicBrand;
    name: string;
    shortName: string;
    domain: string;
    description: string;
    kind: "web" | "software" | "technology";
    services: ServiceCopy[];
    areas: AreaCopy[];
    pages: PageCopy[];
    contact: {title: string; introduction: string; guidance: string};
}

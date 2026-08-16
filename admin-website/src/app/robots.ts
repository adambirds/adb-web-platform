import type { Metadata } from "next";

export default function robots(): Metadata.Robots {
    return {
        rules: {
            userAgent: "*",
            disallow: "/",
        },
    };
}

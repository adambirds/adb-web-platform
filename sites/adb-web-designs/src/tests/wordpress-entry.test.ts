/** @jest-environment node */
import { redirectWordPressEntry } from "@/components/public/WordPressEntry";
import { legacyDestination } from "@/components/public/MarketingPage";
import wordpressURLs from "@/content/wordpress-urls.json";
import editorialAliases from "@/content/wordpress-editorial-aliases.json";

jest.mock("next/navigation", () => ({
    notFound: () => {
        throw new Error("NOT_FOUND");
    },
    permanentRedirect: (destination: string) => {
        throw new Error(`REDIRECT:${destination}`);
    },
}));
jest.mock("@/components/public/MarketingPage", () => ({
    legacyDestination: jest.fn(),
}));
afterEach(() => jest.clearAllMocks());

it("leaves ordinary homepage and campaign requests alone", async () => {
    await expect(
        redirectWordPressEntry({ utm_source: "newsletter" }),
    ).resolves.toBeUndefined();
});
it("redirects known page IDs directly to retained or consolidated pages", async () => {
    await expect(redirectWordPressEntry({ page_id: "11387" })).rejects.toThrow(
        "REDIRECT:/about/",
    );
    await expect(redirectWordPressEntry({ page_id: "11847" })).rejects.toThrow(
        "REDIRECT:/lancashire-website-design/",
    );
});
it("checks publication before redirecting editorial IDs", async () => {
    const entry = Object.entries(wordpressURLs).find(
        ([, path]) => path === "/wordpress-how-to-secure-your-website/",
    )!;
    const [key, id] = entry[0].split(":");
    jest.mocked(legacyDestination).mockRejectedValueOnce(
        new Error("NOT_FOUND"),
    );
    await expect(redirectWordPressEntry({ [key]: id })).rejects.toThrow(
        "NOT_FOUND",
    );
    expect(legacyDestination).toHaveBeenCalledWith([
        "wordpress-how-to-secure-your-website",
    ]);
    jest.mocked(legacyDestination).mockRejectedValueOnce(
        new Error("REDIRECT:/blog/wordpress-how-to-secure-your-website/"),
    );
    await expect(redirectWordPressEntry({ [key]: id })).rejects.toThrow(
        "REDIRECT:/blog/wordpress-how-to-secure-your-website/",
    );
});
it.each([
    { p: "99999999" },
    { p: "invalid" },
    { p: ["1", "2"] },
    { p: "45", page_id: "45" },
    { attachment_id: "11416" },
])(
    "returns a real not-found result for invalid or unmigrated IDs: %j",
    async (search) => {
        await expect(redirectWordPressEntry(search)).rejects.toThrow(
            "NOT_FOUND",
        );
    },
);
it("keeps unpublished article IDs at 404 until their exact replacement is published", async () => {
    const entry = Object.entries(wordpressURLs).find(
        ([, path]) => path === "/textzformatter-review/",
    )!;
    const [key, id] = entry[0].split(":");
    await expect(redirectWordPressEntry({ [key]: id })).rejects.toThrow(
        "NOT_FOUND",
    );
});

it("all exported article paths, including previously retired candidates, remain publication-gated", () => {
    const aliases: Record<string, string> = editorialAliases;
    expect(aliases["/textzformatter-review"]).toBe(
        "/blog/textzformatter-review/",
    );
    expect(
        Object.values(aliases).filter(
            (destination) =>
                destination.startsWith("/blog/") &&
                !destination.startsWith("/blog/category/"),
        ).length,
    ).toBe(14);
});

/** @jest-environment node */
import {
    getCollection,
    getBlogPost,
    PublicContentError,
    publicApiUrl,
} from "@adb/api-client/public";
import { handlePublicContact } from "@adb/ui/public/contact";
import { site } from "@/content/site";

const options = { brand: site.brand, baseUrl: "https://backend.example.test" };
afterEach(() => jest.restoreAllMocks());
it("attributes public collection requests to the site without authentication cookies", async () => {
    const fetcher = jest
        .spyOn(global, "fetch")
        .mockResolvedValue(
            Response.json({ items: [], total: 0, page: 2, page_size: 9 }),
        );
    await getCollection("portfolio", options, {
        page: 2,
        q: "security & recovery",
    });
    const [url, request] = fetcher.mock.calls[0];
    expect(new URL(String(url)).searchParams.get("brand")).toBe(
        "adb-web-designs",
    );
    expect(new URL(String(url)).searchParams.get("q")).toBe(
        "security & recovery",
    );
    expect(request?.credentials).toBe("omit");
    expect(request?.cache).toBe("no-store");
});
it("preserves CMS not-found and network errors", async () => {
    const fetcher = jest
        .spyOn(global, "fetch")
        .mockResolvedValue(new Response(null, { status: 404 }));
    await expect(getBlogPost("draft", options)).rejects.toEqual(
        new PublicContentError(404),
    );
    fetcher.mockRejectedValue(new Error("offline"));
    await expect(getBlogPost("post", options)).rejects.toEqual(
        new PublicContentError(503),
    );
});
it("encodes taxonomy filters", () => {
    expect(
        publicApiUrl("blog/posts", options, {
            category: "web & design",
        }).searchParams.get("category"),
    ).toBe("web & design");
});
function enquiry(body: unknown, origin = "https://adbwebdesigns.co.uk") {
    return new Request("https://adbwebdesigns.co.uk/api/contact", {
        method: "POST",
        headers: { origin, "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
}
it("fixes contact attribution to the actual website and drops browser-supplied privileges", async () => {
    const fetcher = jest
        .spyOn(global, "fetch")
        .mockResolvedValue(Response.json({ success: true }));
    const response = await handlePublicContact(
        enquiry({
            name: "Visitor",
            email: "visitor@example.com",
            message: "Please discuss a website.",
            brand: "adb-technology",
            assigned_to: 1,
        }),
        site,
    );
    expect(response.status).toBe(200);
    const [url, request] = fetcher.mock.calls[0];
    expect(new URL(String(url)).searchParams.get("brand")).toBe(
        "adb-web-designs",
    );
    expect(JSON.parse(String(request?.body))).not.toHaveProperty("assigned_to");
    expect(request?.credentials).toBe("omit");
});
it("rejects cross-origin and oversized submissions without calling the backend", async () => {
    const fetcher = jest.spyOn(global, "fetch");
    expect(
        (
            await handlePublicContact(
                enquiry({ name: "Visitor" }, "https://unrelated.test"),
                site,
            )
        ).status,
    ).toBe(403);
    expect(
        (
            await handlePublicContact(
                enquiry({ message: "x".repeat(40000) }),
                site,
            )
        ).status,
    ).toBe(413);
    expect(fetcher).not.toHaveBeenCalled();
});
it("keeps backend failures visible rather than acknowledging a lost enquiry", async () => {
    const fetcher = jest
        .spyOn(global, "fetch")
        .mockResolvedValue(new Response(null, { status: 503 }));
    expect(
        (await handlePublicContact(enquiry({ name: "Visitor" }), site)).status,
    ).toBe(503);
    fetcher.mockResolvedValue(Response.json({ success: false }));
    expect(
        (await handlePublicContact(enquiry({ name: "Visitor" }), site)).status,
    ).toBe(503);
});
it("shows validation and throttling responses", async () => {
    const fetcher = jest
        .spyOn(global, "fetch")
        .mockResolvedValue(new Response(null, { status: 422 }));
    expect(
        (await handlePublicContact(enquiry({ name: "Visitor" }), site)).status,
    ).toBe(400);
    fetcher.mockResolvedValue(new Response(null, { status: 429 }));
    expect(
        (await handlePublicContact(enquiry({ name: "Visitor" }), site)).status,
    ).toBe(429);
});

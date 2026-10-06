import {NextResponse} from "next/server";
import type {PublicSite} from "./types";
import {apiOptions} from "./server";

/** Fixed Brand attribution; the browser cannot choose the target business. */
export async function handlePublicContact(
    request: Request,
    site: PublicSite,
): Promise<Response> {
    const origin = request.headers.get("origin");
    if (origin && origin !== new URL(request.url).origin)
        return NextResponse.json(
            {message: "Please submit the form from this website."},
            {status: 403},
        );
    const reader = request.body?.getReader();
    if (!reader)
        return NextResponse.json(
            {message: "Please complete the enquiry form."},
            {status: 400},
        );
    const chunks: Uint8Array[] = [];
    let size = 0;
    while (true) {
        const {done, value} = await reader.read();
        if (done) break;
        size += value.length;
        if (size > 32000) {
            await reader.cancel();
            return NextResponse.json(
                {message: "Your enquiry is too long."},
                {status: 413},
            );
        }
        chunks.push(value);
    }
    const text = new TextDecoder().decode(
        Uint8Array.from(chunks.flatMap((chunk) => Array.from(chunk))),
    );
    let payload: Record<string, unknown>;
    try {
        const value: unknown = JSON.parse(text);
        if (!value || typeof value !== "object" || Array.isArray(value))
            throw new Error("Invalid payload");
        payload = value as Record<string, unknown>;
    } catch {
        return NextResponse.json(
            {message: "Please complete the enquiry form."},
            {status: 400},
        );
    }
    const url = new URL(
        `${apiOptions(site).baseUrl.replace(/\/$/, "")}/api/website/contact`,
    );
    url.searchParams.set("brand", site.brand);
    const headers: Record<string, string> = {
        "Content-Type": "application/json",
    };
    // Production ingress must overwrite forwarded IP headers, as for existing auth throttling.
    const forwarded = request.headers.get("x-forwarded-for");
    if (forwarded) headers["X-Forwarded-For"] = forwarded;
    try {
        const response = await fetch(url, {
            method: "POST",
            headers,
            body: JSON.stringify({
                name: payload.name,
                email: payload.email,
                company: payload.company,
                message: payload.message,
                website: payload.website || "",
                source_path: payload.source_path || "/contact/",
            }),
            signal: AbortSignal.timeout(15000),
            cache: "no-store",
            credentials: "omit",
        });
        if (!response.ok)
            return NextResponse.json(
                {
                    message:
                        response.status === 429
                            ? "Too many enquiries have been sent. Please try again later."
                            : response.status === 422
                              ? "Please check your name, email address and message."
                              : "Your enquiry could not be sent. Please try again.",
                },
                {
                    status:
                        response.status === 429
                            ? 429
                            : response.status === 422
                              ? 400
                              : 503,
                },
            );
        const result = (await response.json()) as {success?: boolean};
        if (!result.success)
            return NextResponse.json(
                {message: "Your enquiry could not be sent. Please try again."},
                {status: 503},
            );
        return NextResponse.json({success: true});
    } catch {
        return NextResponse.json(
            {message: "Your enquiry could not be sent. Please try again."},
            {status: 503},
        );
    }
}

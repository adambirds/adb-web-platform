/**
 * Route handlers each site re-exports from src/app/healthz/route.ts and
 * src/app/metrics/route.ts. nginx (adb-deploy) keeps both off the public
 * domains.
 */
import {NextResponse} from "next/server";

import {metrics} from "./metrics";

/**
 * GET /healthz for Docker's health check. A site has no dependency a
 * restart could fix (the API is checked by the backend's own health check),
 * so it is "ok" whenever the server can answer.
 */
export function healthz(): NextResponse {
    return NextResponse.json(
        {
            status: "ok",
            checks: {
                server: {
                    ok: true,
                    uptime_seconds: Math.round(process.uptime()),
                },
            },
        },
        {headers: {"Cache-Control": "no-store"}},
    );
}

/** GET /metrics for Prometheus. */
export async function prometheus(): Promise<Response> {
    const {registry} = metrics();
    return new Response(await registry.metrics(), {
        headers: {
            "Content-Type": registry.contentType,
            "Cache-Control": "no-store",
        },
    });
}

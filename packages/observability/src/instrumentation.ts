/** Each site's instrumentation.ts re-exports this; Next.js runs it once at start-up. */
export async function register(): Promise<void> {
    if (process.env.NEXT_RUNTIME === "nodejs") {
        const {trackHttpRequests} = await import("./metrics");
        trackHttpRequests();
    }
}

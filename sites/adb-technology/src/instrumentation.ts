// Runs once when the Next.js server starts: times every HTTP request for
// /metrics. (JSON logs are set up earlier; see the Dockerfile.)
export { register } from "@adb/observability/instrumentation";

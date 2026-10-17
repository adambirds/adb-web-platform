// GET /healthz for Docker's health check; see @adb/observability.
export const dynamic = "force-dynamic";

export { healthz as GET } from "@adb/observability/routes";

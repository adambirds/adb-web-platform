import type {NextConfig} from "next";
const config: NextConfig = {
    reactStrictMode: true,
    transpilePackages: ["@adb/ui", "@adb/api-client", "@adb/observability"],
};
export default config;

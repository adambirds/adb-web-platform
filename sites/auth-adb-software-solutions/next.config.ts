import type {NextConfig} from "next";

const nextConfig: NextConfig = {
    output: "standalone",
    reactStrictMode: true,
    transpilePackages: ["@adb/observability"],
};

export default nextConfig;

/** @type {import('next').NextConfig} */

const nextConfig = {
    reactStrictMode: true,
    trailingSlash: true,
    skipTrailingSlashRedirect: true,
    async redirects() {
        return require("./redirects.json");
    },
    transpilePackages: ["@adb/ui", "@adb/api-client", "@adb/observability"],
    images: {
        remotePatterns: [
            {
                protocol: "http",
                hostname: "localhost",
                port: "8000",
                pathname: "/media/**",
            },
        ],
    },
};

module.exports = nextConfig;

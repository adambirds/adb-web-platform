const stripTrailingSlash = (value: string): string => value.replace(/\/$/, "");

export const API_URL = stripTrailingSlash(
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
);

export const AUTH_URL = stripTrailingSlash(
    process.env.NEXT_PUBLIC_AUTH_URL || "http://localhost:5175",
);

export function getAdminLoginUrl(returnTo?: string): string {
    const target =
        returnTo ||
        (typeof window !== "undefined" ? window.location.href : undefined);

    if (!target) {
        return `${AUTH_URL}/login`;
    }

    return `${AUTH_URL}/login?next=${encodeURIComponent(target)}`;
}

export function getAccountUrl(returnTo?: string): string {
    const target =
        returnTo ||
        (typeof window !== "undefined" ? window.location.href : undefined);

    if (!target) {
        return `${AUTH_URL}/account/security`;
    }

    return `${AUTH_URL}/account/security?next=${encodeURIComponent(target)}`;
}

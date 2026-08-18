/**
 * Configuration for the shared ADB authentication service.
 */

export const API_URL =
    process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const DEFAULT_APP_URL =
    process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3001";
const ADMIN_URL = process.env.NEXT_PUBLIC_ADMIN_URL ?? "http://localhost:3000";
const WEB_DESIGNS_URL =
    process.env.NEXT_PUBLIC_WEB_DESIGNS_URL ?? "http://localhost:3002";
const TECHNOLOGY_URL =
    process.env.NEXT_PUBLIC_TECHNOLOGY_URL ?? "http://localhost:3003";
const AUTH_URL = process.env.NEXT_PUBLIC_AUTH_URL ?? "http://localhost:3004";

const ALLOWED_REDIRECT_ORIGINS = [
    DEFAULT_APP_URL,
    ADMIN_URL,
    WEB_DESIGNS_URL,
    TECHNOLOGY_URL,
    AUTH_URL,
];

/**
 * Validate that a redirect URL is safe to redirect to.
 * Only known ADB application origins and relative paths are accepted.
 */
export function isValidRedirectUrl(url: string): boolean {
    if (!url) return false;

    if (url.startsWith("/") && !url.startsWith("//")) {
        return true;
    }

    try {
        const parsed = new URL(url);
        return ALLOWED_REDIRECT_ORIGINS.some((allowed) => {
            try {
                return parsed.origin === new URL(allowed).origin;
            } catch {
                return false;
            }
        });
    } catch {
        return false;
    }
}

/**
 * Get the validated return URL from the current query string.
 */
export function getRedirectUrl(): string {
    if (typeof window === "undefined") {
        return DEFAULT_APP_URL;
    }

    const params = new URLSearchParams(window.location.search);
    const next = params.get("next");

    if (next && isValidRedirectUrl(next)) {
        return next;
    }

    return DEFAULT_APP_URL;
}

/**
 * Get the default application URL used when no return target is supplied.
 */
export function getDefaultAppUrl(): string {
    return DEFAULT_APP_URL;
}

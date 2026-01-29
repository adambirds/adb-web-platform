/**
 * Utility for generating canonical URLs for the website
 */

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

/**
 * Generate a canonical URL for the given path
 * @param path - The path relative to the base URL (should start with /)
 * @returns The full canonical URL
 */
export function getCanonicalUrl(path: string): string {
    // Ensure path starts with /
    const normalizedPath = path.startsWith("/") ? path : `/${path}`;

    // Remove trailing slash unless it's the root path
    const cleanPath =
        normalizedPath === "/" ? "/" : normalizedPath.replace(/\/$/, "");

    return `${BASE_URL}${cleanPath}`;
}

/**
 * Get the base URL for the website
 * @returns The base URL
 */
export function getBaseUrl(): string {
    return BASE_URL;
}

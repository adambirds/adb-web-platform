/** Preferences are local to each public website's browser origin. */
export interface PublicPrivacyPreferences {
    rememberTheme: boolean;
    analytics: boolean;
}
export const PRIVACY_COOKIE = "adb-public-privacy";
export const PRIVACY_EVENT = "adb-public-privacy-change";
let sessionPreferences: PublicPrivacyPreferences | undefined;

export function readPrivacyPreferences(): PublicPrivacyPreferences {
    if (sessionPreferences) return sessionPreferences;
    const defaults = {rememberTheme: true, analytics: true};
    if (typeof document === "undefined") return defaults;
    const stored = document.cookie
        .split(";")
        .map((part) => part.trim())
        .find((part) => part.startsWith(`${PRIVACY_COOKIE}=`))
        ?.split("=")[1];
    if (!stored || !/^t[01]a[01]$/.test(stored)) return defaults;
    return {rememberTheme: stored[1] === "1", analytics: stored[3] === "1"};
}

export function savePrivacyPreferences(
    preferences: PublicPrivacyPreferences,
): void {
    sessionPreferences = preferences;
    const secure = location.protocol === "https:" ? "; Secure" : "";
    const value = `t${Number(preferences.rememberTheme)}a${Number(preferences.analytics)}`;
    const duration =
        preferences.rememberTheme && preferences.analytics ? 0 : 31536000;
    document.cookie = `${PRIVACY_COOKIE}=${value}; Path=/; Max-Age=${duration}; SameSite=Lax${secure}`;
    if (!preferences.rememberTheme) {
        try {
            localStorage.removeItem("adb-public-theme");
        } catch {
            /* Storage may be blocked. */
        }
    }
    window.dispatchEvent(new Event(PRIVACY_EVENT));
}

export function clearAnalyticsCookies(): void {
    const names = document.cookie
        .split(";")
        .map((part) => part.trim().split("=")[0])
        .filter((name) => name === "_ga" || name.startsWith("_ga_"));
    const domains = [
        "",
        location.hostname,
        ...location.hostname
            .split(".")
            .map((_, index, parts) => `.${parts.slice(index).join(".")}`),
    ];
    for (const name of names)
        for (const domain of domains) {
            document.cookie = `${name}=; Path=/; Max-Age=0; SameSite=Lax${domain ? `; Domain=${domain}` : ""}`;
        }
}

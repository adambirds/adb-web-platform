"use client";
import {useEffect} from "react";
import {usePathname} from "next/navigation";
import {
    clearAnalyticsCookies,
    PRIVACY_EVENT,
    readPrivacyPreferences,
} from "./privacy";

type AnalyticsWindow = Window & {
    dataLayer?: unknown[];
    gtag?: (...arguments_: unknown[]) => void;
};

export function Analytics({measurementId}: {measurementId: string}) {
    const pathname = usePathname();
    useEffect(() => {
        if (!/^G-[A-Z0-9]+$/.test(measurementId)) return;
        const browser = window as AnalyticsWindow;
        const flags = window as unknown as Record<string, unknown>;
        let script: HTMLScriptElement | undefined;
        function update() {
            const enabled = readPrivacyPreferences().analytics;
            flags[`ga-disable-${measurementId}`] = !enabled;
            if (!enabled) {
                clearAnalyticsCookies();
                return;
            }
            if (document.getElementById("adb-ga4")) return;
            browser.dataLayer ||= [];
            browser.gtag = (...arguments_: unknown[]) =>
                browser.dataLayer?.push(arguments_);
            browser.gtag("consent", "default", {
                analytics_storage: "granted",
                ad_storage: "denied",
                ad_user_data: "denied",
                ad_personalization: "denied",
            });
            browser.gtag("js", new Date());
            browser.gtag("config", measurementId, {
                send_page_view: false,
                page_location: `${location.origin}${location.pathname}`,
                page_referrer: document.referrer
                    ? new URL(document.referrer).origin
                    : "",
                allow_google_signals: false,
                allow_ad_personalization_signals: false,
                cookie_expires: 31536000,
                cookie_update: false,
            });
            script = document.createElement("script");
            script.id = "adb-ga4";
            script.async = true;
            script.src = `https://www.googletagmanager.com/gtag/js?id=${measurementId}`;
            document.head.append(script);
        }
        update();
        window.addEventListener(PRIVACY_EVENT, update);
        return () => {
            window.removeEventListener(PRIVACY_EVENT, update);
            // The disable flag governs an already loaded library, including after opting out.
            script?.remove();
        };
    }, [measurementId]);
    useEffect(() => {
        if (!/^G-[A-Z0-9]+$/.test(measurementId)) return;
        function pageView() {
            if (!readPrivacyPreferences().analytics) return;
            const browser = window as AnalyticsWindow;
            browser.gtag?.("event", "page_view", {
                send_to: measurementId,
                page_location: `${location.origin}${pathname}`,
                page_title: document.title,
                page_referrer: document.referrer
                    ? new URL(document.referrer).origin
                    : "",
            });
        }
        pageView();
        window.addEventListener(PRIVACY_EVENT, pageView);
        return () => window.removeEventListener(PRIVACY_EVENT, pageView);
    }, [measurementId, pathname]);
    return null;
}

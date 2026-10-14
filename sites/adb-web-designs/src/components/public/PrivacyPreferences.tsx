"use client";
import { useEffect, useState } from "react";
import {
    PRIVACY_EVENT,
    readPrivacyPreferences,
    savePrivacyPreferences,
} from "@adb/ui/public/privacy";

export function PrivacyPreferences() {
    const [preferences, setPreferences] = useState({
        rememberTheme: true,
        analytics: true,
    });
    const [saved, setSaved] = useState(false);
    useEffect(() => {
        const update = () => setPreferences(readPrivacyPreferences());
        update();
        window.addEventListener(PRIVACY_EVENT, update);
        return () => window.removeEventListener(PRIVACY_EVENT, update);
    }, []);
    return (
        <section
            className="privacy-preferences"
            aria-labelledby="privacy-preferences-heading"
        >
            <h2 id="privacy-preferences-heading">Your privacy choices</h2>
            <p>
                These choices apply to this website on this browser. You can
                change them at any time.
            </p>
            <label>
                <input
                    type="checkbox"
                    checked={preferences.analytics}
                    onChange={(event) => {
                        setSaved(false);
                        setPreferences({
                            ...preferences,
                            analytics: event.target.checked,
                        });
                    }}
                />{" "}
                Allow Google Analytics for website-usage statistics
            </label>
            <label>
                <input
                    type="checkbox"
                    checked={preferences.rememberTheme}
                    onChange={(event) => {
                        setSaved(false);
                        setPreferences({
                            ...preferences,
                            rememberTheme: event.target.checked,
                        });
                    }}
                />{" "}
                Remember my light or dark display preference
            </label>
            <button
                type="button"
                className="angled-button"
                onClick={() => {
                    savePrivacyPreferences(preferences);
                    setSaved(true);
                }}
            >
                Save privacy choices
            </button>
            <p role="status">
                {saved ? "Your privacy choices have been saved." : ""}
            </p>
        </section>
    );
}

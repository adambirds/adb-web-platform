"use client";
import {useEffect, useState} from "react";
import {readPrivacyPreferences} from "./privacy";

export function ThemeToggle() {
    const [theme, setTheme] = useState("dark");
    useEffect(() => {
        const shell = document.querySelector<HTMLElement>(".marketing");
        try {
            const saved = readPrivacyPreferences().rememberTheme
                ? localStorage.getItem("adb-public-theme")
                : null;
            if (saved === "light") {
                setTheme(saved);
                if (shell) shell.dataset.theme = saved;
            }
        } catch {
            /* A preference does not require storage. */
        }
    }, []);
    function toggle() {
        const next = theme === "dark" ? "light" : "dark";
        setTheme(next);
        const shell = document.querySelector<HTMLElement>(".marketing");
        if (shell) shell.dataset.theme = next;
        try {
            if (readPrivacyPreferences().rememberTheme)
                localStorage.setItem("adb-public-theme", next);
        } catch {
            /* Optional preference. */
        }
    }
    return (
        <button
            className="theme-toggle"
            type="button"
            onClick={toggle}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
        >
            <span aria-hidden="true">{theme === "dark" ? "☼" : "☾"}</span>
        </button>
    );
}

"use client";

import {ThemeContext} from "@/contexts/ThemeContext";
import {ReactNode, useEffect, useState} from "react";

const ThemeProvider = ({children}: {children: ReactNode}) => {
    const [theme, setTheme] = useState("light");

    useEffect(() => {
        const localTheme = localStorage.getItem("theme");
        const preferredTheme = window.matchMedia(
            "(prefers-color-scheme: dark)",
        ).matches
            ? "dark"
            : "light";

        setTheme(localTheme || preferredTheme);
    }, []);

    useEffect(() => {
        document.documentElement.classList.remove("light", "dark");
        document.documentElement.classList.add(theme);
    }, [theme]);

    const toggleTheme = () => {
        const newTheme = theme === "light" ? "dark" : "light";
        setTheme(newTheme);
        localStorage.setItem("theme", newTheme);
    };

    return (
        <ThemeContext.Provider value={{theme, toggleTheme}}>
            {children}
        </ThemeContext.Provider>
    );
};

export default ThemeProvider;

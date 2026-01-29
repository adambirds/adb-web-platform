import {ThemeContext} from "@/contexts/ThemeContext";
import {ReactNode, useEffect, useState} from "react";

const ThemeProvider = ({children}: {children: ReactNode}) => {
    // Use a function to initialize the theme state to ensure it's set immediately
    const [theme, setTheme] = useState<string>(() => {
        const localTheme = localStorage.getItem("theme");
        return (
            localTheme ||
            (window.matchMedia("(prefers-color-scheme: dark)").matches
                ? "dark"
                : "light")
        );
    });

    const toggleTheme = () => {
        const newTheme = theme === "light" ? "dark" : "light";
        setTheme(newTheme);
        localStorage.setItem("theme", newTheme);
    };

    useEffect(() => {
        // Apply the theme as a class to the body or root element of your application but don't override any existing classes
        document.documentElement.classList.remove("light", "dark");
        document.documentElement.classList.add(theme);
    }, [theme]);

    return (
        <ThemeContext.Provider value={{theme, toggleTheme}}>
            {children}
        </ThemeContext.Provider>
    );
};

export default ThemeProvider;

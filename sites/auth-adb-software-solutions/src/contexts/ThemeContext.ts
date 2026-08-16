import {ThemeContextType, defaultContextValue} from "@/types/themeTypes";
import {createContext} from "react";

export const ThemeContext =
    createContext<ThemeContextType>(defaultContextValue);

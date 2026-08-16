export interface ThemeContextType {
    theme: string;
    toggleTheme: () => void;
}

export const defaultContextValue: ThemeContextType = {
    theme: "dark",
    toggleTheme: () => {},
};

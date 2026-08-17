"use client";

import {AuthProvider} from "@/contexts/AuthContext";
import ThemeProvider from "@/providers/ThemeProvider";

export default function Providers({children}: {children: React.ReactNode}) {
    return (
        <ThemeProvider>
            <AuthProvider>{children}</AuthProvider>
        </ThemeProvider>
    );
}

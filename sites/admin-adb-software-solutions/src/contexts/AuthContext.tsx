"use client";

import { API_URL, getAdminLoginUrl } from "@/lib/config";
import {
    createContext,
    ReactNode,
    useCallback,
    useContext,
    useEffect,
    useState,
} from "react";

interface User {
    id: string;
    email: string;
    firstName: string;
    lastName: string;
    isStaff: boolean;
}

interface AuthResponse {
    success: boolean;
    message: string;
    user?: {
        id: string;
        email: string;
        first_name: string;
        last_name: string;
        is_staff: boolean;
    };
}

interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    login: () => void;
    logout: () => Promise<void>;
    refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function transformUser(data: NonNullable<AuthResponse["user"]>): User {
    return {
        id: data.id,
        email: data.email,
        firstName: data.first_name,
        lastName: data.last_name,
        isStaff: data.is_staff,
    };
}

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const refreshUser = useCallback(async () => {
        try {
            setIsLoading(true);
            const response = await fetch(`${API_URL}/api/auth/me`, {
                credentials: "include",
            });

            if (!response.ok) {
                setUser(null);
                return;
            }

            const data: AuthResponse = await response.json();
            if (data.success && data.user) {
                setUser(transformUser(data.user));
            } else {
                setUser(null);
            }
        } catch {
            setUser(null);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        void refreshUser();
    }, [refreshUser]);

    const login = () => {
        window.location.assign(getAdminLoginUrl());
    };

    const logout = async () => {
        try {
            await fetch(`${API_URL}/api/auth/logout`, {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json",
                },
            });
        } finally {
            setUser(null);
        }
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                isLoading,
                isAuthenticated: user !== null,
                login,
                logout,
                refreshUser,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}

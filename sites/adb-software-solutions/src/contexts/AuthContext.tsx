"use client";

import { fetchAPI } from "@/lib/api/fetch";
import { API_URL, getAdminLoginUrl } from "@/lib/config";
import {
    createContext,
    ReactNode,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useState,
} from "react";

interface ObjectScope {
    all: boolean;
    ids: number[];
}

interface AccessScope {
    clients: ObjectScope;
    ticketQueues: ObjectScope;
}

interface User {
    id: string;
    email: string;
    firstName: string;
    lastName: string;
    isStaff: boolean;
    isSuperuser: boolean;
    permissions: string[];
    scope: AccessScope;
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
        is_superuser: boolean;
        permissions: string[];
        scope: {
            clients: ObjectScope;
            ticket_queues: ObjectScope;
        };
    };
}

interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    login: () => void;
    logout: () => Promise<void>;
    refreshUser: () => Promise<void>;
    hasPermission: (permission: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function transformUser(data: NonNullable<AuthResponse["user"]>): User {
    return {
        id: data.id,
        email: data.email,
        firstName: data.first_name,
        lastName: data.last_name,
        isStaff: data.is_staff,
        isSuperuser: data.is_superuser,
        permissions: data.permissions,
        scope: {
            clients: data.scope.clients,
            ticketQueues: data.scope.ticket_queues,
        },
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

            const data = (await response.json()) as AuthResponse;
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
            await fetchAPI(`${API_URL}/api/auth/logout`, {
                method: "POST",
            });
        } finally {
            setUser(null);
        }
    };

    const hasPermission = useCallback(
        (permission: string) =>
            user?.isSuperuser === true ||
            user?.permissions.includes(permission) === true,
        [user],
    );

    const value = useMemo<AuthContextType>(
        () => ({
            user,
            isLoading,
            isAuthenticated: user !== null,
            login,
            logout,
            refreshUser,
            hasPermission,
        }),
        [user, isLoading, refreshUser, hasPermission],
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}

"use client";

import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useState,
    type ReactNode,
} from "react";
import type { WikiUser, WikiUserProfileResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const AUTH_URL = process.env.NEXT_PUBLIC_AUTH_URL || "http://localhost:5175";

interface AuthContextType {
    user: WikiUser | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    refreshUser: () => Promise<void>;
    logout: () => Promise<void>;
    getLoginUrl: (returnTo?: string) => string;
    getSignupUrl: (returnTo?: string) => string;
    getLogoutUrl: (returnTo?: string) => string;
    getAccountUrl: () => string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function transformUser(data: WikiUserProfileResponse["user"]): WikiUser | null {
    if (!data) return null;

    return {
        id: data.id,
        email: data.email,
        firstName: data.first_name,
        lastName: data.last_name,
        role: data.role,
        bio: data.bio,
        website: data.website,
        photo: data.photo,
        github: data.github,
        twitter: data.twitter,
        bluesky: data.bluesky,
        linkedin: data.linkedin,
        instagram: data.instagram,
        facebook: data.facebook,
        devto: data.devto,
        stackoverflow: data.stackoverflow,
        youtube: data.youtube,
        twitch: data.twitch,
        isTrusted: data.is_trusted,
        canPublishDirectly: data.can_publish_directly,
        canModerate: data.can_moderate,
        isModerator: data.is_moderator,
        isStaff: data.is_staff,
        isSuperuser: data.is_superuser,
        articlesCount: data.articles_count,
    };
}

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<WikiUser | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const refreshUser = useCallback(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/wiki/me`, {
                credentials: "include",
            });

            if (!response.ok) {
                setUser(null);
                return;
            }

            const data: WikiUserProfileResponse = await response.json();

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
        refreshUser();
    }, [refreshUser]);

    const logout = useCallback(async () => {
        try {
            await fetch(`${API_BASE}/api/auth-service/logout`, {
                method: "POST",
                credentials: "include",
            });
        } finally {
            setUser(null);
        }
    }, []);

    const getLoginUrl = useCallback((returnTo?: string) => {
        const next =
            returnTo ||
            (typeof window !== "undefined" ? window.location.href : "/");
        return `${AUTH_URL}/login?next=${encodeURIComponent(next)}`;
    }, []);

    const getSignupUrl = useCallback((returnTo?: string) => {
        const next =
            returnTo ||
            (typeof window !== "undefined" ? window.location.href : "/");
        return `${AUTH_URL}/signup?next=${encodeURIComponent(next)}`;
    }, []);

    const getLogoutUrl = useCallback((returnTo?: string) => {
        const next =
            returnTo ||
            (typeof window !== "undefined" ? window.location.origin : "/");
        return `${AUTH_URL}/logout?next=${encodeURIComponent(next)}`;
    }, []);

    const getAccountUrl = useCallback(() => {
        return `${AUTH_URL}/account/security`;
    }, []);

    return (
        <AuthContext.Provider
            value={{
                user,
                isAuthenticated: !!user,
                isLoading,
                refreshUser,
                logout,
                getLoginUrl,
                getSignupUrl,
                getLogoutUrl,
                getAccountUrl,
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

/**
 * Hook to check if current user can edit a specific article.
 */
export function useCanEditArticle(authorId: string | null): boolean {
    const { user } = useAuth();

    if (!user) return false;

    // Author can always edit their own articles
    if (authorId && user.id === authorId) return true;

    // Staff and superusers can edit any article
    if (user.isStaff || user.isSuperuser) return true;

    // Moderators and admins can edit
    if (user.role === "moderator" || user.role === "admin") return true;

    return false;
}

"use client";

import {authApi, ensureCsrfToken} from "@/utils/api";
import React, {
    createContext,
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
    emailVerified: boolean;
    has2faEnabled: boolean;
    hasPasskeys: boolean;
}

interface AuthContextType {
    user: User | null;
    loading: boolean;
    isAuthenticated: boolean;
    requires2fa: boolean;
    challengeToken: string | null;
    login: (email: string, password: string) => Promise<void>;
    loginWithPasskey: () => Promise<void>;
    logout: () => Promise<void>;
    refreshUser: () => Promise<void>;
    verify2fa: (code: string, isRecoveryCode?: boolean) => Promise<void>;
    cancel2fa: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({children}: {children: React.ReactNode}) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const [requires2fa, setRequires2fa] = useState(false);
    const [challengeToken, setChallengeToken] = useState<string | null>(null);

    const refreshUser = useCallback(async () => {
        try {
            const data = await authApi.getCurrentUser();
            if (data.success && data.user) {
                setUser(data.user);
            } else {
                setUser(null);
            }
        } catch (error) {
            console.error("Failed to refresh authenticated user", error);
            setUser(null);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        void ensureCsrfToken().catch((error) => {
            console.error("Failed to initialise CSRF token", error);
        });
        void refreshUser();
    }, [refreshUser]);

    const login = async (email: string, password: string) => {
        const data = await authApi.login(email, password);

        if (!data.success) {
            throw new Error(data.message || "Login failed");
        }

        if (data.requires2fa && data.challengeToken) {
            setChallengeToken(data.challengeToken);
            setRequires2fa(true);
            return;
        }

        await refreshUser();
    };

    const loginWithPasskey = async () => {
        const {authenticateWithDiscoverableCredential} =
            await import("@/utils/webauthn");

        const beginData = await authApi.beginDiscoverableAuth();
        if (!beginData.success || !beginData.options) {
            throw new Error(
                beginData.message || "Failed to start passkey login",
            );
        }

        let options = beginData.options;
        if (typeof options === "string") {
            options = JSON.parse(options);
        }
        const credential =
            await authenticateWithDiscoverableCredential(options);

        const completeData = await authApi.completeDiscoverableAuth(credential);
        if (!completeData.success) {
            throw new Error(
                completeData.message || "Passkey authentication failed",
            );
        }

        await refreshUser();
    };

    const verify2fa = async (code: string, isRecoveryCode = false) => {
        if (!challengeToken) {
            throw new Error("No 2FA challenge in progress");
        }

        const data = await authApi.verify2FA(
            challengeToken,
            code,
            isRecoveryCode,
        );

        if (!data.success) {
            throw new Error(data.message || "Verification failed");
        }

        setRequires2fa(false);
        setChallengeToken(null);

        await refreshUser();
    };

    const cancel2fa = () => {
        setRequires2fa(false);
        setChallengeToken(null);
    };

    const logout = async () => {
        await authApi.logout();
        setUser(null);
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                loading,
                isAuthenticated: !!user,
                requires2fa,
                challengeToken,
                login,
                loginWithPasskey,
                logout,
                refreshUser,
                verify2fa,
                cancel2fa,
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

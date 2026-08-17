import { API_URL } from "./config";

let storedCsrfToken: string | null = null;

interface ApiResult {
    success: boolean;
    message?: string;
}

interface CurrentUser {
    id: string;
    email: string;
    firstName: string;
    lastName: string;
    emailVerified: boolean;
    has2faEnabled: boolean;
    hasPasskeys: boolean;
}

interface RawCurrentUser {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    email_verified: boolean;
    has_2fa_enabled: boolean;
    has_passkeys: boolean;
}

function getCsrfToken(): string | null {
    const cookies = document.cookie.split(";");
    for (const cookie of cookies) {
        const [name, value] = cookie.trim().split("=");
        if (name === "csrftoken") {
            return value;
        }
    }
    return storedCsrfToken;
}

function setCsrfToken(token: string): void {
    storedCsrfToken = token;
}

export async function fetchWithCSRF(
    url: string,
    options: RequestInit = {},
): Promise<Response> {
    const csrfToken = getCsrfToken();
    const headers: Record<string, string> = {
        ...(options.headers as Record<string, string>),
    };

    if (csrfToken) {
        headers["X-CSRFToken"] = csrfToken;
    }

    return fetch(url, {
        ...options,
        headers,
        credentials: "include",
    });
}

export async function ensureCsrfToken(): Promise<void> {
    try {
        const response = await fetch(`${API_URL}/api/auth/csrf`, {
            method: "GET",
            credentials: "include",
        });

        if (!response.ok) {
            return;
        }

        try {
            const data = (await response.json()) as { token?: string };
            if (data.token) {
                setCsrfToken(data.token);
            }
        } catch {
            // The CSRF cookie may already have been set even without a JSON body.
        }
    } catch {
        // A subsequent request may still succeed when a CSRF cookie already exists.
    }
}

async function postJson<T>(url: string, body?: unknown): Promise<T> {
    await ensureCsrfToken();
    const response = await fetchWithCSRF(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
    return response.json() as Promise<T>;
}

export const authApi = {
    async login(
        email: string,
        password: string,
    ): Promise<
        ApiResult & {
            requires2fa?: boolean;
            challengeToken?: string;
            user?: unknown;
        }
    > {
        return postJson(`${API_URL}/api/auth-service/login`, {
            email,
            password,
        });
    },

    async beginDiscoverableAuth(): Promise<
        ApiResult & { options?: Record<string, unknown> }
    > {
        return postJson(`${API_URL}/api/auth-service/webauthn/discover-auth`);
    },

    async completeDiscoverableAuth(
        credential: Record<string, unknown>,
    ): Promise<ApiResult & { user?: unknown }> {
        return postJson(
            `${API_URL}/api/auth-service/webauthn/complete-discover-auth`,
            { credential },
        );
    },

    async register(data: {
        email: string;
        password: string;
        firstName: string;
        lastName: string;
    }): Promise<ApiResult> {
        return postJson(`${API_URL}/api/auth-service/register`, {
            email: data.email,
            password: data.password,
            first_name: data.firstName,
            last_name: data.lastName,
        });
    },

    async verifyEmail(token: string): Promise<ApiResult> {
        return postJson(`${API_URL}/api/auth-service/verify-email`, { token });
    },

    async verify2FA(
        challengeToken: string,
        code: string,
        isRecoveryCode = false,
    ): Promise<ApiResult & { user?: unknown }> {
        return postJson(`${API_URL}/api/auth-service/2fa/verify`, {
            challenge_token: challengeToken,
            code,
            is_recovery_code: isRecoveryCode,
        });
    },

    async getCurrentUser(): Promise<{
        success: boolean;
        message?: string;
        user?: CurrentUser;
    }> {
        const response = await fetchWithCSRF(`${API_URL}/api/auth-service/me`, {
            headers: { "Content-Type": "application/json" },
        });
        const data = (await response.json()) as ApiResult & {
            user?: RawCurrentUser;
        };

        if (!data.success || !data.user) {
            return { success: data.success, message: data.message };
        }

        return {
            success: true,
            message: data.message,
            user: {
                id: data.user.id,
                email: data.user.email,
                firstName: data.user.first_name,
                lastName: data.user.last_name,
                emailVerified: data.user.email_verified,
                has2faEnabled: data.user.has_2fa_enabled,
                hasPasskeys: data.user.has_passkeys,
            },
        };
    },

    async logout(): Promise<ApiResult> {
        return postJson(`${API_URL}/api/auth-service/logout`);
    },

    async beginPasskeyRegistration(
        passkeyName: string,
    ): Promise<ApiResult & { options?: Record<string, unknown> }> {
        return postJson(`${API_URL}/api/auth-service/webauthn/begin-register`, {
            passkey_name: passkeyName,
        });
    },

    async completePasskeyRegistration(
        credential: Record<string, unknown>,
    ): Promise<ApiResult & { passkey?: unknown }> {
        return postJson(
            `${API_URL}/api/auth-service/webauthn/complete-register`,
            { credential },
        );
    },

    async getPasskeys(): Promise<{
        success: boolean;
        passkeys?: Array<{
            id: string;
            name: string;
            deviceType: string;
            createdAt: string;
            lastUsedAt: string | null;
            backedUp: boolean;
        }>;
    }> {
        const response = await fetchWithCSRF(
            `${API_URL}/api/auth-service/webauthn/passkeys`,
            { headers: { "Content-Type": "application/json" } },
        );
        return response.json();
    },

    async deletePasskey(passkeyId: string): Promise<ApiResult> {
        return postJson(`${API_URL}/api/auth-service/webauthn/delete`, {
            passkey_id: passkeyId,
        });
    },

    async renamePasskey(
        passkeyId: string,
        newName: string,
    ): Promise<ApiResult & { passkey?: unknown }> {
        return postJson(`${API_URL}/api/auth-service/webauthn/rename`, {
            passkey_id: passkeyId,
            new_name: newName,
        });
    },

    async changePassword(
        currentPassword: string,
        newPassword: string,
    ): Promise<ApiResult> {
        return postJson(`${API_URL}/api/auth-service/change-password`, {
            current_password: currentPassword,
            new_password: newPassword,
        });
    },

    async begin2FASetup(): Promise<
        ApiResult & { secret?: string; qrCodeUri?: string }
    > {
        return postJson(`${API_URL}/api/auth-service/2fa/setup`);
    },

    async confirm2FASetup(
        code: string,
    ): Promise<ApiResult & { recoveryCodes?: string[] }> {
        return postJson(`${API_URL}/api/auth-service/2fa/confirm`, { code });
    },

    async disable2FA(password: string): Promise<ApiResult> {
        return postJson(`${API_URL}/api/auth-service/2fa/disable`, { password });
    },

    async get2FAStatus(): Promise<{
        success: boolean;
        enabled: boolean;
        recoveryCodesRemaining?: number;
    }> {
        const response = await fetchWithCSRF(
            `${API_URL}/api/auth-service/2fa/status`,
            { headers: { "Content-Type": "application/json" } },
        );
        return response.json();
    },

    async regenerateRecoveryCodes(
        password: string,
    ): Promise<ApiResult & { recoveryCodes?: string[] }> {
        return postJson(`${API_URL}/api/auth-service/2fa/recovery-codes`, {
            password,
        });
    },

    async requestPasswordReset(email: string): Promise<ApiResult> {
        return postJson(`${API_URL}/api/auth-service/forgot-password`, { email });
    },

    async resetPassword(token: string, newPassword: string): Promise<ApiResult> {
        return postJson(`${API_URL}/api/auth-service/reset-password`, {
            token,
            new_password: newPassword,
        });
    },

    async getSessions(): Promise<{
        success: boolean;
        sessions?: Session[];
        message?: string;
    }> {
        const response = await fetchWithCSRF(`${API_URL}/api/sessions/list`, {
            method: "GET",
        });
        return response.json();
    },

    async revokeSession(sessionId: string): Promise<ApiResult> {
        return postJson(`${API_URL}/api/sessions/revoke`, {
            session_id: sessionId,
        });
    },

    async revokeAllSessions(): Promise<
        ApiResult & { revoked_count?: number }
    > {
        return postJson(`${API_URL}/api/sessions/revoke-all`);
    },
};

export interface Session {
    id: string;
    device_type: string;
    device_name: string;
    browser: string;
    operating_system: string;
    ip_address: string | null;
    location: string;
    created_at: string;
    last_activity: string;
    auth_method: string;
    is_current: boolean;
}

import {API_URL} from "./config";

// Store CSRF token in memory as fallback
let storedCsrfToken: string | null = null;

/**
 * Get the CSRF token from cookies.
 */
function getCsrfToken(): string | null {
    // First check cookies
    const cookies = document.cookie.split(";");
    for (const cookie of cookies) {
        const [name, value] = cookie.trim().split("=");
        if (name === "csrftoken") {
            return value;
        }
    }
    // Fall back to stored token
    return storedCsrfToken;
}

/**
 * Set the CSRF token in memory.
 */
function setCsrfToken(token: string): void {
    storedCsrfToken = token;
}

/**
 * Fetch with CSRF token and credentials included.
 */
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

    console.log("[FETCH] Making request", {
        url,
        method: options.method,
        csrfToken: csrfToken ? "SET" : "NOT SET",
        headers,
    });

    const response = await fetch(url, {
        ...options,
        headers,
        credentials: "include", // Always include cookies
    });

    console.log("[FETCH] Got response", {url, status: response.status});
    return response;
}

/**
 * Ensure CSRF token is available before making requests.
 */
export async function ensureCsrfToken(): Promise<void> {
    try {
        // Always fetch to ensure the CSRF cookie is set
        const response = await fetch(`${API_URL}/api/auth/csrf`, {
            method: "GET",
            credentials: "include",
        });

        if (!response.ok) {
            throw new Error(`Failed to get CSRF token: ${response.status}`);
        }

        // Try to extract token from response
        try {
            const data = await response.json();
            if (data.token) {
                setCsrfToken(data.token);
            }
        } catch {
            // Response might not be JSON, that's ok
        }
    } catch (error) {
        console.error("Error fetching CSRF token:", error);
        // Continue anyway - might already be set
    }
}

/**
 * API client for auth service.
 */
export const authApi = {
    /**
     * Login with email and password.
     */
    async login(
        email: string,
        password: string,
    ): Promise<{
        success: boolean;
        message?: string;
        requires2fa?: boolean;
        challengeToken?: string;
        user?: unknown;
    }> {
        console.log("[API] Ensuring CSRF token");
        await ensureCsrfToken();
        console.log("[API] CSRF token ensured");

        console.log("[API] Making login request", {
            url: `${API_URL}/api/auth-service/login`,
            email,
        });
        const response = await fetchWithCSRF(
            `${API_URL}/api/auth-service/login`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({email, password}),
            },
        );

        console.log("[API] Got login response", response.status);
        const data = await response.json();
        console.log("[API] Parsed login response", data);
        return data;
    },

    /**
     * Begin discoverable credential authentication (no email required).
     */
    async beginDiscoverableAuth(): Promise<{
        success: boolean;
        message?: string;
        options?: Record<string, unknown>;
    }> {
        await ensureCsrfToken();

        const response = await fetchWithCSRF(
            `${API_URL}/api/auth-service/webauthn/discover-auth`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
            },
        );

        return response.json();
    },

    /**
     * Complete discoverable credential authentication.
     */
    async completeDiscoverableAuth(
        credential: Record<string, unknown>,
    ): Promise<{
        success: boolean;
        message?: string;
        user?: unknown;
    }> {
        await ensureCsrfToken();

        const response = await fetchWithCSRF(
            `${API_URL}/api/auth-service/webauthn/complete-discover-auth`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({credential}),
            },
        );

        return response.json();
    },

    /**
     * Register a new user.
     */
    async register(data: {
        email: string;
        password: string;
        firstName: string;
        lastName: string;
    }): Promise<{
        success: boolean;
        message?: string;
    }> {
        await ensureCsrfToken();

        const response = await fetchWithCSRF(
            `${API_URL}/api/auth-service/register`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    email: data.email,
                    password: data.password,
                    first_name: data.firstName,
                    last_name: data.lastName,
                }),
            },
        );

        return response.json();
    },

    /**
     * Verify email with token.
     */
    async verifyEmail(token: string): Promise<{
        success: boolean;
        message?: string;
    }> {
        await ensureCsrfToken();

        const response = await fetchWithCSRF(
            `${API_URL}/api/auth-service/verify-email`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({token}),
            },
        );

        return response.json();
    },

    /**
     * Verify 2FA code.
     */
    async verify2FA(
        challengeToken: string,
        code: string,
        isRecoveryCode: boolean = false,
    ): Promise<{
        success: boolean;
        message?: string;
        user?: unknown;
    }> {
        await ensureCsrfToken();

        const response = await fetchWithCSRF(
            `${API_URL}/api/auth-service/2fa/verify`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    challenge_token: challengeToken,
                    code,
                    is_recovery_code: isRecoveryCode,
                }),
            },
        );

        return response.json();
    },

    /**
     * Get current user info.
     */
    async getCurrentUser(): Promise<{
        success: boolean;
        user?: {
            id: string;
            email: string;
            firstName: string;
            lastName: string;
            emailVerified: boolean;
            has2faEnabled: boolean;
            hasPasskeys: boolean;
        };
    }> {
        const response = await fetchWithCSRF(`${API_URL}/api/auth-service/me`, {
            headers: {
                "Content-Type": "application/json",
            },
        });

        const data = await response.json();
        if (data.success && data.user) {
            // Transform snake_case to camelCase
            return {
                success: true,
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
        }
        return data;
    },

    /**
     * Logout.
     */
    async logout(): Promise<{success: boolean; message?: string}> {
        await ensureCsrfToken();

        const response = await fetchWithCSRF(
            `${API_URL}/api/auth-service/logout`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
            },
        );

        return response.json();
    },

    /**
     * Begin passkey registration.
     */
    async beginPasskeyRegistration(passkeyName: string): Promise<{
        success: boolean;
        message?: string;
        options?: Record<string, unknown>;
    }> {
        await ensureCsrfToken();

        const response = await fetchWithCSRF(
            `${API_URL}/api/auth-service/webauthn/begin-register`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({passkey_name: passkeyName}),
            },
        );

        return response.json();
    },

    /**
     * Complete passkey registration.
     */
    async completePasskeyRegistration(
        credential: Record<string, unknown>,
    ): Promise<{
        success: boolean;
        message?: string;
        passkey?: unknown;
    }> {
        await ensureCsrfToken();

        const response = await fetchWithCSRF(
            `${API_URL}/api/auth-service/webauthn/complete-register`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({credential}),
            },
        );

        return response.json();
    },

    /**
     * Get list of passkeys.
     */
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
            {
                headers: {
                    "Content-Type": "application/json",
                },
            },
        );

        return response.json();
    },

    /**
     * Delete a passkey.
     */
    async deletePasskey(passkeyId: string): Promise<{
        success: boolean;
        message?: string;
    }> {
        await ensureCsrfToken();

        const response = await fetchWithCSRF(
            `${API_URL}/api/auth-service/webauthn/delete`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({passkey_id: passkeyId}),
            },
        );

        return response.json();
    },

    /**
     * Rename a passkey.
     */
    async renamePasskey(
        passkeyId: string,
        newName: string,
    ): Promise<{
        success: boolean;
        message?: string;
        passkey?: unknown;
    }> {
        await ensureCsrfToken();

        const response = await fetchWithCSRF(
            `${API_URL}/api/auth-service/webauthn/rename`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    passkey_id: passkeyId,
                    new_name: newName,
                }),
            },
        );

        return response.json();
    },

    /**
     * Change password.
     */
    async changePassword(
        currentPassword: string,
        newPassword: string,
    ): Promise<{
        success: boolean;
        message?: string;
    }> {
        await ensureCsrfToken();

        const response = await fetchWithCSRF(
            `${API_URL}/api/auth-service/change-password`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword,
                }),
            },
        );

        return response.json();
    },

    /**
     * Begin 2FA setup.
     */
    async begin2FASetup(): Promise<{
        success: boolean;
        message?: string;
        secret?: string;
        qrCodeUri?: string;
    }> {
        await ensureCsrfToken();

        const response = await fetchWithCSRF(
            `${API_URL}/api/auth-service/2fa/setup`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
            },
        );

        return response.json();
    },

    /**
     * Confirm 2FA setup with verification code.
     */
    async confirm2FASetup(code: string): Promise<{
        success: boolean;
        message?: string;
        recoveryCodes?: string[];
    }> {
        await ensureCsrfToken();

        const response = await fetchWithCSRF(
            `${API_URL}/api/auth-service/2fa/confirm`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({code}),
            },
        );

        return response.json();
    },

    /**
     * Disable 2FA.
     */
    async disable2FA(password: string): Promise<{
        success: boolean;
        message?: string;
    }> {
        await ensureCsrfToken();

        const response = await fetchWithCSRF(
            `${API_URL}/api/auth-service/2fa/disable`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({password}),
            },
        );

        return response.json();
    },

    /**
     * Get 2FA status.
     */
    async get2FAStatus(): Promise<{
        success: boolean;
        enabled: boolean;
        recoveryCodesRemaining?: number;
    }> {
        const response = await fetchWithCSRF(
            `${API_URL}/api/auth-service/2fa/status`,
            {
                headers: {
                    "Content-Type": "application/json",
                },
            },
        );

        return response.json();
    },

    /**
     * Regenerate recovery codes.
     */
    async regenerateRecoveryCodes(password: string): Promise<{
        success: boolean;
        message?: string;
        recoveryCodes?: string[];
    }> {
        await ensureCsrfToken();

        const response = await fetchWithCSRF(
            `${API_URL}/api/auth-service/2fa/recovery-codes`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({password}),
            },
        );

        return response.json();
    },

    /**
     * Request password reset.
     */
    async requestPasswordReset(email: string): Promise<{
        success: boolean;
        message?: string;
    }> {
        await ensureCsrfToken();

        const response = await fetchWithCSRF(
            `${API_URL}/api/auth-service/forgot-password`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({email}),
            },
        );

        return response.json();
    },

    /**
     * Reset password with token.
     */
    async resetPassword(
        token: string,
        newPassword: string,
    ): Promise<{
        success: boolean;
        message?: string;
    }> {
        await ensureCsrfToken();

        const response = await fetchWithCSRF(
            `${API_URL}/api/auth-service/reset-password`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({token, new_password: newPassword}),
            },
        );

        return response.json();
    },

    // ========================================================================
    // Session/Device Management
    // ========================================================================

    /**
     * Get all active sessions for the current user.
     */
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

    /**
     * Revoke (log out) a specific session.
     */
    async revokeSession(sessionId: string): Promise<{
        success: boolean;
        message?: string;
    }> {
        await ensureCsrfToken();

        const response = await fetchWithCSRF(`${API_URL}/api/sessions/revoke`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({session_id: sessionId}),
        });

        return response.json();
    },

    /**
     * Revoke all sessions except the current one.
     */
    async revokeAllSessions(): Promise<{
        success: boolean;
        message?: string;
        revoked_count?: number;
    }> {
        await ensureCsrfToken();

        const response = await fetchWithCSRF(
            `${API_URL}/api/sessions/revoke-all`,
            {
                method: "POST",
            },
        );

        return response.json();
    },
};

/**
 * Session/device information.
 */
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

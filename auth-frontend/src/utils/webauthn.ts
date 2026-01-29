/**
 * WebAuthn utilities for passkey authentication.
 * Supports both discoverable credentials (no email required) and
 * traditional email-based credential lookup.
 */

// Track active ceremony to prevent "request already in progress" errors
let activeAbortController: AbortController | null = null;

/**
 * Detect if the browser is an in-app browser (WebView) that doesn't support WebAuthn.
 * Common in-app browsers include: Google app, Facebook, Instagram, Twitter/X,
 * LinkedIn, TikTok, Snapchat, etc.
 */
function isInAppBrowser(): boolean {
    if (typeof navigator === "undefined") {
        return false;
    }

    const ua = navigator.userAgent || navigator.vendor || "";

    // Common in-app browser identifiers
    const inAppBrowserPatterns = [
        /FBAN|FBAV/i, // Facebook
        /Instagram/i, // Instagram
        /Twitter/i, // Twitter/X
        /LinkedInApp/i, // LinkedIn
        /GSA\//i, // Google Search App (Google app)
        /KAKAOTALK/i, // KakaoTalk
        /Line\//i, // LINE
        /Snapchat/i, // Snapchat
        /TikTok/i, // TikTok
        /Weibo/i, // Weibo
        /MicroMessenger/i, // WeChat
        /Pinterest/i, // Pinterest
        /Slack/i, // Slack
        /Discord/i, // Discord (in-app browser)
    ];

    return inAppBrowserPatterns.some((pattern) => pattern.test(ua));
}

/**
 * Check if WebAuthn is supported in the current browser.
 * Chrome on iOS/iPadOS 16+ supports passkeys via the iCloud Keychain.
 * In-app browsers (WebViews) generally don't support WebAuthn.
 */
export function isWebAuthnSupported(): boolean {
    if (typeof window === "undefined") {
        return false;
    }

    // In-app browsers don't have proper WebAuthn support
    if (isInAppBrowser()) {
        return false;
    }

    return typeof window.PublicKeyCredential !== "undefined";
}

/**
 * Check if platform authenticator (built-in biometric/PIN) is available.
 */
export async function isPlatformAuthenticatorAvailable(): Promise<boolean> {
    if (!isWebAuthnSupported()) {
        return false;
    }

    try {
        return await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
    } catch {
        return false;
    }
}

/**
 * Check if conditional mediation (autofill) is supported.
 */
export async function isConditionalMediationAvailable(): Promise<boolean> {
    if (!isWebAuthnSupported()) {
        return false;
    }

    try {
        return (
            typeof PublicKeyCredential.isConditionalMediationAvailable ===
                "function" &&
            (await PublicKeyCredential.isConditionalMediationAvailable())
        );
    } catch {
        return false;
    }
}

/**
 * Abort any active WebAuthn ceremony.
 * Call this before starting a new ceremony to prevent conflicts.
 */
export function abortActiveWebAuthnCeremony(): void {
    if (activeAbortController) {
        activeAbortController.abort();
        activeAbortController = null;
    }
}

/**
 * Convert a base64url string to an ArrayBuffer.
 */
export function base64urlToBuffer(base64url: string): ArrayBuffer {
    // Add padding if needed
    const padding = "=".repeat((4 - (base64url.length % 4)) % 4);
    const base64 = (base64url + padding).replace(/-/g, "+").replace(/_/g, "/");

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }

    return outputArray.buffer;
}

/**
 * Convert an ArrayBuffer to a base64url string.
 */
export function bufferToBase64url(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = "";
    for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return window
        .btoa(binary)
        .replace(/\+/g, "-")
        .replace(/\//g, "_")
        .replace(/=/g, "");
}

/**
 * Parse WebAuthn registration options from the server.
 */
export function parseRegistrationOptions(
    options: Record<string, unknown>,
): PublicKeyCredentialCreationOptions {
    const user = options.user as Record<string, unknown>;
    const rp = options.rp as Record<string, unknown>;

    console.log("[WebAuthn] Parsing registration options:", {
        rpId: rp?.id,
        rpName: rp?.name,
        userEmail: user?.name,
    });

    const parsedOptions: PublicKeyCredentialCreationOptions = {
        ...options,
        challenge: base64urlToBuffer(options.challenge as string),
        user: {
            ...user,
            id: base64urlToBuffer(user.id as string),
            name: user.name as string,
            displayName: user.displayName as string,
        },
        rp: {
            id: rp.id as string,
            name: rp.name as string,
        },
        pubKeyCredParams:
            options.pubKeyCredParams as PublicKeyCredentialParameters[],
    };

    // Handle excludeCredentials if present
    if (
        options.excludeCredentials &&
        Array.isArray(options.excludeCredentials)
    ) {
        parsedOptions.excludeCredentials = (
            options.excludeCredentials as Array<Record<string, unknown>>
        ).map((cred) => ({
            type: "public-key" as const,
            id: base64urlToBuffer(cred.id as string),
            transports: cred.transports as AuthenticatorTransport[] | undefined,
        }));
    }

    return parsedOptions;
}

/**
 * Parse WebAuthn authentication options from the server.
 */
export function parseAuthenticationOptions(
    options: Record<string, unknown>,
): PublicKeyCredentialRequestOptions {
    console.log("[WebAuthn] Parsing authentication options:", {
        rpId: options.rpId,
        allowCredentialsCount:
            (options.allowCredentials as Array<unknown>)?.length || 0,
    });

    const parsedOptions: PublicKeyCredentialRequestOptions = {
        challenge: base64urlToBuffer(options.challenge as string),
        rpId: options.rpId as string,
        timeout: options.timeout as number,
        userVerification:
            options.userVerification as UserVerificationRequirement,
    };

    // Handle allowCredentials if present
    if (options.allowCredentials && Array.isArray(options.allowCredentials)) {
        parsedOptions.allowCredentials = (
            options.allowCredentials as Array<Record<string, unknown>>
        ).map((cred) => ({
            type: "public-key" as const,
            id: base64urlToBuffer(cred.id as string),
            transports: cred.transports as AuthenticatorTransport[] | undefined,
        }));
    }

    return parsedOptions;
}

/**
 * Encode a credential response for sending to the server.
 */
export function encodeRegistrationCredential(
    credential: PublicKeyCredential,
): Record<string, unknown> {
    const response = credential.response as AuthenticatorAttestationResponse;

    return {
        id: credential.id,
        rawId: bufferToBase64url(credential.rawId),
        type: credential.type,
        authenticatorAttachment:
            (
                credential as PublicKeyCredential & {
                    authenticatorAttachment?: string;
                }
            ).authenticatorAttachment || null,
        response: {
            clientDataJSON: bufferToBase64url(response.clientDataJSON),
            attestationObject: bufferToBase64url(response.attestationObject),
            transports: response.getTransports?.() || [],
        },
    };
}

/**
 * Encode an authentication credential response for sending to the server.
 */
export function encodeAuthenticationCredential(
    credential: PublicKeyCredential,
): Record<string, unknown> {
    const response = credential.response as AuthenticatorAssertionResponse;

    const encoded: Record<string, unknown> = {
        id: credential.id,
        rawId: bufferToBase64url(credential.rawId),
        type: credential.type,
        response: {
            clientDataJSON: bufferToBase64url(response.clientDataJSON),
            authenticatorData: bufferToBase64url(response.authenticatorData),
            signature: bufferToBase64url(response.signature),
        },
    };

    // Include userHandle if present (for discoverable credentials)
    if (response.userHandle) {
        (encoded.response as Record<string, unknown>).userHandle =
            bufferToBase64url(response.userHandle);
    }

    return encoded;
}

/**
 * Create a new passkey (registration).
 */
export async function createPasskey(
    options: Record<string, unknown>,
): Promise<Record<string, unknown>> {
    // Abort any existing ceremony
    abortActiveWebAuthnCeremony();

    const abortController = new AbortController();
    activeAbortController = abortController;

    // Set a timeout
    const timeoutId = setTimeout(() => {
        abortController.abort();
    }, 120000); // 2 minute timeout

    try {
        const credential = (await navigator.credentials.create({
            publicKey: parseRegistrationOptions(options),
            signal: abortController.signal,
        })) as PublicKeyCredential | null;

        if (!credential) {
            throw new Error("No credential returned from authenticator");
        }

        return encodeRegistrationCredential(credential);
    } finally {
        clearTimeout(timeoutId);
        if (activeAbortController === abortController) {
            activeAbortController = null;
        }
    }
}

/**
 * Authenticate with a passkey (discoverable credentials - no email required).
 */
export async function authenticateWithDiscoverableCredential(
    options: Record<string, unknown>,
): Promise<Record<string, unknown>> {
    // Abort any existing ceremony
    abortActiveWebAuthnCeremony();

    const abortController = new AbortController();
    activeAbortController = abortController;

    // Set a timeout
    const timeoutId = setTimeout(() => {
        abortController.abort();
    }, 120000); // 2 minute timeout

    try {
        const credential = (await navigator.credentials.get({
            publicKey: parseAuthenticationOptions(options),
            signal: abortController.signal,
        })) as PublicKeyCredential | null;

        if (!credential) {
            throw new Error("No credential returned from authenticator");
        }

        return encodeAuthenticationCredential(credential);
    } finally {
        clearTimeout(timeoutId);
        if (activeAbortController === abortController) {
            activeAbortController = null;
        }
    }
}

/**
 * Authenticate with a passkey using email-based credential lookup.
 * This is the legacy mode that requires email first.
 */
export async function authenticateWithPasskey(
    options: Record<string, unknown>,
): Promise<Record<string, unknown>> {
    return authenticateWithDiscoverableCredential(options);
}

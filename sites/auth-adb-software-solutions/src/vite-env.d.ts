/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_API_URL: string;
    readonly VITE_APP_URL: string;
    readonly VITE_ADMIN_URL: string;
    readonly VITE_DOCS_URL: string;
    readonly VITE_AUTH_URL: string;
}

interface ImportMeta {
    readonly env: ImportMetaEnv;
}

// Rewardful types
interface Window {
    rewardful?: (event: string, callback: () => void) => void;
    Rewardful?: {
        referral?: string;
    };
}

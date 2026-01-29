import {authApi} from "@/utils/api";
import {getDefaultAppUrl} from "@/utils/config";
import {useEffect} from "react";

export default function LogoutPage() {
    useEffect(() => {
        const performLogout = async () => {
            try {
                await authApi.logout();
            } catch {
                // Ignore errors - still redirect
            }
            window.location.href = getDefaultAppUrl();
        };

        performLogout();
    }, []);

    return (
        <div className="text-center">
            <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-brand border-t-transparent" />
            <p className="mt-4 text-slate-600 dark:text-slate-400">
                Signing out...
            </p>
        </div>
    );
}

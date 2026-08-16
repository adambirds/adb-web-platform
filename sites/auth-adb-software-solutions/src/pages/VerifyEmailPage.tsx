import Alert from "@/components/Alert";
import {authApi} from "@/utils/api";
import {getRedirectUrl} from "@/utils/config";
import {useEffect, useState} from "react";
import {useParams} from "react-router-dom";

export default function VerifyEmailPage() {
    const {token} = useParams<{token: string}>();
    const [status, setStatus] = useState<"loading" | "success" | "error">(
        "loading",
    );
    const [message, setMessage] = useState("");

    useEffect(() => {
        if (!token) {
            setStatus("error");
            setMessage("Invalid verification link");
            return;
        }

        const verifyEmail = async () => {
            try {
                const result = await authApi.verifyEmail(token);
                if (result.success) {
                    setStatus("success");
                    setMessage("Your email has been verified!");
                } else {
                    setStatus("error");
                    setMessage(result.message || "Verification failed");
                }
            } catch {
                setStatus("error");
                setMessage("An error occurred during verification");
            }
        };

        verifyEmail();
    }, [token]);

    if (status === "loading") {
        return (
            <div className="text-center">
                <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-brand border-t-transparent" />
                <p className="mt-4 text-slate-600 dark:text-slate-400">
                    Verifying your email...
                </p>
            </div>
        );
    }

    return (
        <div className="text-center">
            <Alert
                type={status === "success" ? "success" : "error"}
                className="mb-6"
            >
                {message}
            </Alert>

            {status === "success" && (
                <div className="space-y-4">
                    <p className="text-slate-600 dark:text-slate-400">
                        You can now set up additional security options:
                    </p>
                    <div className="flex flex-col gap-3">
                        <a href="/setup-passkey" className="btn btn-passkey">
                            Set up Passkey (optional)
                        </a>
                        <a href="/setup-2fa" className="btn btn-secondary">
                            Set up 2FA (optional)
                        </a>
                        <button
                            onClick={() => {
                                const redirectUrl = getRedirectUrl();
                                window.location.href = redirectUrl;
                            }}
                            className="btn btn-primary"
                        >
                            Skip and continue to app
                        </button>
                    </div>
                </div>
            )}

            {status === "error" && (
                <a href="/login" className="btn btn-primary mt-4">
                    Go to login
                </a>
            )}
        </div>
    );
}

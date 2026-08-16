import {useState} from "react";

interface TwoFactorVerificationProps {
    onVerify: (code: string, isRecoveryCode: boolean) => Promise<void>;
    onCancel: () => void;
    isLoading: boolean;
    error: string | null;
}

export default function TwoFactorVerification({
    onVerify,
    onCancel,
    isLoading,
    error,
}: TwoFactorVerificationProps) {
    const [code, setCode] = useState("");
    const [isRecoveryMode, setIsRecoveryMode] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!code.trim()) return;
        await onVerify(code.trim(), isRecoveryMode);
    };

    return (
        <div className="space-y-6">
            <p className="text-center text-sm text-slate-600 dark:text-slate-400">
                {isRecoveryMode
                    ? "Enter one of your recovery codes"
                    : "Enter the 6-digit code from your authenticator app"}
            </p>

            {error && (
                <div className="rounded-md bg-red-50 p-4 text-sm text-red-800 dark:bg-red-900/30 dark:text-red-300">
                    {error}
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label htmlFor="code" className="sr-only">
                        {isRecoveryMode ? "Recovery code" : "Verification code"}
                    </label>
                    <input
                        id="code"
                        name="code"
                        type="text"
                        autoComplete="one-time-code"
                        required
                        placeholder={
                            isRecoveryMode ? "XXXX-XXXX-XXXX" : "000000"
                        }
                        value={code}
                        onChange={(e) => setCode(e.target.value)}
                        className="text-center text-lg tracking-widest"
                        maxLength={isRecoveryMode ? 14 : 6}
                    />
                </div>

                <button
                    type="submit"
                    disabled={isLoading || !code.trim()}
                    className="btn btn-primary w-full"
                >
                    {isLoading ? "Verifying..." : "Verify"}
                </button>
            </form>

            <div className="flex flex-col items-center gap-2">
                <button
                    type="button"
                    onClick={() => {
                        setIsRecoveryMode(!isRecoveryMode);
                        setCode("");
                    }}
                    className="text-sm text-brand hover:underline"
                >
                    {isRecoveryMode
                        ? "Use authenticator app instead"
                        : "Use a recovery code instead"}
                </button>
                <button
                    type="button"
                    onClick={onCancel}
                    className="text-sm text-slate-500 hover:text-slate-700"
                >
                    Cancel
                </button>
            </div>
        </div>
    );
}

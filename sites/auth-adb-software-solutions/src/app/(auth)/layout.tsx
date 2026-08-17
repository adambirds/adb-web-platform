import LogoComponent from "@/components/logo/LogoComponent";

export default function AuthLayout({children}: {children: React.ReactNode}) {
    return (
        <div className="flex min-h-screen flex-col justify-center bg-white px-6 py-12 lg:px-8 dark:bg-slate-900">
            <div className="sm:mx-auto sm:w-full sm:max-w-md">
                <div className="flex justify-center">
                    <LogoComponent className="h-16 w-auto" />
                </div>
            </div>

            <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
                <div className="bg-white px-6 py-8 shadow-sm ring-1 ring-slate-900/5 sm:rounded-lg sm:px-12 dark:bg-slate-800">
                    {children}
                </div>
            </div>
        </div>
    );
}

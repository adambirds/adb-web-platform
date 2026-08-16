export const metadata = {
    title: "Clients",
};

export default function ClientsPage() {
    return (
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between">
                <h1 className="text-adb-navy text-3xl font-bold dark:text-white">
                    Clients
                </h1>
                <button className="bg-adb-cyan text-adb-navy-950 hover:bg-adb-cyan-600 rounded-lg px-4 py-2 font-medium transition">
                    Add Client
                </button>
            </div>

            <div className="border-adb-navy-200 dark:border-adb-navy-800 dark:bg-adb-navy-900 mt-8 rounded-lg border bg-white p-8 text-center">
                <p className="text-adb-navy-600 dark:text-adb-navy-300">
                    No clients yet. Add your first client to get started.
                </p>
            </div>
        </div>
    );
}

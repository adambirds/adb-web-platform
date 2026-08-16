export const metadata = {
    title: "Leads",
};

export default function LeadsPage() {
    return (
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
            <h1 className="text-adb-navy text-3xl font-bold dark:text-white">
                Leads
            </h1>

            <div className="border-adb-navy-200 dark:border-adb-navy-800 dark:bg-adb-navy-900 mt-8 rounded-lg border bg-white p-8 text-center">
                <p className="text-adb-navy-600 dark:text-adb-navy-300">
                    No leads yet. Leads from your contact form will appear here.
                </p>
            </div>
        </div>
    );
}

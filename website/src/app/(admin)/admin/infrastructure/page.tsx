export const metadata = {
    title: "Infrastructure",
};

export default function InfrastructurePage() {
    return (
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
            <h1 className="text-adb-navy text-3xl font-bold dark:text-white">
                Infrastructure
            </h1>

            <div className="mt-8 grid gap-6 md:grid-cols-2">
                <a
                    href="/admin/infrastructure/servers"
                    className="border-adb-navy-200 hover:border-adb-cyan dark:border-adb-navy-800 dark:bg-adb-navy-900 rounded-lg border bg-white p-6 transition"
                >
                    <h3 className="text-adb-navy font-semibold dark:text-white">
                        Servers
                    </h3>
                    <p className="text-adb-navy-600 dark:text-adb-navy-300 mt-2 text-sm">
                        Manage physical and virtual servers
                    </p>
                </a>

                <a
                    href="/admin/infrastructure/databases"
                    className="border-adb-navy-200 hover:border-adb-cyan dark:border-adb-navy-800 dark:bg-adb-navy-900 rounded-lg border bg-white p-6 transition"
                >
                    <h3 className="text-adb-navy font-semibold dark:text-white">
                        Databases
                    </h3>
                    <p className="text-adb-navy-600 dark:text-adb-navy-300 mt-2 text-sm">
                        Manage database instances
                    </p>
                </a>

                <a
                    href="/admin/infrastructure/websites"
                    className="border-adb-navy-200 hover:border-adb-cyan dark:border-adb-navy-800 dark:bg-adb-navy-900 rounded-lg border bg-white p-6 transition"
                >
                    <h3 className="text-adb-navy font-semibold dark:text-white">
                        Websites
                    </h3>
                    <p className="text-adb-navy-600 dark:text-adb-navy-300 mt-2 text-sm">
                        Manage web applications
                    </p>
                </a>

                <a
                    href="/admin/infrastructure/domains"
                    className="border-adb-navy-200 hover:border-adb-cyan dark:border-adb-navy-800 dark:bg-adb-navy-900 rounded-lg border bg-white p-6 transition"
                >
                    <h3 className="text-adb-navy font-semibold dark:text-white">
                        Domains
                    </h3>
                    <p className="text-adb-navy-600 dark:text-adb-navy-300 mt-2 text-sm">
                        Manage domain registrations
                    </p>
                </a>
            </div>
        </div>
    );
}

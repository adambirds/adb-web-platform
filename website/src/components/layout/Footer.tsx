export function Footer() {
    return (
        <footer className="border-adb-navy-200/20 bg-adb-navy-950 dark:bg-adb-navy-950 border-t">
            <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
                <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
                    <div>
                        <h3 className="text-lg font-semibold text-white">
                            ADB Software Solutions
                        </h3>
                        <p className="text-adb-navy-300 mt-2 text-sm">
                            Building reliable, scalable software solutions.
                        </p>
                    </div>

                    <div>
                        <h4 className="font-semibold text-white">Company</h4>
                        <ul className="mt-4 space-y-2">
                            <li>
                                <a
                                    href="/about"
                                    className="text-adb-navy-300 hover:text-adb-cyan text-sm"
                                >
                                    About
                                </a>
                            </li>
                            <li>
                                <a
                                    href="/services"
                                    className="text-adb-navy-300 hover:text-adb-cyan text-sm"
                                >
                                    Services
                                </a>
                            </li>
                            <li>
                                <a
                                    href="/blog"
                                    className="text-adb-navy-300 hover:text-adb-cyan text-sm"
                                >
                                    Blog
                                </a>
                            </li>
                        </ul>
                    </div>

                    <div>
                        <h4 className="font-semibold text-white">Resources</h4>
                        <ul className="mt-4 space-y-2">
                            <li>
                                <a
                                    href="/portfolio"
                                    className="text-adb-navy-300 hover:text-adb-cyan text-sm"
                                >
                                    Portfolio
                                </a>
                            </li>
                            <li>
                                <a
                                    href="/faqs"
                                    className="text-adb-navy-300 hover:text-adb-cyan text-sm"
                                >
                                    FAQs
                                </a>
                            </li>
                            <li>
                                <a
                                    href="/contact"
                                    className="text-adb-navy-300 hover:text-adb-cyan text-sm"
                                >
                                    Contact
                                </a>
                            </li>
                        </ul>
                    </div>

                    <div>
                        <h4 className="font-semibold text-white">Legal</h4>
                        <ul className="mt-4 space-y-2">
                            <li>
                                <a
                                    href="/privacy"
                                    className="text-adb-navy-300 hover:text-adb-cyan text-sm"
                                >
                                    Privacy
                                </a>
                            </li>
                            <li>
                                <a
                                    href="/terms"
                                    className="text-adb-navy-300 hover:text-adb-cyan text-sm"
                                >
                                    Terms
                                </a>
                            </li>
                        </ul>
                    </div>
                </div>

                <div className="border-adb-navy-800 mt-8 border-t pt-8 text-center">
                    <p className="text-adb-navy-300 text-sm">
                        © 2026 ADB Software Solutions. All rights reserved.
                    </p>
                </div>
            </div>
        </footer>
    );
}

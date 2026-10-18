import Image from "next/image";

export function BrandLogo() {
    return (
        <span className="software-logo">
            <Image
                src="/brand/adb-software-logo.svg"
                alt="ADB Software Solutions"
                width={741}
                height={469}
                className="software-logo-light"
                priority
            />
            <Image
                src="/brand/adb-software-logo-dark.svg"
                alt="ADB Software Solutions"
                width={741}
                height={469}
                className="software-logo-dark"
                priority
            />
        </span>
    );
}

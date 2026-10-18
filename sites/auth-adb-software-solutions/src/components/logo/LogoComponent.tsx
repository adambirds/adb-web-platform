import Image from "next/image";

export default function LogoComponent({className = ""}: {className?: string}) {
    return (
        <span className={`inline-block shrink-0 ${className}`}>
            <Image
                src="/brand/adb-software-logo.svg"
                alt="ADB Software Solutions"
                width={741}
                height={469}
                className="h-full w-auto dark:hidden"
                priority
            />
            <Image
                src="/brand/adb-software-logo-dark.svg"
                alt="ADB Software Solutions"
                width={741}
                height={469}
                className="hidden h-full w-auto dark:block"
                priority
            />
        </span>
    );
}

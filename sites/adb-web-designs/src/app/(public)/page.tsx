import { HomePage } from "@/components/public/HomePage";
import { redirectWordPressEntry } from "@/components/public/WordPressEntry";

export default async function Page({
    searchParams,
}: {
    searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
    await redirectWordPressEntry(await searchParams);
    return <HomePage />;
}

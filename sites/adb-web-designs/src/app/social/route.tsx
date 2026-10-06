import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { socialImage } from "@adb/ui/public/SocialImage";
import { site } from "@/content/site";
export const runtime = "nodejs";
export async function GET(request: Request) {
    const title =
        new URL(request.url).searchParams.get("title")?.trim().slice(0, 110) ||
        site.name;
    const logo = await readFile(
        join(process.cwd(), "public/brand/logo-dark.png"),
    );
    return socialImage(
        site,
        title,
        `data:image/png;base64,${logo.toString("base64")}`,
    );
}

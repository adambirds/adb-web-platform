import { handlePublicContact } from "@adb/ui/public/contact";
import { site } from "@/content/site";
export async function POST(request: Request) {
    return handlePublicContact(request, site);
}

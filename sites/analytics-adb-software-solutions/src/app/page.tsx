import {redirect} from "next/navigation";
import {ANALYTICS_URL, loginUrl} from "./client";

export default function Page() {
    redirect(loginUrl(new URL("/dashboard", ANALYTICS_URL).toString()));
}

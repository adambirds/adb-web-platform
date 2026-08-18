"use client";

import ResetPasswordPage from "@/screens/ResetPasswordPage";
import {useParams} from "next/navigation";

export default function Page() {
    const params = useParams<{token: string}>();

    if (!params) {
        return null;
    }

    return <ResetPasswordPage token={params.token} />;
}

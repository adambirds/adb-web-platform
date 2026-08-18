"use client";

import VerifyEmailPage from "@/pages/VerifyEmailPage";
import {useParams} from "next/navigation";

export default function Page() {
    const params = useParams<{token: string}>();

    if (!params) {
        return null;
    }

    return <VerifyEmailPage token={params.token} />;
}

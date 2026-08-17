"use client";

import VerifyEmailPage from "@/pages/VerifyEmailPage";
import {useParams} from "next/navigation";

export default function Page() {
    const {token} = useParams<{token: string}>();
    return <VerifyEmailPage token={token} />;
}

"use client";

import ResetPasswordPage from "@/pages/ResetPasswordPage";
import {useParams} from "next/navigation";

export default function Page() {
    const {token} = useParams<{token: string}>();
    return <ResetPasswordPage token={token} />;
}

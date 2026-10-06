"use client";
import { useId, useState } from "react";
import Image from "next/image";
import { API_URL } from "@/lib/config";
import { fetchAPI } from "@/lib/api/fetch";
import { Button } from "@/components/ui";

export function ContentImageEditor({
    kind,
    itemId,
    field,
    label,
    initialUrl,
}: {
    kind: "portfolio" | "blogpost" | "testimonial";
    itemId: number;
    field: "image" | "featured_image";
    label: string;
    initialUrl: string | null;
}) {
    const id = useId();
    const [url, setUrl] = useState(initialUrl);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    async function change(file?: File) {
        if (file && file.size > 8 * 1024 * 1024) {
            setError("Choose an image smaller than 8 MB.");
            return;
        }
        setBusy(true);
        setError("");
        try {
            const body = new FormData();
            if (file) body.set("image", file);
            const result = (await fetchAPI(
                `${API_URL}/api/admin/website/media/${kind}/${itemId}/${field}`,
                { method: file ? "POST" : "DELETE", ...(file ? { body } : {}) },
            )) as { image_url: string | null };
            setUrl(result.image_url);
        } catch (failure) {
            setError(
                failure instanceof Error
                    ? failure.message
                    : "Unable to update the image.",
            );
        } finally {
            setBusy(false);
        }
    }
    return (
        <div className="border-adb-navy-300 dark:border-adb-navy-700 space-y-3 rounded-md border p-4">
            <label htmlFor={id} className="block text-sm font-medium">
                {label}
            </label>
            {url ? (
                <Image
                    src={url}
                    width={320}
                    height={210}
                    alt="Current content image preview"
                    className="h-auto max-h-52 w-auto"
                    unoptimized
                />
            ) : null}
            <input
                id={id}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                disabled={busy}
                onChange={(event) => {
                    const file = event.target.files?.[0];
                    if (file) void change(file);
                    event.target.value = "";
                }}
                className="block text-sm"
            />
            <p className="text-xs">
                PNG, JPEG or WebP, up to 8 MB. Images are saved immediately;
                edit the alternative text below.
            </p>
            {url ? (
                <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={busy}
                    onClick={() => void change()}
                >
                    Remove image
                </Button>
            ) : null}
            {busy ? (
                <p role="status" className="text-sm">
                    Updating image…
                </p>
            ) : null}
            {error ? (
                <p
                    role="alert"
                    className="text-sm text-red-600 dark:text-red-300"
                >
                    {error}
                </p>
            ) : null}
        </div>
    );
}

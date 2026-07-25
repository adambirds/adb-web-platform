"use client";

import { Button, Input, Textarea } from "@/components/ui";
import { PublicAPI } from "@/lib/api/endpoints";
import { fetchAPI } from "@/lib/api/fetch";
import { useState } from "react";

export function ContactForm() {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [status, setStatus] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setIsSubmitting(true);
        setStatus(null);
        setError(null);

        const formData = new FormData(event.currentTarget);
        const payload = Object.fromEntries(formData.entries());

        try {
            await fetchAPI(PublicAPI.contact.submit(), {
                method: "POST",
                body: JSON.stringify(payload),
            });
            setStatus("Thanks! We'll be in touch shortly.");
            event.currentTarget.reset();
        } catch (err) {
            setError("Something went wrong. Please try again.");
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
                <Input name="name" placeholder="Your name" required />
                <Input
                    name="email"
                    type="email"
                    placeholder="Email address"
                    required
                />
            </div>
            <div className="grid gap-4 md:grid-cols-2">
                <Input name="company" placeholder="Company (optional)" />
                <Input name="phone" placeholder="Phone (optional)" />
            </div>
            <Textarea
                name="message"
                rows={6}
                placeholder="How can I help?"
                required
            />
            {status ? (
                <p className="text-sm text-emerald-400">{status}</p>
            ) : null}
            {error ? <p className="text-sm text-red-400">{error}</p> : null}
            <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Sending..." : "Send message"}
            </Button>
        </form>
    );
}

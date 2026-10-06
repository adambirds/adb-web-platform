"use client";
import {useState, type FormEvent} from "react";

export function ContactForm({
    services,
}: {
    services: {slug: string; title: string}[];
}) {
    const [error, setError] = useState("");
    const [sending, setSending] = useState(false);
    async function submit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (sending) return;
        const form = event.currentTarget;
        const data = new FormData(form);
        setSending(true);
        setError("");
        try {
            const selection = services.find(
                (service) => service.slug === data.get("service"),
            );
            const body = {
                name: String(data.get("name") || ""),
                email: String(data.get("email") || ""),
                company: String(data.get("company") || ""),
                website: String(data.get("website") || ""),
                source_path: window.location.pathname,
                message: `${selection ? `Service: ${selection.title}\n\n` : ""}${String(data.get("message") || "")}`,
            };
            const response = await fetch("/api/contact", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(body),
            });
            if (!response.ok) {
                const result = (await response.json().catch(() => ({}))) as {
                    message?: string;
                };
                throw new Error(
                    result.message ||
                        "Your enquiry could not be sent. Please try again.",
                );
            }
            window.location.assign("/contact/thank-you/");
        } catch (failure) {
            setError(
                failure instanceof Error
                    ? failure.message
                    : "Your enquiry could not be sent. Please try again.",
            );
            setSending(false);
        }
    }
    return (
        <form className="contact-form" onSubmit={submit} aria-busy={sending}>
            <div className="form-grid">
                <div>
                    <label htmlFor="contact-name">Your name</label>
                    <input
                        id="contact-name"
                        name="name"
                        autoComplete="name"
                        maxLength={150}
                        required
                    />
                </div>
                <div>
                    <label htmlFor="contact-email">Email address</label>
                    <input
                        id="contact-email"
                        name="email"
                        type="email"
                        autoComplete="email"
                        maxLength={254}
                        required
                    />
                </div>
            </div>
            <div>
                <label htmlFor="contact-company">
                    Business or project name{" "}
                    <span className="muted">(optional)</span>
                </label>
                <input
                    id="contact-company"
                    name="company"
                    autoComplete="organization"
                    maxLength={200}
                />
            </div>
            <div>
                <label htmlFor="contact-service">What can I help with?</label>
                <select id="contact-service" name="service" defaultValue="">
                    <option value="">I’d like to discuss a project</option>
                    {services.map((service) => (
                        <option key={service.slug} value={service.slug}>
                            {service.title}
                        </option>
                    ))}
                </select>
            </div>
            <div>
                <label htmlFor="contact-message">Tell me about it</label>
                <textarea
                    id="contact-message"
                    name="message"
                    minLength={10}
                    maxLength={9000}
                    rows={7}
                    required
                    placeholder="What would you like to build, change or fix?"
                />
            </div>
            <div className="form-trap" aria-hidden="true">
                <label htmlFor="contact-website">Leave this field empty</label>
                <input
                    id="contact-website"
                    name="website"
                    tabIndex={-1}
                    autoComplete="off"
                />
            </div>
            <p className="form-notice">
                Your details will be used to respond to your enquiry. Read the{" "}
                <a href="/privacy-policy/">privacy policy</a>. Please don’t
                include passwords or other secrets.
            </p>
            {error ? (
                <p className="form-error" role="alert">
                    {error}
                </p>
            ) : null}
            <button type="submit" className="angled-button" disabled={sending}>
                {sending ? "Sending…" : "Send enquiry"}
                <span aria-hidden="true">→</span>
            </button>
        </form>
    );
}

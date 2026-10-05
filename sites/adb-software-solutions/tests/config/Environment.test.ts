const previous = process.env.NEXT_PUBLIC_API_URL;
afterEach(() => {
    if (previous === undefined) delete process.env.NEXT_PUBLIC_API_URL;
    else process.env.NEXT_PUBLIC_API_URL = previous;
    jest.resetModules();
});
test.each(["https://api.example.test", "https://api.example.test/"])(
    "uses one backend origin for admin, public, auth and live endpoints (%s)",
    async (origin) => {
        process.env.NEXT_PUBLIC_API_URL = origin;
        jest.resetModules();
        const { API_URL } = await import("@/lib/config");
        const { AdminAPI } = await import("@/lib/api/endpoints");
        const { LeadEmailAPI } = await import("@/lib/api/leadEmail");
        const { TicketFocusAPI } = await import("@/lib/api/ticketFocus");
        expect(`${API_URL}/api/admin/events`).toBe(
            "https://api.example.test/api/admin/events",
        );
        expect(AdminAPI.clients.list()).toBe(
            "https://api.example.test/api/admin/clients",
        );
        expect(LeadEmailAPI.options(4)).toBe(
            "https://api.example.test/api/admin/leads/4/email-options",
        );
        expect(TicketFocusAPI.list()).toBe(
            "https://api.example.test/api/admin/ticket-focus",
        );
    },
);

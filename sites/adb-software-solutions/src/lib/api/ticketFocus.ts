import { API_URL } from "@/lib/config";

const API_BASE_URL = `${API_URL}/api`;

export const TicketFocusAPI = {
    list: (query = "") =>
        `${API_BASE_URL}/admin/ticket-focus${query ? `?${query}` : ""}`,
    queuePreferences: () =>
        `${API_BASE_URL}/admin/ticket-focus/queue-preferences`,
};

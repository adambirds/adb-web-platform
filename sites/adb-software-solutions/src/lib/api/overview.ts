import { API_URL } from "@/lib/config";

const API_BASE_URL = `${API_URL}/api`;

export const OverviewAPI = {
    clients: (query = "") =>
        `${API_BASE_URL}/admin/client-overview${query ? `?${query}` : ""}`,
    leads: (query = "") =>
        `${API_BASE_URL}/admin/lead-overview${query ? `?${query}` : ""}`,
};

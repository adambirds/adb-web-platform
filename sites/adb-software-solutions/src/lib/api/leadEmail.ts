import { API_URL } from "@/lib/config";

const API_BASE_URL = `${API_URL}/api`;

export const LeadEmailAPI = {
    options: (leadId: number) =>
        `${API_BASE_URL}/admin/leads/${leadId}/email-options`,
    conversations: (leadId: number) =>
        `${API_BASE_URL}/admin/leads/${leadId}/conversations`,
    send: (leadId: number) => `${API_BASE_URL}/admin/leads/${leadId}/email`,
};

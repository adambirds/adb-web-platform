export type KnowledgeContext =
    | { ownership_type: "internal"; client_id: null }
    | { ownership_type: "client"; client_id: number };

export function parseKnowledgeContext(
    ownership?: string,
    clientId?: string,
): KnowledgeContext | null {
    if (ownership === "internal")
        return clientId
            ? null
            : { ownership_type: "internal", client_id: null };
    if (ownership && ownership !== "client") return null;
    const id = clientId ? Number(clientId) : NaN;
    return Number.isSafeInteger(id) && id > 0
        ? { ownership_type: "client", client_id: id }
        : null;
}

export function knowledgeContextParams(
    context: KnowledgeContext,
): URLSearchParams {
    const params = new URLSearchParams({
        ownership_type: context.ownership_type,
    });
    if (context.client_id !== null)
        params.set("client_id", String(context.client_id));
    return params;
}

export function knowledgeBaseHref(context: KnowledgeContext): string {
    return `/admin/knowledge-base?${knowledgeContextParams(context)}`;
}

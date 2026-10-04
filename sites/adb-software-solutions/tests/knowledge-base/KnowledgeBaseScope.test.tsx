import "@testing-library/jest-dom";
import { KnowledgeBaseWorkspace } from "@/app/(admin)/admin/knowledge-base/KnowledgeBaseWorkspace";
import { KnowledgeDocumentForm } from "@/app/(admin)/admin/knowledge-base/KnowledgeDocumentForm";
import {
    parseKnowledgeContext,
    type KnowledgeContext,
} from "@/app/(admin)/admin/knowledge-base/context";
import NewKnowledgeDocumentPage from "@/app/(admin)/admin/knowledge-base/documents/new/page";
import { KnowledgeBasePanel } from "@/components/admin/KnowledgeBasePanel";
import { fetchAPI } from "@/lib/api/fetch";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

jest.mock("@/lib/api/fetch", () => ({ fetchAPI: jest.fn() }));
jest.mock("@/contexts/AuthContext", () => ({
    useAuth: () => ({ hasPermission: () => true }),
}));
jest.mock("@/app/(admin)/admin/knowledge-base/MarkdownContent", () => ({
    MarkdownContent: ({ content }: { content: string }) => <div>{content}</div>,
}));
const mockPush = jest.fn();
const mockRefresh = jest.fn();
const mockRedirect = jest.fn(() => {
    throw new Error("Redirect to context picker");
});
jest.mock("next/navigation", () => ({
    useRouter: () => ({ push: mockPush, refresh: mockRefresh }),
    redirect: () => mockRedirect(),
}));
const mockFetch = jest.mocked(fetchAPI);
const clientContext: KnowledgeContext = {
    ownership_type: "client",
    client_id: 3,
};
const internalContext: KnowledgeContext = {
    ownership_type: "internal",
    client_id: null,
};
const folder = {
    id: 10,
    name: "Client folder",
    path: "Client folder",
    ownership_type: "client",
    client_id: 3,
    client_name: "Client A",
    parent_id: null,
    order: 0,
    description: "",
};
const internalFolder = {
    ...folder,
    id: 11,
    name: "Internal folder",
    path: "Internal folder",
    ownership_type: "internal",
    client_id: null,
    client_name: null,
};
const document = {
    id: 20,
    title: "Client article",
    summary: "",
    ownership_type: "client",
    client_id: 3,
    client_name: "Client A",
    section_id: 10,
    section_path: "Client folder",
    tags: [],
    archived: false,
    updated_at: "2026-01-01T00:00:00Z",
    version_count: 1,
};
const options = {
    clients: [{ id: 3, label: "Client A" }],
    sections: [folder],
    resources: [],
    credentials: [],
};
const workspace = {
    ownership_type: "client",
    client_id: 3,
    client_name: "Client A",
    sections: [folder],
    documents: [document],
    total_documents: 1,
    page: 1,
    page_size: 30,
};
beforeEach(() => {
    mockFetch.mockReset();
    mockPush.mockReset();
    mockRefresh.mockReset();
    mockRedirect.mockClear();
    mockFetch.mockImplementation(async (url: string, request?: RequestInit) => {
        if (request?.method === "POST") return { id: 20 };
        if (url.includes("/contexts"))
            return {
                items: [{ id: 3, label: "Client A" }],
                page: 1,
                page_size: 25,
                total: 1,
            };
        if (url.includes("/options")) return options;
        if (url.includes("/documents/"))
            return {
                ...document,
                content: "# Existing",
                resources: [],
                credentials: [],
                versions: [],
                attachments: [],
            };
        return workspace;
    });
});

test("the landing page shows Knowledge Base choices without loading folders or articles", async () => {
    render(<KnowledgeBaseWorkspace />);
    expect(
        await screen.findByRole("link", { name: /Client A/ }),
    ).toHaveAttribute(
        "href",
        "/admin/knowledge-base?ownership_type=client&client_id=3",
    );
    expect(
        screen.getByRole("link", { name: "Open Internal Knowledge Base" }),
    ).toHaveAttribute("href", "/admin/knowledge-base?ownership_type=internal");
    expect(screen.queryByText("Folders")).not.toBeInTheDocument();
    expect(
        screen.queryByRole("link", { name: "New document" }),
    ).not.toBeInTheDocument();
    expect(
        mockFetch.mock.calls.every(([url]) => url.includes("/contexts")),
    ).toBe(true);
});

test.each([clientContext, internalContext])(
    "folder creation uses the selected $ownership_type context",
    async (context) => {
        mockFetch.mockImplementation(
            async (url: string, request?: RequestInit) => {
                if (request?.method) return folder;
                if (url.includes("/options"))
                    return {
                        ...options,
                        sections:
                            context.client_id === null
                                ? [internalFolder]
                                : [folder],
                    };
                return {
                    ...workspace,
                    ownership_type: context.ownership_type,
                    client_id: context.client_id,
                    documents: [],
                    sections:
                        context.client_id === null
                            ? [internalFolder]
                            : [folder],
                };
            },
        );
        render(<KnowledgeBaseWorkspace context={context} />);
        await screen.findByRole("link", {
            name:
                context.client_id === null
                    ? "Internal folder"
                    : "Client folder",
        });
        fireEvent.click(screen.getByRole("button", { name: "New folder" }));
        fireEvent.change(screen.getByLabelText("Folder name"), {
            target: { value: "Runbooks" },
        });
        fireEvent.click(screen.getByRole("button", { name: "Create folder" }));
        await waitFor(() =>
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining("/sections"),
                expect.objectContaining({
                    method: "POST",
                    body: expect.stringContaining(
                        `"ownership_type":"${context.ownership_type}"`,
                    ),
                }),
            ),
        );
        const payload = JSON.parse(
            String(
                mockFetch.mock.calls.find(
                    ([, request]) => request?.method === "POST",
                )?.[1]?.body,
            ),
        );
        expect(payload.client_id).toBe(context.client_id);
        expect(screen.queryByText("All ownership")).not.toBeInTheDocument();
        expect(
            screen.getByRole("link", { name: "New document" }),
        ).toHaveAttribute(
            "href",
            `/admin/knowledge-base/documents/new?ownership_type=${context.ownership_type}${context.client_id === null ? "" : "&client_id=3"}`,
        );
    },
);

test("switching Clients immediately discards the previous folder tree and articles", async () => {
    const child = {
        ...folder,
        id: 12,
        name: "Child folder",
        path: "Client folder / Child folder",
        parent_id: 10,
    };
    mockFetch.mockResolvedValue({ ...workspace, sections: [folder, child] });
    const { rerender } = render(
        <KnowledgeBaseWorkspace context={clientContext} sectionId={10} />,
    );
    await screen.findByRole("link", { name: "Child folder" });
    await screen.findByText("Client article");
    mockFetch.mockResolvedValue({
        ...workspace,
        client_id: 4,
        sections: [],
        documents: [],
        total_documents: 0,
    });
    rerender(
        <KnowledgeBaseWorkspace
            context={{ ownership_type: "client", client_id: 4 }}
        />,
    );
    expect(
        screen.queryByRole("link", { name: "Child folder" }),
    ).not.toBeInTheDocument();
    expect(screen.queryByText("Client article")).not.toBeInTheDocument();
    await waitFor(() =>
        expect(
            mockFetch.mock.calls.some(
                ([url]) =>
                    url.includes("/workspace?") && url.includes("client_id=4"),
            ),
        ).toBe(true),
    );
});

test("new article form requires a context before loading any content", () => {
    render(<KnowledgeDocumentForm />);
    expect(
        screen.getByRole("link", { name: "Choose Knowledge Base" }),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText("Title")).not.toBeInTheDocument();
    expect(mockFetch).not.toHaveBeenCalled();
});

test("article creation locks ownership and only offers the selected Client folders", async () => {
    mockFetch.mockImplementation(async (url: string, request?: RequestInit) =>
        request?.method
            ? { id: 20 }
            : url.includes("/options")
              ? { ...options, sections: [folder, internalFolder] }
              : workspace,
    );
    render(
        <KnowledgeDocumentForm
            initialContext={clientContext}
            initialSectionId={10}
        />,
    );
    const title = await screen.findByLabelText("Title");
    expect(screen.getByLabelText("Ownership")).toBeDisabled();
    expect(screen.getByLabelText("Client")).toBeDisabled();
    expect(
        screen.queryByRole("option", { name: "Internal folder" }),
    ).not.toBeInTheDocument();
    fireEvent.change(title, { target: { value: "New article" } });
    fireEvent.click(screen.getByRole("button", { name: "Create document" }));
    await waitFor(() =>
        expect(mockPush).toHaveBeenCalledWith(
            "/admin/knowledge-base/documents/20",
        ),
    );
    expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/documents"),
        expect.objectContaining({
            method: "POST",
            body: expect.stringContaining('"client_id":3'),
        }),
    );
    expect(
        mockFetch.mock.calls
            .filter(([url]) => url.includes("/options"))
            .every(([url]) => url.includes("client_id=3")),
    ).toBe(true);
});

test("editing an article loads options for its existing owner", async () => {
    render(<KnowledgeDocumentForm documentId={20} />);
    expect(await screen.findByLabelText("Title")).toHaveValue("Client article");
    expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/options?ownership_type=client&client_id=3"),
    );
});

test("the direct new-article route redirects to the picker without an explicit context", async () => {
    await expect(
        NewKnowledgeDocumentPage({ searchParams: Promise.resolve({}) }),
    ).rejects.toThrow("Redirect to context picker");
    expect(mockRedirect).toHaveBeenCalled();
});

test("resource documentation links preserve the resolved Client Knowledge Base", async () => {
    render(<KnowledgeBasePanel resourceId={42} />);
    expect(
        await screen.findByRole("link", { name: "Add document" }),
    ).toHaveAttribute(
        "href",
        "/admin/knowledge-base/documents/new?ownership_type=client&client_id=3",
    );
    expect(
        screen.getByRole("link", { name: "Open Knowledge Base" }),
    ).toHaveAttribute(
        "href",
        "/admin/knowledge-base?ownership_type=client&client_id=3&resource_id=42",
    );
});

test.each([
    [undefined, undefined],
    ["client", undefined],
    ["all", "3"],
    ["internal", "3"],
    ["client", "0"],
    ["client", "invalid"],
])(
    "invalid scope %s / %s cannot open a Knowledge Base",
    (ownership, clientId) => {
        expect(parseKnowledgeContext(ownership, clientId)).toBeNull();
    },
);

test("navigating to a different Client's new-article route clears the previous draft", async () => {
    const { rerender } = render(
        await NewKnowledgeDocumentPage({
            searchParams: Promise.resolve({ client_id: "3" }),
        }),
    );
    fireEvent.change(await screen.findByLabelText("Title"), {
        target: { value: "Client A draft" },
    });
    mockFetch.mockResolvedValue({
        ...options,
        clients: [{ id: 4, label: "Client B" }],
        sections: [
            {
                ...folder,
                id: 12,
                name: "B folder",
                path: "B folder",
                client_id: 4,
            },
        ],
    });
    rerender(
        await NewKnowledgeDocumentPage({
            searchParams: Promise.resolve({ client_id: "4" }),
        }),
    );
    expect(await screen.findByLabelText("Title")).toHaveValue("");
    expect(screen.getByLabelText("Client")).toHaveValue("4");
    expect(
        screen.queryByRole("option", { name: "Client folder" }),
    ).not.toBeInTheDocument();
});

test("the file browser shows only immediate folders at the root", async () => {
    const child = {
        ...folder,
        id: 12,
        name: "Nested folder",
        path: "Client folder / Nested folder",
        parent_id: 10,
    };
    mockFetch.mockResolvedValue({
        ...workspace,
        sections: [folder, child],
        documents: [],
        total_documents: 0,
    });
    render(<KnowledgeBaseWorkspace context={clientContext} />);
    expect(
        await screen.findByRole("link", { name: "Client folder" }),
    ).toHaveAttribute(
        "href",
        "/admin/knowledge-base?ownership_type=client&client_id=3&section_id=10",
    );
    expect(
        screen.queryByRole("link", { name: "Nested folder" }),
    ).not.toBeInTheDocument();
    expect(
        screen.getByRole("table", { name: "Folder contents" }),
    ).toBeInTheDocument();
    expect(
        screen.queryByRole("heading", { name: "Folders" }),
    ).not.toBeInTheDocument();
    expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("browse=true"),
    );
});

test("an open folder mixes subfolders and articles and has breadcrumbs and up navigation", async () => {
    const child = {
        ...folder,
        id: 12,
        name: "Nested folder",
        path: "Client folder / Nested folder",
        parent_id: 10,
    };
    mockFetch.mockResolvedValue({ ...workspace, sections: [folder, child] });
    render(<KnowledgeBaseWorkspace context={clientContext} sectionId={10} />);
    await screen.findByRole("link", { name: "Nested folder" });
    expect(
        screen.getByRole("link", { name: "Client article" }),
    ).toHaveAttribute("href", "/admin/knowledge-base/documents/20");
    expect(
        screen.getByRole("navigation", { name: "Folder breadcrumbs" }),
    ).toHaveTextContent("Client AClient folder");
    expect(screen.getByRole("link", { name: "Up one level" })).toHaveAttribute(
        "href",
        "/admin/knowledge-base?ownership_type=client&client_id=3",
    );
    expect(screen.getByRole("link", { name: "New document" })).toHaveAttribute(
        "href",
        "/admin/knowledge-base/documents/new?ownership_type=client&client_id=3&section_id=10",
    );
    fireEvent.click(screen.getByRole("button", { name: "New folder" }));
    fireEvent.change(screen.getByLabelText("Folder name"), {
        target: { value: "New child" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create folder" }));
    await waitFor(() =>
        expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining("/sections"),
            expect.objectContaining({
                method: "POST",
                body: expect.stringContaining('"parent_id":10'),
            }),
        ),
    );
});

test("grid view presents the same folder contents without a separate sidebar", async () => {
    mockFetch.mockResolvedValue(workspace);
    render(<KnowledgeBaseWorkspace context={clientContext} sectionId={10} />);
    await screen.findByRole("link", { name: "Client article" });
    fireEvent.click(screen.getByRole("button", { name: "Grid view" }));
    expect(screen.getByRole("button", { name: "Grid view" })).toHaveAttribute(
        "aria-pressed",
        "true",
    );
    expect(
        screen.queryByRole("table", { name: "Folder contents" }),
    ).not.toBeInTheDocument();
    expect(
        screen.getByRole("link", { name: /Client article/ }),
    ).toBeInTheDocument();
});

test("deep-folder breadcrumbs link back to each ancestor and preserve resource context", async () => {
    const child = {
        ...folder,
        id: 12,
        name: "Nested folder",
        path: "Client folder / Nested folder",
        parent_id: 10,
    };
    mockFetch.mockResolvedValue({
        ...workspace,
        sections: [folder, child],
        documents: [],
        total_documents: 0,
    });
    render(
        <KnowledgeBaseWorkspace
            context={clientContext}
            sectionId={12}
            resourceId={42}
        />,
    );
    expect(
        await screen.findByRole("link", { name: "Client folder" }),
    ).toHaveAttribute(
        "href",
        "/admin/knowledge-base?ownership_type=client&client_id=3&section_id=10&resource_id=42",
    );
    expect(screen.getByRole("link", { name: "Up one level" })).toHaveAttribute(
        "href",
        "/admin/knowledge-base?ownership_type=client&client_id=3&section_id=10&resource_id=42",
    );
});

test("folder search searches descendants and shows their locations", async () => {
    const child = {
        ...folder,
        id: 12,
        name: "Deploy",
        path: "Client folder / Deploy",
        parent_id: 10,
    };
    const sibling = {
        ...folder,
        id: 13,
        name: "Deploy elsewhere",
        path: "Deploy elsewhere",
        parent_id: null,
    };
    mockFetch.mockResolvedValue({
        ...workspace,
        sections: [folder, child, sibling],
        documents: [],
        total_documents: 0,
    });
    render(<KnowledgeBaseWorkspace context={clientContext} sectionId={10} />);
    await screen.findByRole("link", { name: "Deploy" });
    fireEvent.change(screen.getByLabelText("Search Knowledge Base"), {
        target: { value: "Deploy" },
    });
    expect(
        await screen.findByRole("link", {
            name: /Deploy.*Client folder \/ Deploy/,
        }),
    ).toBeInTheDocument();
    expect(
        screen.queryByRole("link", { name: /Deploy elsewhere/ }),
    ).not.toBeInTheDocument();
    await waitFor(() =>
        expect(
            mockFetch.mock.calls.some(
                ([url]) =>
                    url.includes("q=Deploy") &&
                    url.includes("section_id=10") &&
                    url.includes("browse=true"),
            ),
        ).toBe(true),
    );
});

test("reading an article provides a return link to its containing folder", async () => {
    const { KnowledgeDocumentWorkspace } =
        await import("@/app/(admin)/admin/knowledge-base/KnowledgeDocumentWorkspace");
    mockFetch.mockResolvedValue({
        ...document,
        content: "# Existing",
        resources: [],
        credentials: [],
        versions: [],
        attachments: [],
        created_at: "2026-01-01T00:00:00Z",
        created_by_name: null,
        updated_by_name: null,
        is_portal_visible: false,
    });
    render(<KnowledgeDocumentWorkspace documentId={20} />);
    expect(
        await screen.findByRole("link", { name: "Back to folder" }),
    ).toHaveAttribute(
        "href",
        "/admin/knowledge-base?ownership_type=client&client_id=3&section_id=10",
    );
});

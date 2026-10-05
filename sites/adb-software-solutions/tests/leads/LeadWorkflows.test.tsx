import "@testing-library/jest-dom";
import { LeadWorkspace } from "@/app/(admin)/admin/leads/[id]/LeadWorkspace";
import { LeadForm } from "@/app/(admin)/admin/leads/LeadForm";
import { LeadList } from "@/app/(admin)/admin/leads/LeadList";
import { fetchAPI } from "@/lib/api/fetch";
import {
    fireEvent,
    render,
    screen,
    waitFor,
    within,
} from "@testing-library/react";

jest.mock("@/lib/api/fetch", () => ({ fetchAPI: jest.fn() }));
jest.mock("next/navigation", () => ({
    useRouter: () => ({ push: jest.fn(), refresh: jest.fn() }),
}));
jest.mock("@/app/(admin)/admin/leads/LeadEmailPanel", () => ({
    LeadEmailPanel: () => null,
}));
const permission = jest.fn(() => true);
jest.mock("@/contexts/AuthContext", () => ({
    useAuth: () => ({ user: { id: "staff-1" }, hasPermission: permission }),
}));
const api = jest.mocked(fetchAPI);
const options = {
    statuses: [{ id: 1, name: "New" }],
    sources: [{ id: 2, name: "Email" }],
    assignees: [{ id: "staff-1", name: "Adam", email: "adam@example.test" }],
};

beforeEach(() => {
    permission.mockImplementation(() => true);
    api.mockReset();
    api.mockImplementation(async (url, init) => {
        if (url.endsWith("lead-sources") || url.endsWith("lead-statuses"))
            return { id: 3, name: "Custom" };
        if (init?.method === "POST") return { id: 9 };
        return url.endsWith("lead-options") ? options : [];
    });
});

it.each(["source", "stage"])(
    "creates and selects a %s without discarding the lead draft",
    async (kind) => {
        render(<LeadForm onSaved={jest.fn()} onCancel={jest.fn()} />);
        expect(await screen.findByLabelText("Sales stage")).toHaveValue("1");
        fireEvent.change(screen.getByLabelText("Contact name"), {
            target: { value: "Jane" },
        });
        fireEvent.click(screen.getByRole("button", { name: `Add ${kind}` }));
        fireEvent.change(
            screen.getByLabelText(
                kind === "source" ? "Source name" : "Stage name",
            ),
            { target: { value: "Custom" } },
        );
        if (kind === "stage")
            fireEvent.change(screen.getByLabelText("Outcome"), {
                target: { value: "won" },
            });
        fireEvent.click(screen.getByRole("button", { name: "Add and select" }));
        await waitFor(() =>
            expect(
                screen.getByLabelText(
                    kind === "source" ? "Source" : "Sales stage",
                ),
            ).toHaveValue("3"),
        );
        expect(screen.getByLabelText("Contact name")).toHaveValue("Jane");
        const call = api.mock.calls.find(([, init]) => init?.method === "POST");
        expect(JSON.parse(String(call?.[1]?.body))).toEqual(
            kind === "source"
                ? { name: "Custom" }
                : { name: "Custom", outcome: "won" },
        );
    },
);

it("hides catalogue creation controls without their capabilities", async () => {
    permission.mockImplementation(() => false);
    render(<LeadForm />);
    await screen.findByLabelText("Sales stage");
    expect(
        screen.queryByRole("button", { name: "Add source" }),
    ).not.toBeInTheDocument();
    expect(
        screen.queryByRole("button", { name: "Add stage" }),
    ).not.toBeInTheDocument();
});

it("refreshes the list owner immediately after assigning a lead to the current user", async () => {
    let assigned = false;
    const detail = {
        id: 9,
        name: "Jane",
        company: "Example",
        email: "jane@example.test",
        phone: "",
        status_name: null,
        source_name: "Email",
        brand_name: "ADB",
        assigned_to_id: null,
        assigned_to_name: null,
        can_assign: true,
        can_convert: false,
        converted_at: null,
        converted_client_id: null,
        message: "",
        notes: "",
        related_tickets: [],
        created_at: "2026-10-01T00:00:00Z",
        updated_at: "2026-10-01T00:00:00Z",
    };
    api.mockImplementation(async (url, init) => {
        if (init?.method === "POST" && url.endsWith("assignment")) {
            assigned = true;
            return {
                ...detail,
                assigned_to_id: "staff-1",
                assigned_to_name: "Adam",
            };
        }
        if (url.includes("lead-overview"))
            return {
                items: [
                    {
                        ...detail,
                        status: "No sales stage",
                        outcome: "open",
                        source: "Email",
                        brand: "ADB",
                        assigned_to_name: assigned ? "Adam" : null,
                    },
                ],
                stats: {
                    active: 1,
                    mine: assigned ? 1 : 0,
                    unassigned: assigned ? 0 : 1,
                    new_last_30_days: 1,
                },
                page: 1,
                page_size: 25,
                total: 1,
                total_pages: 1,
            };
        if (url.endsWith("lead-options")) return options;
        if (url.endsWith("leads/9")) return detail;
        return [];
    });
    render(<LeadList />);
    fireEvent.click(await screen.findByRole("button", { name: "Example" }));
    fireEvent.click(
        await screen.findByRole("button", { name: "Assign to me" }),
    );
    await waitFor(() =>
        expect(
            within(screen.getByRole("table")).getByText("Adam"),
        ).toBeInTheDocument(),
    );
    expect(
        within(screen.getByRole("table")).getByText("No sales stage"),
    ).toBeInTheDocument();
    expect(
        within(screen.getByRole("table")).queryByText("Unassigned"),
    ).not.toBeInTheDocument();
});

it.each(["won", "lost"])(
    "marks a lead %s directly and notifies the list",
    async (outcome) => {
        const detail = {
            id: 9,
            name: "Jane",
            company: "Example",
            email: "jane@example.test",
            phone: "",
            status_id: 1,
            status_name: "New",
            assigned_to_id: null,
            assigned_to_name: null,
            can_assign: false,
            can_convert: false,
            converted_at: null,
            message: "",
            notes: "",
            related_tickets: [],
            created_at: "2026-10-01T00:00:00Z",
            updated_at: "2026-10-01T00:00:00Z",
        };
        const stage = { id: 3, name: "Closed", outcome };
        api.mockImplementation(async (url, init) => {
            if (init?.method === "POST")
                return { ...detail, status_id: 3, status_name: "Closed" };
            return url.endsWith("lead-options")
                ? { ...options, statuses: [...options.statuses, stage] }
                : detail;
        });
        const changed = jest.fn();
        render(<LeadWorkspace leadId={9} onChanged={changed} />);
        fireEvent.click(
            await screen.findByRole("button", { name: `Mark as ${outcome}` }),
        );
        await waitFor(() => expect(changed).toHaveBeenCalled());
        expect(screen.getByLabelText("Sales stage")).toHaveValue("3");
        const call = api.mock.calls.find(([, init]) => init?.method === "POST");
        expect(call?.[0]).toContain("leads/9/stage");
        expect(JSON.parse(String(call?.[1]?.body))).toEqual({ status_id: 3 });
    },
);

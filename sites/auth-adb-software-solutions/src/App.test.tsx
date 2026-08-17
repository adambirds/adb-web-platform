import {render, waitFor} from "@testing-library/react";
import {BrowserRouter} from "react-router-dom";
import {describe, expect, it, vi} from "vitest";

const getCurrentUser = vi.fn().mockResolvedValue({
    success: true,
    user: null,
});
const ensureCsrfToken = vi.fn().mockResolvedValue(undefined);

vi.mock("@/utils/api", async (importOriginal) => {
    const actual = await importOriginal<typeof import("@/utils/api")>();

    return {
        ...actual,
        authApi: {
            ...actual.authApi,
            getCurrentUser,
        },
        ensureCsrfToken,
    };
});

import App from "./App";

async function renderApp() {
    const result = render(
        <BrowserRouter>
            <App />
        </BrowserRouter>,
    );

    await waitFor(() => {
        expect(getCurrentUser).toHaveBeenCalled();
        expect(ensureCsrfToken).toHaveBeenCalled();
    });

    return result;
}

describe("App", () => {
    it("renders without crashing", async () => {
        const {container} = await renderApp();
        expect(container).toBeTruthy();
    });

    it("has valid document structure", async () => {
        const {container} = await renderApp();
        expect(container.firstChild).toBeTruthy();
    });
});

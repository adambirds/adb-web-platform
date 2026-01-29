import {render} from "@testing-library/react";
import {BrowserRouter} from "react-router-dom";
import {describe, expect, it} from "vitest";
import App from "./App";

describe("App", () => {
    it("renders without crashing", () => {
        const {container} = render(
            <BrowserRouter>
                <App />
            </BrowserRouter>,
        );
        expect(container).toBeTruthy();
    });

    it("has valid document structure", () => {
        const {container} = render(
            <BrowserRouter>
                <App />
            </BrowserRouter>,
        );
        expect(container.firstChild).toBeTruthy();
    });
});

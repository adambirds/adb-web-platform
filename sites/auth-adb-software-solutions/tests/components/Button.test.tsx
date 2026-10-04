import {render, screen} from "@testing-library/react";
import {describe, expect, it} from "vitest";

describe("Button component tests", () => {
    it("should render a button element", () => {
        render(<button>Click me</button>);
        const button = screen.getByText("Click me");
        expect(button).toBeInTheDocument();
    });

    it("should have correct text content", () => {
        render(<button>Submit</button>);
        expect(screen.getByText("Submit")).toBeInTheDocument();
    });

    it("should be disabled when disabled prop is set", () => {
        render(<button disabled>Disabled</button>);
        const button = screen.getByText("Disabled");
        expect(button).toBeDisabled();
    });
});

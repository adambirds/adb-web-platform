import "@testing-library/jest-dom/vitest";

// jsdom has no layout observer. Browser validation exercises the real chart sizes.
class TestResizeObserver implements ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
}
globalThis.ResizeObserver = TestResizeObserver;

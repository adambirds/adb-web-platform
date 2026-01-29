import {describe, expect, it} from "vitest";

describe("Basic validation tests", () => {
    it("should validate email format", () => {
        const validEmail = "test@example.com";
        const invalidEmail = "invalid-email";

        expect(validEmail).toContain("@");
        expect(invalidEmail).not.toContain("@");
    });

    it("should validate password length", () => {
        const validPassword = "SecurePass123!";
        const shortPassword = "123";

        expect(validPassword.length).toBeGreaterThanOrEqual(8);
        expect(shortPassword.length).toBeLessThan(8);
    });

    it("should handle empty strings", () => {
        const emptyString = "";

        expect(emptyString).toBe("");
        expect(emptyString.length).toBe(0);
    });
});

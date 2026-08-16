import typescriptPlugin from "@typescript-eslint/eslint-plugin";
import typescriptParser from "@typescript-eslint/parser";
import reactPlugin from "eslint-plugin-react";
import reactHooksPlugin from "eslint-plugin-react-hooks";
import reactRefreshPlugin from "eslint-plugin-react-refresh";
import globals from "globals";
import path from "path";
import {fileURLToPath} from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default [
    {
        ignores: [
            "dist/**",
            "node_modules/**",
            "stylelint.config.js",
            "*.config.js",
        ],
    },
    {
        languageOptions: {
            globals: {
                ...globals.browser,
                ...globals.es2020,
            },
            parser: typescriptParser,
            ecmaVersion: 5,
            sourceType: "module",
            parserOptions: {
                project: ["./tsconfig.json", "./tsconfig.node.json"],
                tsconfigRootDir: __dirname,
            },
        },
        files: ["**/*.ts", "**/*.tsx"],
        plugins: {
            "@typescript-eslint": typescriptPlugin,
            react: reactPlugin,
            "react-hooks": reactHooksPlugin,
            "react-refresh": reactRefreshPlugin,
        },
        settings: {
            react: {
                version: "detect",
            },
        },
        rules: {
            // TypeScript rules
            "@typescript-eslint/no-var-requires": "off",
            "@typescript-eslint/no-explicit-any": "off",
            "@typescript-eslint/no-empty-function": "off",
            "@typescript-eslint/no-empty-interface": "off",
            "@typescript-eslint/prefer-for-of": "off",
            "@typescript-eslint/no-unused-vars": [
                "warn",
                {
                    args: "none",
                    ignoreRestSiblings: true,
                },
            ],
            // React rules
            "react/prop-types": "off",
            // React Refresh rules
            "react-refresh/only-export-components": [
                "warn",
                {allowConstantExport: true},
            ],
            // React Hooks rules
            "react-hooks/exhaustive-deps": "warn",
            // General rules
            "no-unused-vars": "off",
        },
    },
];

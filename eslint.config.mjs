import globals from "globals";
import babelParser from "@babel/eslint-parser";

export default [{
    languageOptions: {
        globals: {
            ...globals.node,
        },

        parser: babelParser,
        ecmaVersion: 5,
        sourceType: "commonjs",

        parserOptions: {
            requireConfigFile: false,
        },
    },

    rules: {
        "no-html-link-for-pages": 0,
        "@next/next/no-html-link-for-pages": "off",
    },
    ignores: [
        "node_modules",
        "venv",
        "prettier.config.js",
        "stylelint.config.js",
    ],
    files: [
        "**/*.ts",
        "**/*.tsx",
        "**/*.js",
        "**/*.jsx",
    ]
}];
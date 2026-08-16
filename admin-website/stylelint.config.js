"use strict";

module.exports = {
    extends: ["stylelint-config-standard", "stylelint-config-tailwindcss"],
    plugins: ["stylelint-order"],
    rules: {
        "at-rule-no-unknown": [
            true,
            {
                ignoreAtRules: [
                    "tailwind",
                    "extend",
                    "define-mixin",
                    "mixin",
                    "theme",
                    "source",
                    "plugin",
                    "custom-variant",
                    "utility",
                ],
            },
        ],
        "font-family-no-missing-generic-family-keyword": [
            true,
            {
                ignoreFontFamilies: ["FontAwesome"],
            },
        ],
        "function-no-unknown": [
            true,
            {
                ignoreFunctions: ["theme"],
            },
        ],
        "no-invalid-position-at-import-rule": null,
        "custom-property-pattern": null,
        "no-descending-specificity": null,
        "comment-empty-line-before": null,
        "declaration-empty-line-before": null,
        "keyframes-name-pattern": null,
        "selector-class-pattern": null,
        "selector-id-pattern": null,
        "import-notation": null,
        "alpha-value-notation": "number",
        "color-function-notation": "modern",
        "hue-degree-notation": "number",
        "declaration-property-value-disallowed-list": {
            "/^(border(-top|-right|-bottom|-left)?|outline)(-width)?$/": [
                /\b(thin|medium|thick)\b/,
            ],
        },
        "function-disallowed-list": [],
        "function-url-no-scheme-relative": true,
        "function-url-scheme-allowed-list": ["data"],
    },
    ignoreFiles: ["dist/**", "node_modules/**"],
};

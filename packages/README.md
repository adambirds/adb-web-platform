# Shared TypeScript packages

These packages hold genuinely shared contracts and primitives. Brand-specific
pages, layouts and visual identity belong in their applications.

| Package                                   | Entry point and purpose                            |
| ----------------------------------------- | -------------------------------------------------- |
| [api-client](./api-client/)               | `src/index.ts`: shared API transport and contracts |
| [ui](./ui/)                               | `src/index.ts`: brand-neutral UI exports and types |
| [eslint-config](./eslint-config/)         | Shared frontend lint configuration                 |
| [typescript-config](./typescript-config/) | Shared TypeScript configuration                    |

Each package's `package.json` defines its exports and scripts. Application
consumers live in [sites](../sites/README.md); business rules remain in the
[Django backend](../backend/README.md).

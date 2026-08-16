# AGENTS.md

Scoped guidance for `packages/`.

- Put code here only when it is genuinely shared by two or more applications or is deliberately defined as a cross-application contract.
- Do not move brand-specific layouts, copy, navigation or styling into shared packages merely to reduce file count.
- Keep package APIs small, typed and documented.
- Avoid circular dependencies between packages and applications.
- `ui` should remain brand-neutral; individual sites own their visual identity.
- `api-client` should contain shared transport/contracts, not page-specific data-fetching logic.
- Follow the root `AGENTS.md` and `CONTRIBUTING.md` branch, commit and validation rules.

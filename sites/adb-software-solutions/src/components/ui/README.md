# Admin UI primitives

This directory is the local UI library for the ADB Business Platform operations console.

The admin application is deliberately **dark-only**. Do not add theme toggles, light-mode variants or page-specific light surfaces. Public ADB websites may have their own design systems; these primitives are specifically for the internal operations application.

## Principles

- Reuse these primitives before writing one-off cards, page headers, inputs, tables or empty states.
- Keep information density appropriate for an internal CRM/helpdesk/operations tool rather than a marketing site.
- Prefer slate neutral surfaces with ADB cyan used as a focused accent rather than covering whole interfaces in brand colour.
- Keep spacing compact and predictable.
- Backend permissions remain authoritative. UI visibility is only a usability layer.
- Add a new primitive when the same visual/interaction pattern appears in multiple admin features; do not turn one-off page composition into a generic abstraction prematurely.

## Existing primitives

- `Badge` — compact statuses and categorical labels.
- `Button` / `ButtonLink` — primary and secondary actions.
- `Card` — bordered operational panel surface, with header/content/footer helpers.
- `Container` — consistent workspace width and horizontal padding.
- `EmptyState` — empty collection/message treatment.
- `Input`, `Select`, `Textarea` — standard form controls.
- `PageHeader` — page title, operational context and actions.
- `SectionHeader` — subsection title/action row.
- `StatCard` — dashboard/summary KPI.
- `Table` — standard tabular surface.

## Layout components

Application-level navigation lives in `../layout/` rather than this directory:

- `AdminLayout` — authenticated full-height operations shell.
- `Sidebar` — grouped, permission-aware navigation.
- `TopBar` — collapse control, global-search affordance, notifications and account menu.

## Adding a primitive

1. Check whether an existing primitive can be composed instead.
2. Keep the API small and strongly typed.
3. Make dark styling the normal/default styling rather than a `dark:` override of a light component.
4. Export reusable primitives from `index.ts`.
5. Add component tests when the primitive includes behaviour rather than presentation alone.

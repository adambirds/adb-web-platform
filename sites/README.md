# Browser applications

| Application                                                     | Navigation                                                           |
| --------------------------------------------------------------- | -------------------------------------------------------------------- |
| [ADB Software Solutions](adb-software-solutions/README.md)      | Public routes in `src/app/`; operations in `src/app/(admin)/admin/`  |
| [Authentication/account](auth-adb-software-solutions/README.md) | Dedicated identity and account-security UI; Vitest suite in `tests/` |
| [ADB Web Designs](./adb-web-designs/)                           | Public App Router routes in `src/app/`                               |
| [ADB Technology](./adb-technology/)                             | Public App Router routes in `src/app/`                               |

Each application owns its `package.json`, Next.js configuration and visual
identity. Start applications with the root `pnpm dev:*` scripts. Use
`pnpm --dir sites/<application> <script>` for an application's scripts.

The Software Solutions public site and `/admin` workspace share one deployable
application. Its route-group layout separates operations from public pages.
Django enforces authentication, business permissions and object scope; account
security workflows belong in the dedicated authentication application.

See [shared packages](../packages/README.md), the
[backend code map](../backend/README.md) and
[canonical platform docs](../docs/README.md) for cross-application boundaries.

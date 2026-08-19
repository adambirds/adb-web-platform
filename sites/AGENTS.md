# AGENTS.md

Scoped guidance for `sites/`.

- `adb-software-solutions/` is a combined Next.js application: public ADB Software Solutions routes plus the authenticated internal operations workspace under `/admin`.
- `adb-web-designs/` and `adb-technology/` are public marketing/content applications.
- `auth-adb-software-solutions/` is the dedicated authentication/account-security application.
- Do not move privileged `/admin` workflows into the other public sites or duplicate authentication/security flows across applications.
- Use Next.js App Router and TypeScript. Public brand sites use Tailwind CSS and should prefer Server Components by default.
- ADB Software Solutions, ADB Web Designs and ADB Technology are separate brands. Do not make them recoloured copies of a single page template.
- Share genuinely reusable primitives through `packages/`, while keeping brand messaging, page composition, navigation, imagery and visual identity local to each site.
- Public forms should call the shared Django backend and identify the originating Brand/source; contact enquiries should continue through the unified Lead/Ticket communication pipeline.
- Build accessible, performant public pages with deliberate metadata, structured data and migration-safe URLs.
- Internal `/admin` screens should follow the scoped guidance in `sites/adb-software-solutions/AGENTS.md`.
- Follow the root `AGENTS.md` and `CONTRIBUTING.md` branch, commit and validation rules.

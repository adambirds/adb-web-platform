# AGENTS.md

Scoped guidance for `sites/`.

- These applications are public marketing/content websites. They must not contain privileged internal admin functionality.
- Use Next.js App Router, TypeScript and Tailwind CSS. Prefer Server Components by default.
- ADB Software Solutions and ADB Web Designs are separate brands. Do not make them recoloured copies of a single page template.
- Share genuinely reusable primitives through `packages/`, while keeping brand messaging, page composition, navigation, imagery and visual identity local to each site.
- Public forms should call the shared Django backend and identify the originating brand/source.
- Build accessible, performant pages with deliberate metadata, structured data and migration-safe URLs.
- Follow the root `AGENTS.md` and `CONTRIBUTING.md` branch, commit and validation rules.

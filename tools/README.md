# Repository tooling

Run tools from the repository root in the configured development environment.

| Tool                                  | Purpose                                              |
| ------------------------------------- | ---------------------------------------------------- |
| `tools/setup` / `tools/setup-project` | Development environment setup                        |
| `tools/lint`                          | Repository formatting, lint and type checks          |
| `tools/run-mypy`                      | Backend static typing                                |
| `tools/test-backend [labels/options]` | Django suite with test settings                      |
| `tools/test-auth-frontend`            | Authentication Vitest suite with coverage            |
| `tools/test-all`                      | Backend and browser application test orchestration   |
| `tools/check-templates`               | Template checks                                      |
| `tools/commit-message-lint`           | Repository commit-message validation                 |
| `tools/update-locked-requirements`    | Generate Python requirement locks from `.in` sources |
| `tools/update-ci-files.py`            | CI configuration generation                          |
| `tools/update-devcontainer-ports.py`  | Devcontainer port configuration generation           |
| `tools/update-tasks-json.py`          | Editor task configuration generation                 |
| `tools/lib/`                          | Shared tooling implementation and custom lint rules  |

`tools/test-website` still targets the historical `website/` path. For current
sites, use `pnpm --dir sites/<application> test --passWithNoTests` or
`tools/test-all`.

Stage intended new files before linting: `tools/lint` discovers files through
Git. Do not hand-edit generated requirement locks; see
[backend requirements](../backend/requirements/README.md).
See [contributing](../CONTRIBUTING.md) for the complete working conventions.

## WordPress migration commands

Run `python backend/manage.py export_wordpress_content` before cutover and
`python backend/manage.py import_wordpress_content` afterwards. The complete
[archive guide](../docs/migrations/README.md) covers the versioned JSON, embedded
original images, offline restoration and draft review. The exporter is read-only;
the importer never publishes or overwrites existing editorial records.

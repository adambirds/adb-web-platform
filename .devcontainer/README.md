# ADB development container

Open the repository in VS Code and choose **Dev Containers: Reopen in Container**.
Docker and the VS Code Dev Containers extension must be installed on the host.
Post-create installs workspace dependencies, prepares the Python environment and
runs Django migrations. Compose starts PostgreSQL and the Redis services.
Application servers and Celery are started explicitly using the tasks below.

## Starting applications

Choose **Tasks: Run Task → Start Analytics Stack** to start Django, the shared
account application, Analytics, all Celery workers and Celery Beat in separate
terminals. The general worker processes analytics synchronization; Beat schedules
refreshes. **Start Full Stack** also starts the three public brand applications.
Stop the compound task's running terminals when finished. Run one compound stack
at a time, since both use the same servers and workers.

| Application                       | Command from `/workspace`                 | Local URL               |
| --------------------------------- | ----------------------------------------- | ----------------------- |
| Django API                        | `start-backend`                           | <http://localhost:8000> |
| Software Solutions and operations | `pnpm dev:software-solutions`             | <http://localhost:3000> |
| Web Designs                       | `pnpm dev:web-designs`                    | <http://localhost:3002> |
| Technology                        | `pnpm dev:technology`                     | <http://localhost:3003> |
| Authentication/accounts           | `pnpm dev:auth`                           | <http://localhost:3004> |
| Analytics                         | `pnpm dev:analytics` or `start-analytics` | <http://localhost:3005> |

For a minimal Analytics setup from individual terminals, run `start-backend`,
`pnpm dev:auth`, `pnpm dev:analytics`, `start-celery-general` and
`start-celery-beat`. Each command remains running. All application ports and
PostgreSQL port 5432 are forwarded by the devcontainer.

## Environment and Google setup

Post-create copies `.env.example` to `.devcontainer/.env` when it does not exist.
For an existing container, add missing variables from the example without
replacing your secrets, then rebuild the container to load them through Compose.
Keep `NODE_ENV` blank for normal Next.js mode selection.

Analytics uses `ANALYTICS_FRONTEND_URL` and `NEXT_PUBLIC_ANALYTICS_URL` pointing to
`http://localhost:3005`. Google integration requires
`ANALYTICS_GOOGLE_CLIENT_ID`, `ANALYTICS_GOOGLE_CLIENT_SECRET`, and the registered
callback `ANALYTICS_GOOGLE_REDIRECT_URI`:
`http://localhost:8000/api/analytics/oauth/callback`.
Follow the [Analytics setup guide](../docs/ANALYTICS_PLATFORM.md) for APIs,
consent scopes, property permissions and verification against real Google data.
Create a local account with `python backend/manage.py createsuperuser`; there is
no default administrator password.

## Tests and debugging

- **Test Analytics** runs the Analytics frontend suite; CLI: `test-analytics`.
- Backend Analytics tests: `cd backend && DJANGO_SETTINGS_MODULE=adbsoftwaresolutions.settings_test python manage.py test apps.analytics`.
- **Test All** runs the repository test runner. **Lint Code** and **Lint and Fix Code** use `tools/lint`.
- **Django: Debug** launches Django under the debugger. Stop the existing backend first.
- **Django: Test** discovers tests from `backend/` using isolated test settings.

Rebuild after changing the Dockerfile or adding helper scripts, since scripts
are installed into `/usr/local/bin` during image build. Before rebuilding, the
new helpers can also be run as `bash .devcontainer/scripts/start-analytics` and
`bash .devcontainer/scripts/test-analytics`.

See the [main setup guide](../README.md#setup-and-configuration) for the complete
environment inventory, optional ClamAV, database services and deployment setup.
Production uses the application Dockerfiles rather than this development image.

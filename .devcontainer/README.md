# Devcontainer Setup

This directory contains the devcontainer configuration for the project template monorepo. The devcontainer provides a complete development environment with all necessary tools and services.

## 🚀 Getting Started

### Prerequisites

- [Visual Studio Code](https://code.visualstudio.com/)
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- [Docker Desktop](https://www.docker.com/products/docker-desktop)

### Quick Start

1. Open the project in VS Code
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
3. Type "Dev Containers: Reopen in Container"
4. Wait for the container to build and start

The devcontainer will automatically:

- Set up the Python environment with all dependencies
- Start PostgreSQL, Redis, and other necessary services
- Run Django migrations
- Configure VS Code with extensions and settings

## 📁 Project Structure

```
project-template/
├── .devcontainer/          # Devcontainer configuration
├── .git/                   # Git repository
├── .gitignore              # Root gitignore
├── backend/                # Django backend
│   ├── apps/
│   ├── authentication/     # Auth app (reusable)
│   ├── app/                # Django settings module
│   └── ...
├── website/                # Website/Frontend (Next.js)
│   ├── src/
│   └── package.json
├── auth-frontend/          # Auth frontend (Vite/React)
│   ├── src/
│   └── package.json
├── tools/                  # Development scripts and tools
```

## 🛠️ Development Tools

### Available Commands

The devcontainer includes several helper scripts:

```bash
# Backend Development
start-backend          # Start Django development server

# Frontend Development
start-website          # Start Next.js website/frontend (port 3000)

# Code Quality & Dependencies
lint                  # Run project linting checks (tools/lint)
lint-fix              # Run linting with auto-fix (tools/lint --fix)
update-requirements   # Update pip-tools locked requirements

# Testing
test-backend          # Run Django tests
test-website          # Run Next.js website tests
test-all              # Run all tests (backend + frontend)
```

**Linting Tools Installation:**

- The devcontainer uses your existing `tools/setup/install-shellcheck` and `tools/setup/install-shfmt` scripts
- This ensures consistency with your local development environment
- All linting tools are installed with the exact versions you've specified

### VS Code Tasks

Use `Ctrl+Shift+P` → "Tasks: Run Task" to access:

**Backend Services:**

- **Start Backend** - Django development server

**Frontend Services:**

- **Start Website (Next.js)** - Marketing website (port 3000)

**Development Tasks:**

- **Lint Code** - Run project linting checks
- **Lint and Fix Code** - Run linting with auto-fix
- **Update Requirements** - Update pip-tools locked requirements
- **Run Tests** - Execute Django test suite
- **Test All** - Run all tests (backend + all frontends)
- **Test Website** - Run Next.js website tests
- **Django Shell** - Interactive Django shell

**Composite Tasks:**

- **Start Full Stack** - Start everything (backend + frontend)

### Debugging

Pre-configured debug configurations:

- **Django: Debug** - Debug Django application
- **Django: Test** - Debug Django test

## 🌐 Service URLs

When the devcontainer is running, access these services:

| Service           | URL                          | Description                   |
| ----------------- | ---------------------------- | ----------------------------- |
| Django Backend    | http://localhost:8000        | Main API and admin            |
| Django Admin      | http://localhost:8000/admin/ | Admin interface (admin/admin) |
| Website (Next.js) | http://localhost:3000        | website / Frontend            |

## 🗄️ Database

- **Host**: localhost
- **Port**: 5432
- **Database**: app_dev
- **Username**: app
- **Password**: app_dev_password

## 📦 Environment Variables

The devcontainer uses environment variables defined in:

- `.devcontainer/.env` - Devcontainer-specific environment variables (not committed to git)

**Setting up Environment Variables:**

1. Copy the example file: `cp .devcontainer/.env.example .devcontainer/.env`
2. Edit `.devcontainer/.env` with your actual credentials and API keys
3. The `.env` file is gitignored and will not be committed

**Required Configuration:**

- Update `SECRET_KEY` with a secure random string

**Security Note:** Never commit the `.env` file - it contains sensitive credentials.

## 🛡️ Optional local ClamAV

Malware scanning is disabled by default, so the normal devcontainer does not start ClamAV. The optional scanner uses the multi-architecture Debian ClamAV image so it can run on both x86-64 and ARM64 development hosts.

To run ClamAV as part of the devcontainer, set these values in `.devcontainer/.env` before rebuilding or reopening the container:

```env
COMPOSE_PROFILES=malware-scanning
TICKETING_MALWARE_SCANNING_ENABLED=1
TICKETING_CLAMAV_HOST=clamav
TICKETING_CLAMAV_PORT=3310
```

Leave `COMPOSE_PROFILES` empty and `TICKETING_MALWARE_SCANNING_ENABLED=0` for the normal scanner-free development environment. A remote or central ClamAV service can instead be used by enabling malware scanning and setting `TICKETING_CLAMAV_HOST` to that private service hostname.

## 🔧 Customization

### Adding Extensions

Edit `.devcontainer/devcontainer.json` to add VS Code extensions:

```json
"extensions": [
  "your.extension.id"
]
```

### Modifying Services

Edit `.devcontainer/docker-compose.yml` to add or modify services.

### Post-Create Scripts

Modify `.devcontainer/post-create.sh` to add custom setup steps.

## 🐛 Troubleshooting

### Container Won't Start

1. Ensure Docker Desktop is running
2. Check Docker Desktop has sufficient resources allocated
3. Try rebuilding: `Ctrl+Shift+P` → "Dev Containers: Rebuild Container"

### Database Connection Issues

1. Wait for database to be ready (check Docker logs)
2. Check environment variables in `.devcontainer/.env`

### Environment Variable Issues

1. Ensure `.devcontainer/.env` file exists (copy from `.env.example`)
2. Verify all required variables are set with actual values
3. Check for typos in variable names
4. Restart devcontainer after changing environment variables

### Python Import Issues

1. Ensure you're using the correct Python interpreter: `/opt/venv/bin/python`
2. Check if dependencies are installed: `pip list`
3. Rebuild container if packages are missing

## 🤝 Contributing

When working on the project:

1. Always work within the devcontainer
2. Use the provided VS Code tasks for common operations
3. Commit and push changes normally - Git works from within the container
4. Use the debug configurations for troubleshooting

## 📝 Notes

- The devcontainer is configured for development only
- Production deployments should use the existing Dockerfile setup
- All development data is persisted in Docker volumes

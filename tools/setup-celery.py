#!/usr/bin/env python3
"""
Celery setup script for project template.

This script configures Celery with user-specified queue names,
creates necessary files and scripts for development and production.
"""

import argparse
import os
import sys
from pathlib import Path


def create_celery_py(backend_dir: Path, app_name: str, python_name: str) -> None:
    """Create celery.py file in the backend app directory."""
    celery_file = backend_dir / python_name / "celery.py"
    
    content = f"""import logging
import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

from {python_name}.bootsteps import LivenessProbe

# Setting the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{python_name}.settings")

app = Celery("{app_name}")
app.steps["worker"].add(LivenessProbe)

# Configuring Celery with settings from the Django settings.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Define the Celery beat schedule if any.
app.conf.beat_schedule = {{
    
}}
app.conf.timezone = "UTC"

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
"""
    
    celery_file.write_text(content)
    print(f"  ✓ Created {celery_file.relative_to(backend_dir.parent)}")


def create_bootsteps_py(backend_dir: Path, python_name: str) -> None:
    """Create bootsteps.py file in the backend app directory."""
    bootsteps_file = backend_dir / python_name / "bootsteps.py"
    
    content = """# bootsteps.py
from __future__ import annotations

from pathlib import Path
from typing import Any

from celery import bootsteps
from celery.worker import WorkController

HEARTBEAT_FILE = Path("/tmp/celery_worker_heartbeat")


class LivenessProbe(bootsteps.StartStopStep):
    requires = {"celery.worker.components:Timer"}

    tref: Any  # TimerReference, but no stable public type

    def __init__(self, parent: WorkController, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self.tref = None

    def start(self, worker: WorkController) -> None:
        self.tref = worker.timer.call_repeatedly(
            1.0,
            self.update_heartbeat_file,
            (worker,),
            priority=10,
        )

    def stop(self, worker: WorkController) -> None:
        HEARTBEAT_FILE.unlink(missing_ok=True)

    def update_heartbeat_file(self, worker: WorkController) -> None:
        HEARTBEAT_FILE.touch()
"""
    
    bootsteps_file.write_text(content)
    print(f"  ✓ Created {bootsteps_file.relative_to(backend_dir.parent)}")


def create_devcontainer_scripts(scripts_dir: Path, python_name: str, queues: list[str]) -> None:
    """Create devcontainer scripts for Celery workers, beat, and flower."""
    # Celery beat script
    beat_script = scripts_dir / "start-celery-beat"
    beat_content = f"""#!/bin/bash
# Start Celery beat scheduler
set -e

cd /workspace/backend
source /opt/venv/bin/activate

echo "⏰ Starting Celery beat..."
celery -A {python_name} beat -l info
"""
    beat_script.write_text(beat_content)
    beat_script.chmod(0o755)
    print(f"  ✓ Created {beat_script.relative_to(scripts_dir.parent.parent)}")
    
    # Individual queue scripts
    for queue in queues:
        queue_script = scripts_dir / f"start-celery-{queue}"
        queue_content = f"""#!/bin/bash
# Start Celery worker for {queue} queue
set -e

cd /workspace/backend
source /opt/venv/bin/activate

echo "🔄 Starting Celery worker for {queue} queue..."
celery -A {python_name} worker -Q {queue} -l info --concurrency=1 --hostname={queue}@%h
"""
        queue_script.write_text(queue_content)
        queue_script.chmod(0o755)
        print(f"  ✓ Created {queue_script.relative_to(scripts_dir.parent.parent)}")
    
    # Multi-worker script
    multi_script = scripts_dir / "start-celery-multi"
    multi_content = f"""#!/bin/bash
# Start multiple Celery workers with different queues (1 worker per queue for dev)
set -e

cd /workspace/backend
source /opt/venv/bin/activate

echo "🔄 Starting Celery workers with different queues (dev setup - 1 worker per queue)..."

"""
    
    for queue in queues:
        multi_content += f"""echo "Starting {queue} queue worker..."
celery -A {python_name} worker -Q {queue} -l info --concurrency=1 --hostname={queue}@%h &

"""
    
    multi_content += """echo "✅ All Celery workers started (1 per queue)"

# Wait for all background processes
wait
"""
    
    multi_script.write_text(multi_content)
    multi_script.chmod(0o755)
    print(f"  ✓ Created {multi_script.relative_to(scripts_dir.parent.parent)}")
    
    # Flower script
    flower_script = scripts_dir / "start-flower"
    flower_content = f"""#!/bin/bash
# Start Flower (Celery monitoring)
set -e

cd /workspace/backend
source /opt/venv/bin/activate

echo "🌸 Starting Flower..."
celery -A {python_name} flower --port=5555 --address=0.0.0.0
"""
    flower_script.write_text(flower_content)
    flower_script.chmod(0o755)
    print(f"  ✓ Created {flower_script.relative_to(scripts_dir.parent.parent)}")


def create_entrypoint_scripts(project_root: Path, python_name: str) -> None:
    """Create entrypoint scripts for Docker containers."""
    # Celery worker entrypoint
    worker_entrypoint = project_root / "entrypoint-celery-worker.sh"
    worker_content = f"""#!/bin/sh
set -e

QUEUE_NAME=${{CELERY_QUEUE:-default}}
CONCURRENCY=${{CELERY_CONCURRENCY:-2}}
WORKER_NAME="worker_${{QUEUE_NAME}}@$(hostname)"

exec celery -A {python_name} worker \\
\t-Q "$QUEUE_NAME" \\
\t-n "$WORKER_NAME" \\
\t-c "$CONCURRENCY" \\
\t-l INFO
"""
    worker_entrypoint.write_text(worker_content)
    worker_entrypoint.chmod(0o755)
    print(f"  ✓ Created {worker_entrypoint.name}")
    
    # Flower entrypoint
    flower_entrypoint = project_root / "entrypoint-flower.sh"
    flower_content = f"""#!/bin/sh
exec celery -A {python_name} \\
\t--broker="$CELERY_BROKER" \\
\tflower \\
\t--loglevel=info \\
\t--address=0.0.0.0 \\
\t--port=5555 \\
\t--broker_use_ssl=true \\
\t--auth_provider="flower.views.auth.GithubLoginHandler" \\
\t--auth="$FLOWER_AUTH" \\
\t--oauth2_key="$FLOWER_OAUTH2_KEY" \\
\t--oauth2_secret="$FLOWER_OAUTH2_SECRET" \\
\t--oauth2_redirect_uri="$FLOWER_OAUTH2_REDIRECT_URI"
"""
    flower_entrypoint.write_text(flower_content)
    flower_entrypoint.chmod(0o755)
    print(f"  ✓ Created {flower_entrypoint.name}")


def create_dockerfiles(project_root: Path, python_name: str, slug_name: str) -> None:
    """Create Dockerfiles for Celery services."""
    # Dockerfile.celery-worker
    worker_dockerfile = project_root / "Dockerfile.celery-worker"
    worker_content = f"""# Use official Python base image with slimmed down Debian base
FROM python:3.12-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PIP_DISABLE_PIP_VERSION_CHECK=1 \\
    LANG=C.UTF-8

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    libpq-dev \\
    gcc \\
    curl \\
    libffi-dev \\
    libxml2-dev \\
    libxslt1-dev \\
    libjpeg-dev \\
    zlib1g-dev \\
    libcairo2 \\
    libcairo2-dev \\
    fontconfig \\
    # WeasyPrint dependencies for PDF generation
    libpango-1.0-0 \\
    libpangocairo-1.0-0 \\
    libgdk-pixbuf-2.0-0 \\
    shared-mime-info \\
    && apt-get clean \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements/prod.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set working directory
WORKDIR /opt/{slug_name}

# Copy project code (backend directory contents)
COPY ./backend/ .

# Copy health check scripts into the image
COPY docker/healthchecks/celery_*.py /opt/healthchecks/

COPY ./entrypoint-celery-worker.sh /entrypoint-celery-worker.sh
RUN chmod +x /entrypoint-celery-worker.sh

ENTRYPOINT [ "/entrypoint-celery-worker.sh" ]
"""
    worker_dockerfile.write_text(worker_content)
    print(f"  ✓ Created {worker_dockerfile.name}")
    
    # Dockerfile.celery-beat
    beat_dockerfile = project_root / "Dockerfile.celery-beat"
    beat_content = f"""# Use official Python base image with slimmed down Debian base
FROM python:3.12-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PIP_DISABLE_PIP_VERSION_CHECK=1 \\
    LANG=C.UTF-8

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    libpq-dev \\
    gcc \\
    curl \\
    libffi-dev \\
    libxml2-dev \\
    libxslt1-dev \\
    libjpeg-dev \\
    zlib1g-dev \\
    libcairo2 \\
    libcairo2-dev \\
    fontconfig \\
    procps \\
    # WeasyPrint dependencies for PDF generation
    libpango-1.0-0 \\
    libpangocairo-1.0-0 \\
    libgdk-pixbuf-2.0-0 \\
    shared-mime-info \\
    && apt-get clean \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements/prod.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set working directory
WORKDIR /opt/{slug_name}

# Copy project code (backend directory contents)
COPY ./backend/ .

CMD ["celery", "-A", "{python_name}", "beat", "-l", "INFO"]
"""
    beat_dockerfile.write_text(beat_content)
    print(f"  ✓ Created {beat_dockerfile.name}")
    
    # Dockerfile.flower
    flower_dockerfile = project_root / "Dockerfile.flower"
    flower_content = f"""# Use official Python base image with slimmed down Debian base
FROM python:3.12-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PIP_DISABLE_PIP_VERSION_CHECK=1 \\
    LANG=C.UTF-8

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    libpq-dev \\
    gcc \\
    curl \\
    libffi-dev \\
    libxml2-dev \\
    libxslt1-dev \\
    libjpeg-dev \\
    zlib1g-dev \\
    libcairo2 \\
    libcairo2-dev \\
    fontconfig \\
    procps \\
    # WeasyPrint dependencies for PDF generation
    libpango-1.0-0 \\
    libpangocairo-1.0-0 \\
    libgdk-pixbuf-2.0-0 \\
    shared-mime-info \\
    && apt-get clean \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements/prod.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set working directory
WORKDIR /opt/{slug_name}

# Copy project code (backend directory contents)
COPY ./backend/ .

# Expose port for Flower
EXPOSE 5555

COPY ./entrypoint-flower.sh /entrypoint-flower.sh
RUN chmod +x /entrypoint-flower.sh

ENTRYPOINT ["/entrypoint-flower.sh"]
"""
    flower_dockerfile.write_text(flower_content)
    print(f"  ✓ Created {flower_dockerfile.name}")


def update_backend_ci(workflows_dir: Path) -> None:
    """Update backend-ci.yml to include Celery services."""
    backend_ci = workflows_dir / "backend-ci.yml"
    
    if not backend_ci.exists():
        print(f"  ⚠ Warning: {backend_ci} not found, skipping")
        return
    
    content = backend_ci.read_text()
    
    # Add to matrix images
    if '- flower' not in content:
        # Find the backend line and add celery services after it
        matrix_section = '''                image:
                    - backend'''
        
        new_matrix = '''                image:
                    - backend
                    - flower
                    - celery-worker
                    - celery-beat'''
        
        content = content.replace(matrix_section, new_matrix)
    
    # Add Dockerfiles and entrypoints to paths
    if 'Dockerfile.flower' not in content:
        # Find the paths section and add new files
        paths_section = '''            - "backend/**"
            - "Dockerfile.backend"'''
        
        new_paths = '''            - "backend/**"
            - "Dockerfile.backend"
            - "Dockerfile.flower"
            - "Dockerfile.celery-worker"
            - "Dockerfile.celery-beat"
            - "entrypoint-flower.sh"
            - "entrypoint-celery-worker.sh"'''
        
        content = content.replace(paths_section, new_paths)
    
    backend_ci.write_text(content)
    print(f"  ✓ Updated {backend_ci.relative_to(workflows_dir.parent)}")


def update_tasks_json(project_root: Path, queues: list[str]) -> None:
    """Update tasks.json with Celery tasks."""
    import json
    
    tasks_json = project_root / ".vscode" / "tasks.json"
    
    if not tasks_json.exists():
        print(f"  ⚠ {tasks_json.relative_to(project_root)} not found, skipping")
        return
    
    with open(tasks_json) as f:
        data = json.load(f)
    
    tasks = data.get("tasks", [])
    existing_commands = {task.get("command") for task in tasks if "command" in task}
    
    # Task template with presentation config
    def create_task(label: str, command: str, is_background: bool = True) -> dict:
        task = {
            "label": label,
            "type": "shell",
            "command": command,
            "group": "build",
            "presentation": {
                "echo": True,
                "reveal": "always",
                "focus": False,
                "panel": "new",
                "showReuseMessage": True
            }
        }
        if is_background:
            task["isBackground"] = True
            task["problemMatcher"] = []
        return task
    
    new_tasks = []
    
    # Add multi-worker task if multiple queues
    if len(queues) > 1:
        if "start-celery-multi" not in existing_commands:
            new_tasks.append(create_task(
                "Start All Celery Workers (Multi-Queue)",
                "start-celery-multi"
            ))
    
    # Add individual queue tasks
    for queue in queues:
        command = f"start-celery-{queue}"
        if command not in existing_commands:
            queue_title = queue.replace("-", " ").replace("_", " ").title()
            new_tasks.append(create_task(
                f"Start Celery - {queue_title} Queue",
                command
            ))
    
    # Add beat task
    if "start-celery-beat" not in existing_commands:
        new_tasks.append(create_task(
            "Start Celery Beat",
            "start-celery-beat"
        ))
    
    # Add flower task
    if "start-flower" not in existing_commands:
        new_tasks.append(create_task(
            "Start Flower",
            "start-flower"
        ))
    
    if new_tasks:
        # Insert after "Start Backend" task if it exists
        backend_idx = None
        for i, task in enumerate(tasks):
            if task.get("label") == "Start Backend":
                backend_idx = i + 1
                break
        
        if backend_idx is not None:
            tasks[backend_idx:backend_idx] = new_tasks
        else:
            tasks.extend(new_tasks)
        
        data["tasks"] = tasks
        
        with open(tasks_json, "w") as f:
            json.dump(data, f, indent=4)
        
        print(f"  ✓ Added {len(new_tasks)} Celery task(s) to tasks.json")
    else:
        print(f"  ✓ Celery tasks already exist in tasks.json")


def update_devcontainer_json(project_root: Path, flower_port: str) -> None:
    """Update devcontainer.json to add Flower port by calling update-devcontainer-ports.py."""
    import subprocess
    
    devcontainer_json = project_root / ".devcontainer" / "devcontainer.json"
    
    if not devcontainer_json.exists():
        print(f"  ⚠ {devcontainer_json.relative_to(project_root)} not found, skipping")
        return
    
    # We need to re-run the devcontainer ports script with the flower port
    # The script should be called from setup-project after Celery setup,
    # so we'll just note that it needs to be called with --flower-port
    print(f"  ℹ Flower port {flower_port} will be added by setup-project")
    print(f"    (Re-run update-devcontainer-ports.py with --flower-port {flower_port} if needed)")


def main():
    parser = argparse.ArgumentParser(
        description="Configure Celery for the project template"
    )
    parser.add_argument(
        "--project-root",
        required=True,
        help="Path to project root directory"
    )
    parser.add_argument(
        "--app-name",
        required=True,
        help="Application name (e.g., 'fliplytics')"
    )
    parser.add_argument(
        "--python-name",
        required=True,
        help="Python module name (e.g., 'fliplytics')"
    )
    parser.add_argument(
        "--slug-name",
        required=True,
        help="Slug name for workdir (e.g., 'fliplytics')"
    )
    parser.add_argument(
        "--queues",
        required=True,
        help="Comma-separated list of Celery queue names (e.g., 'general,email,ebay')"
    )
    parser.add_argument(
        "--flower-port",
        default="5555",
        help="Port for Flower monitoring (default: 5555)"
    )
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root).resolve()
    backend_dir = project_root / "backend"
    scripts_dir = project_root / ".devcontainer" / "scripts"
    workflows_dir = project_root / ".github" / "workflows"
    
    # Parse queue names
    queues = [q.strip() for q in args.queues.split(",") if q.strip()]
    
    if not queues:
        print("Error: No queue names provided", file=sys.stderr)
        sys.exit(1)
    
    print(f"Configuring Celery with {len(queues)} queues: {', '.join(queues)}")
    
    # Create Celery files
    print("\nCreating Celery configuration files...")
    create_celery_py(backend_dir, args.app_name, args.python_name)
    create_bootsteps_py(backend_dir, args.python_name)
    
    # Create devcontainer scripts
    print("\nCreating devcontainer scripts...")
    create_devcontainer_scripts(scripts_dir, args.python_name, queues)
    
    # Create entrypoint scripts
    print("\nCreating entrypoint scripts...")
    create_entrypoint_scripts(project_root, args.python_name)
    
    # Create Dockerfiles
    print("\nCreating Dockerfiles...")
    create_dockerfiles(project_root, args.python_name, args.slug_name)
    
    # Update backend-ci.yml
    print("\nUpdating CI configuration...")
    update_backend_ci(workflows_dir)
    
    # Update tasks.json
    print("\nUpdating tasks.json...")
    update_tasks_json(project_root, queues)
    
    # Update devcontainer.json
    print("\nUpdating devcontainer.json...")
    update_devcontainer_json(project_root, args.flower_port)
    
    print(f"\n✅ Celery configuration complete!")
    print(f"   Queues: {', '.join(queues)}")
    print(f"   Flower port: {args.flower_port}")


if __name__ == "__main__":
    main()

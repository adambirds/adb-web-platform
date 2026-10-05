from __future__ import annotations

import ast
import re
import runpy
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.mail import get_connection
from django.test import SimpleTestCase, override_settings

from apps.ticketing.email_backend import MicrosoftGraphEmailBackend

ROOT = Path(__file__).resolve().parents[3]


class EnvironmentTemplateTests(SimpleTestCase):
    def test_github_signing_material_is_read_from_environment(self) -> None:
        with patch.dict("os.environ", {"GITHUB_APP_PRIVATE_KEY": "injected-key"}):
            configured = runpy.run_path(str(ROOT / "backend/adbsoftwaresolutions/settings.py"))
        self.assertEqual(configured["GITHUB_APP_PRIVATE_KEY"], "injected-key")
        self.assertNotIn("GITHUB_APP_CREDENTIAL_ID", configured)

    def test_template_covers_backend_and_frontend_runtime_variables(self) -> None:
        template = (ROOT / ".devcontainer/.env.example").read_text()
        documented = set(re.findall(r"^([A-Z][A-Z0-9_]*)=", template, re.MULTILINE))
        consumed: set[str] = set()
        for path in (ROOT / "backend").rglob("*.py"):
            if "tests" in path.parts:
                continue
            for node in ast.walk(ast.parse(path.read_text())):
                if not isinstance(node, ast.Call) or not node.args:
                    continue
                first = node.args[0]
                if not isinstance(first, ast.Constant) or not isinstance(first.value, str):
                    continue
                function = ast.unparse(node.func)
                if function in {
                    "os.environ.get",
                    "os.getenv",
                    "_configured_seconds",
                    "_environment_int",
                }:
                    consumed.add(first.value)
        for site in (ROOT / "sites").iterdir():
            source = site / "src"
            if not source.is_dir():
                continue
            for path in source.rglob("*"):
                if path.suffix in {".ts", ".tsx"}:
                    consumed.update(
                        re.findall(r"process\.env\.([A-Z][A-Z0-9_]*)", path.read_text())
                    )
        for name in ["entrypoint-celery-worker.sh"]:
            script = (ROOT / name).read_text()
            internal = set(re.findall(r"^([A-Z][A-Z0-9_]*)=", script, re.MULTILINE))
            consumed.update(set(re.findall(r"\$\{?([A-Z][A-Z0-9_]*)", script)) - internal)
        self.assertFalse(
            consumed - documented, f"Missing template variables: {sorted(consumed - documented)}"
        )

    def test_application_email_uses_graph_and_environment_sender(self) -> None:
        with patch.dict("os.environ", {"DEFAULT_FROM_EMAIL": "no-reply@example.test"}):
            configured = runpy.run_path(str(ROOT / "backend/adbsoftwaresolutions/settings.py"))
        with override_settings(EMAIL_BACKEND=configured["EMAIL_BACKEND"]):
            connection = get_connection()
        self.assertIsInstance(connection, MicrosoftGraphEmailBackend)
        self.assertEqual(configured["DEFAULT_FROM_EMAIL"], "no-reply@example.test")
        self.assertEqual(configured["SERVER_EMAIL"], "no-reply@example.test")
        self.assertNotIn("EMAIL_HOST", configured)

    def test_worker_entrypoint_consumes_the_application_default_queue(self) -> None:
        from adbsoftwaresolutions.celery import app

        with TemporaryDirectory() as directory:
            executable = Path(directory) / "celery"
            executable.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\"\n")
            executable.chmod(0o755)
            result = subprocess.run(
                ["sh", str(ROOT / "entrypoint-celery-worker.sh")],
                env={"PATH": f"{directory}:/usr/bin:/bin"},
                check=True,
                capture_output=True,
                text=True,
            )
        arguments = result.stdout.splitlines()
        self.assertEqual(arguments[arguments.index("-Q") + 1], app.conf.task_default_queue)

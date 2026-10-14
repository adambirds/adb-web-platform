"""Create an offline JSON archive before WordPress is switched off."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.website.services.wordpress_export import (
    WordPressExporter,
    WordPressExportError,
    route_manifest,
)


class Command(BaseCommand):
    help = (
        "Export all public WordPress posts, projects, pages, taxonomies, authors and image bytes."
    )
    requires_system_checks: list[str] = []

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--url", default="https://adbwebdesigns.co.uk")
        parser.add_argument("--output", required=True, help="Version-controlled JSON archive path.")
        parser.add_argument(
            "--routes-directory",
            help="Optionally regenerate the Web Designs frontend ID and publication-gated alias JSON files.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        destination = Path(options["output"])
        temporary: Path | None = None
        try:
            archive = WordPressExporter(options["url"], self.stdout.write).export()
            destination.parent.mkdir(parents=True, exist_ok=True)
            with NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=destination.parent, delete=False
            ) as file:
                temporary = Path(file.name)
                json.dump(archive, file, ensure_ascii=False, indent=4)
                file.write("\n")
            if temporary.stat().st_size > 90 * 1024 * 1024:
                raise WordPressExportError("Archive exceeds the 90 MB Git snapshot limit.")
            os.replace(temporary, destination)
        except (WordPressExportError, OSError, ValueError) as error:
            raise CommandError(f"Export failed; previous archive preserved: {error}") from error
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        if options["routes_directory"]:
            directory = Path(options["routes_directory"])
            directory.mkdir(parents=True, exist_ok=True)
            manifests = route_manifest(archive["collections"])
            for key, name in (
                ("wordpress_urls", "wordpress-urls.json"),
                ("editorial_aliases", "wordpress-editorial-aliases.json"),
            ):
                (directory / name).write_text(
                    json.dumps(manifests[key], indent=4, sort_keys=True) + "\n"
                )
        self.stdout.write(self.style.SUCCESS(f"Saved offline archive: {destination}"))
        self.stdout.write(json.dumps(archive["counts"], sort_keys=True))

"""Import version-controlled WordPress JSON without accessing the old website."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.core.models import Brand
from apps.website.services.wordpress_import import import_wordpress_archive


class Command(BaseCommand):
    help = "Import all archived posts/projects as drafts. No network, publication or overwrites."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--source", required=True)
        parser.add_argument("--brand", default="adb-web-designs")
        parser.add_argument(
            "--media-base-url",
            default="",
            help="Public backend/media origin for inline image links.",
        )
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            archive = json.loads(Path(options["source"]).read_text())
            brand = Brand.objects.get(slug=options["brand"], is_active=True)
            result = import_wordpress_archive(
                archive, brand, media_base_url=options["media_base_url"], dry_run=options["dry_run"]
            )
        except (OSError, ValueError, Brand.DoesNotExist) as error:
            raise CommandError(f"Draft import failed: {error}") from error
        for item in result.skipped:
            self.stdout.write(f"Skipped {item}")
        verb = "Would create" if options["dry_run"] else "Created"
        self.stdout.write(
            self.style.SUCCESS(
                f"{verb} {result.posts} blog drafts and {result.projects} portfolio drafts; {result.images} images restored."
            )
        )
        self.stdout.write("Nothing published. Review drafts in /admin/content before publishing.")

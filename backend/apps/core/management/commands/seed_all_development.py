from __future__ import annotations

from typing import Any

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    help = "Populate all currently implemented platform development data in one command."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Reset generated development records before reseeding.",
        )
        parser.add_argument(
            "--scale",
            type=int,
            default=1,
            help="Multiply generated record counts. Defaults to 1.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Allow seeding when DEBUG is disabled in a disposable environment.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        scale = max(1, options["scale"])
        reset = options["reset"]
        force = options["force"]

        common_args: list[str] = []
        if reset:
            common_args.append("--reset")
        if force:
            common_args.append("--force")
        common_args.extend(["--scale", str(scale)])

        for command_name in (
            "seed_development",
            "seed_infrastructure_development",
            "seed_ticketing_development",
        ):
            call_command(
                command_name,
                *common_args,
                stdout=self.stdout,
                stderr=self.stderr,
            )

        self.stdout.write(
            self.style.SUCCESS(f"Full platform development data ready (scale={scale}).")
        )

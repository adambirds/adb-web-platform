"""Import selected original WordPress articles as reviewable, unpublished drafts."""

from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction

from apps.core.models import Brand
from apps.website.models import BlogCategory, BlogPost, Portfolio

ARTICLES = {
    "is-wordpress-a-great-cms-for-seo": "wordpress",
    "wordpress-what-are-the-benefits": "wordpress",
    "wordpress-how-to-secure-your-website": "security",
    "freelancer-vs-agency-who-will-design-your-website": "business",
    "how-to-prevent-spam-comments-on-wordpress": "wordpress",
}


class EditorialText(HTMLParser):
    """Preserve readable headings/lists while discarding embeds and active HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.suppressed = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "iframe"}:
            self.suppressed += 1
        if self.suppressed:
            return
        if tag in {"p", "div", "section", "blockquote"}:
            self.parts.append("\n\n")
        elif tag in {"h1", "h2", "h3", "h4"}:
            self.parts.append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag == "li":
            self.parts.append("\n- ")
        elif tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "iframe"} and self.suppressed:
            self.suppressed -= 1
        elif tag in {"p", "div", "h1", "h2", "h3", "h4", "ul", "ol"}:
            self.parts.append("\n\n")

    def handle_data(self, data: str) -> None:
        if not self.suppressed:
            self.parts.append(data)

    def text(self) -> str:
        lines = [line.strip() for line in "".join(self.parts).splitlines()]
        return "\n\n".join(line for line in lines if line).strip()


def readable_html(value: str) -> str:
    parser = EditorialText()
    parser.feed(value)
    return parser.text()


class Command(BaseCommand):
    help = "Import five selected Web Designs WordPress articles and confirmed recovery case study as drafts. Never publishes or overwrites content."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--source",
            required=True,
            help="Path to the archived wp-json-wp-v2-posts.txt JSON export.",
        )
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args: Any, **options: Any) -> None:
        source = Path(options["source"])
        try:
            records = json.loads(source.read_text())
        except (OSError, ValueError) as error:
            raise CommandError("Cannot read the WordPress JSON export.") from error
        if not isinstance(records, list):
            raise CommandError("Expected a JSON list of WordPress posts.")
        selected = [record for record in records if record.get("slug") in ARTICLES]
        if options["dry_run"]:
            self.stdout.write(
                f"Would import {len(selected)} articles and one recovery case study as drafts; existing records are skipped."
            )
            return
        brand = Brand.objects.get(slug="adb-web-designs")
        with transaction.atomic():
            for record in selected:
                slug = record["slug"]
                category, _ = BlogCategory.objects.get_or_create(
                    slug=ARTICLES[slug], defaults={"name": ARTICLES[slug].title()}
                )
                category.brands.add(brand)
                post, created = BlogPost.objects.get_or_create(
                    slug=slug,
                    defaults={
                        "title": readable_html(record["title"]["rendered"]),
                        "excerpt": readable_html(record["excerpt"]["rendered"])[:500],
                        "content": readable_html(record["content"]["rendered"]),
                        "author": "Adam Birds",
                        "published": False,
                    },
                )
                if created:
                    post.brands.add(brand)
                    post.categories.add(category)
                self.stdout.write(f"{'Imported draft' if created else 'Skipped existing'}: {slug}")
            project, created = Portfolio.objects.get_or_create(
                slug="welcome-to-travel",
                defaults={
                    "title": "Welcome to Travel: recovering a hacked website",
                    "description": "Website recovery work for Welcome to Travel after its site had been hacked and infected with malware.",
                    "challenge": "Welcome to Travel needed help recovering its website after a hack and malware infection.",
                    "solution": "ADB Web Designs helped recover the affected website. The detailed work and approved project imagery will be added following review.",
                    "results": "This recovery work started the client relationship. Further project detail needs approval before publication.",
                    "technologies": "",
                    "published": False,
                    "service_slugs": ["website-rescue"],
                },
            )
            if created:
                project.brands.add(brand)
            self.stdout.write(
                f"{'Imported draft' if created else 'Skipped existing'}: welcome-to-travel"
            )
        self.stdout.write(
            self.style.SUCCESS(
                "Import complete. Review drafts, check images and publish explicitly in /admin/content."
            )
        )

from __future__ import annotations

import base64
import hashlib
import json
import re
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings
from PIL import Image

from apps.core.models import Brand
from apps.website.models import BlogCategory, BlogPost, BlogTag, Portfolio
from apps.website.services.wordpress_export import (
    WordPressExporter,
    WordPressExportError,
    route_manifest,
)
from apps.website.services.wordpress_html import html_to_markdown
from apps.website.services.wordpress_import import WordPressImportError, import_wordpress_archive


def archive_fixture() -> dict[str, Any]:
    image = BytesIO()
    Image.new("RGB", (10, 10), "cyan").save(image, format="PNG")
    data = image.getvalue()
    source = "https://adbwebdesigns.co.uk"
    posts = [
        {
            "id": 11,
            "slug": "archived-post",
            "status": "publish",
            "link": source + "/archived-post/",
            "title": {"rendered": "A &amp; B"},
            "excerpt": {"rendered": "<p>The original excerpt.</p>"},
            "content": {
                "rendered": '<h2>Original heading</h2><p><strong>Bold</strong> <a href="/project/archived-project/">project</a></p><img src="https://optimizer.example/https://adbwebdesigns.co.uk/wp-content/uploads/2021/image.png" alt="Diagram"><script>alert(1)</script>'
            },
            "author": 1,
            "categories": [2],
            "tags": [3],
            "featured_media": 4,
            "yoast_head_json": {"description": "Original SEO description"},
        }
    ]
    projects = [
        {
            "id": 12,
            "slug": "archived-project",
            "status": "publish",
            "link": source + "/project/archived-project/",
            "title": {"rendered": "Original project"},
            "excerpt": {"rendered": "<p>Original project summary</p>"},
            "content": {"rendered": '<p>[et_pb_text foo="bar"]Actual work[/et_pb_text]</p>'},
            "featured_media": 4,
        }
    ]
    collections = {
        "posts": posts,
        "projects": projects,
        "pages": [],
        "categories": [
            {
                "id": 2,
                "slug": "archived-category",
                "name": "Original category",
                "link": source + "/category/archived-category/",
                "description": "Category description",
            }
        ],
        "tags": [{"id": 3, "slug": "archived-tag", "name": "Original tag"}],
        "authors": [{"id": 1, "name": "Adam Birds"}],
        "media": [
            {
                "id": 4,
                "mime_type": "image/png",
                "source_url": source + "/wp-content/uploads/2021/image.png",
                "alt_text": "Original alternative text",
                "media_details": {"file": "2021/image.png"},
                "archive_file": {
                    "encoding": "base64",
                    "data": base64.b64encode(data).decode(),
                    "size": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                },
            }
        ],
    }
    return {
        "format": "adb-wordpress-export",
        "version": 1,
        "source": source,
        "counts": {name: len(rows) for name, rows in collections.items()},
        "collections": collections,
    }


class WordPressExportTests(SimpleTestCase):
    def test_fetches_all_pages_not_just_the_first_hundred(self) -> None:
        exporter = WordPressExporter("https://adbwebdesigns.co.uk", lambda message: None)
        first = MagicMock(headers={"X-WP-Total": "101", "X-WP-TotalPages": "2"})
        first.json.return_value = [{"id": value} for value in range(1, 101)]
        last = MagicMock(headers={"X-WP-Total": "101", "X-WP-TotalPages": "2"})
        last.json.return_value = [{"id": 101}]
        with patch.object(exporter.session, "get", side_effect=[first, last]) as get:
            self.assertEqual(len(exporter.collection("posts")), 101)
        self.assertEqual(get.call_args_list[1].kwargs["params"]["page"], 2)
        exporter.session.close()

    def test_changing_collection_is_rejected_instead_of_saving_incomplete_data(self) -> None:
        exporter = WordPressExporter("https://adbwebdesigns.co.uk", lambda message: None)
        first = MagicMock(headers={"X-WP-Total": "101", "X-WP-TotalPages": "2"})
        first.json.return_value = [{"id": 1}]
        last = MagicMock(headers={"X-WP-Total": "102", "X-WP-TotalPages": "2"})
        last.json.return_value = [{"id": 2}]
        with (
            patch.object(exporter.session, "get", side_effect=[first, last]),
            self.assertRaises(WordPressExportError),
        ):
            exporter.collection("posts")
        exporter.session.close()

    def test_failed_export_preserves_existing_archive(self) -> None:
        with TemporaryDirectory() as directory:
            file = Path(directory) / "archive.json"
            file.write_text("previous archive")
            with (
                patch.object(
                    WordPressExporter, "export", side_effect=WordPressExportError("offline")
                ),
                self.assertRaises(CommandError),
            ):
                call_command("export_wordpress_content", output=str(file), stdout=StringIO())
            self.assertEqual(file.read_text(), "previous archive")

    def test_export_saves_original_content_media_and_small_route_manifests(self) -> None:
        archive = archive_fixture()
        with TemporaryDirectory() as directory:
            file = Path(directory) / "archive.json"
            with patch.object(WordPressExporter, "export", return_value=archive):
                call_command(
                    "export_wordpress_content",
                    output=str(file),
                    routes_directory=directory,
                    stdout=StringIO(),
                )
            self.assertEqual(json.loads(file.read_text()), archive)
            self.assertEqual(
                json.loads((Path(directory) / "wordpress-editorial-aliases.json").read_text())[
                    "/archived-post"
                ],
                "/blog/archived-post/",
            )
        self.assertEqual(
            route_manifest(archive["collections"])["wordpress_urls"]["p:11"], "/archived-post/"
        )

    def test_markdown_preserves_structure_without_active_html_or_divi_tags(self) -> None:
        html = '<h2>Heading</h2><p>[et_pb_text]<em>Emphasis</em> <a href="javascript:alert(1)">unsafe</a>[/et_pb_text]</p><ol><li>One</li><li>Two</li></ol><pre><code>print("hello")</code></pre><iframe>hidden</iframe>'
        result = html_to_markdown(
            html, "https://adbwebdesigns.co.uk", lambda url: url, lambda url: url
        )
        self.assertIn("## Heading", result)
        self.assertIn("*Emphasis* unsafe", result)
        self.assertIn("1. One\n2. Two", result)
        self.assertIn('```\nprint("hello")\n```', result)
        self.assertNotIn("javascript", result)
        self.assertNotIn("et_pb", result)
        self.assertNotIn("hidden", result)


class WordPressDraftImportTests(TestCase):
    def setUp(self) -> None:
        self.web = Brand.objects.get(slug="adb-web-designs")
        self.software = Brand.objects.get(slug="adb-software-solutions")
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        settings = override_settings(MEDIA_ROOT=self.directory.name, MEDIA_URL="/media/")
        settings.enable()
        self.addCleanup(settings.disable)
        self.archive = archive_fixture()

    def run_import(self, **options: Any) -> Any:
        with patch(
            "requests.sessions.Session.request",
            side_effect=AssertionError("Importer attempted network access"),
        ):
            return import_wordpress_archive(
                self.archive, self.web, media_base_url="http://localhost:8000", **options
            )

    def test_import_is_offline_draft_only_and_scoped_with_original_taxonomies_and_images(
        self,
    ) -> None:
        result = self.run_import()
        self.assertEqual((result.posts, result.projects, result.images), (1, 1, 1))
        post = BlogPost.objects.get(slug="archived-post")
        project = Portfolio.objects.get(slug="archived-project")
        self.assertFalse(post.published)
        self.assertIsNone(post.published_at)
        self.assertFalse(project.published)
        self.assertEqual(list(post.brands.values_list("pk", flat=True)), [self.web.pk])
        self.assertFalse(post.brands.filter(pk=self.software.pk).exists())
        self.assertEqual(post.author, "Adam Birds")
        self.assertEqual(post.title, "A & B")
        self.assertIn("**Bold**", post.content)
        self.assertIn("/portfolio/archived-project/", post.content)
        self.assertIn("http://localhost:8000/media/wordpress-import/", post.content)
        self.assertNotIn("optimizer.example", post.content)
        self.assertNotIn("alert(1)", post.content)
        self.assertEqual(post.categories.get().slug, "archived-category")
        self.assertEqual(post.tags.get().slug, "archived-tag")
        self.assertEqual(post.meta_description, "Original SEO description")
        self.assertEqual(project.solution, "Actual work")
        self.assertEqual(project.challenge, "")
        self.assertEqual(project.results, "")
        image_name = post.featured_image.name
        assert image_name is not None
        self.assertTrue(post.featured_image.storage.exists(image_name))
        self.assertEqual(project.image.name, post.featured_image.name)
        for kind in ("blog", "portfolio"):
            response = self.client.get(f"/api/public/collections/{kind}", {"brand": self.web.slug})
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("archived-", json.dumps(response.json()))

    def test_rerun_preserves_edits_publication_and_images(self) -> None:
        self.run_import()
        post = BlogPost.objects.get(slug="archived-post")
        post.title = "Manually edited"
        post.published = True
        post.save()
        existing_name = post.featured_image.name
        result = self.run_import()
        post.refresh_from_db()
        self.assertEqual((result.posts, result.projects, result.images), (0, 0, 0))
        self.assertEqual(post.title, "Manually edited")
        self.assertTrue(post.published)
        self.assertEqual(post.featured_image.name, existing_name)
        self.assertEqual(len(list(Path(self.directory.name).rglob("*.webp"))), 1)

    def test_dry_run_has_no_database_or_storage_writes(self) -> None:
        result = self.run_import(dry_run=True)
        self.assertEqual((result.posts, result.projects), (1, 1))
        self.assertFalse(BlogPost.objects.filter(slug="archived-post").exists())
        self.assertFalse(BlogCategory.objects.filter(slug="archived-category").exists())
        self.assertFalse(BlogTag.objects.filter(slug="archived-tag").exists())
        self.assertEqual(list(Path(self.directory.name).iterdir()), [])

    def test_corrupt_media_aborts_before_any_write(self) -> None:
        self.archive["collections"]["media"][0]["archive_file"]["sha256"] = "invalid"
        with self.assertRaises(WordPressImportError):
            self.run_import()
        self.assertFalse(BlogPost.objects.filter(slug="archived-post").exists())
        self.assertEqual(list(Path(self.directory.name).iterdir()), [])

    def test_incomplete_archives_and_other_brand_sources_are_rejected(self) -> None:
        self.archive["counts"]["posts"] = 99
        with self.assertRaises(WordPressImportError):
            self.run_import()
        self.archive = archive_fixture()
        with self.assertRaises(WordPressImportError):
            import_wordpress_archive(
                self.archive, self.software, media_base_url="http://localhost:8000"
            )

    def test_existing_other_brand_posts_are_preserved_and_not_reassigned(self) -> None:
        item = BlogPost.objects.create(
            slug="archived-post", title="Software", content="Keep", excerpt="Keep", published=True
        )
        item.brands.add(self.software)
        self.run_import()
        item.refresh_from_db()
        self.assertEqual(item.content, "Keep")
        self.assertTrue(item.published)
        self.assertFalse(item.brands.filter(pk=self.web.pk).exists())

    def test_taxonomy_collision_aborts_without_extending_other_brand_access(self) -> None:
        category = BlogCategory.objects.create(slug="archived-category", name="Software")
        category.brands.add(self.software)
        with self.assertRaises(WordPressImportError):
            self.run_import()
        self.assertFalse(category.brands.filter(pk=self.web.pk).exists())
        self.assertFalse(Portfolio.objects.filter(slug="archived-project").exists())

    def test_database_failure_rolls_back_records_and_removes_new_files(self) -> None:
        with (
            patch.object(Portfolio.objects, "create", side_effect=ValueError("database failure")),
            self.assertRaises(ValueError),
        ):
            self.run_import()
        self.assertFalse(BlogPost.objects.filter(slug="archived-post").exists())
        self.assertFalse(BlogCategory.objects.filter(slug="archived-category").exists())
        self.assertEqual(list(Path(self.directory.name).rglob("*.webp")), [])

    def test_command_imports_exported_json_with_network_disabled(self) -> None:
        file = Path(self.directory.name) / "archive.json"
        file.write_text(json.dumps(self.archive))
        with patch(
            "requests.sessions.Session.request", side_effect=AssertionError("Network forbidden")
        ):
            call_command(
                "import_wordpress_content",
                source=str(file),
                media_base_url="http://localhost:8000",
                stdout=StringIO(),
            )
        self.assertFalse(BlogPost.objects.get(slug="archived-post").published)

    def test_versioned_live_snapshot_imports_completely_without_wordpress(self) -> None:
        path = (
            Path(__file__).resolve().parents[4]
            / "backend/apps/website/fixtures/wordpress/adb-web-designs.json"
        )
        self.archive = json.loads(path.read_text())
        result = self.run_import()
        self.assertEqual(result.posts, self.archive["counts"]["posts"])
        self.assertEqual(result.projects, self.archive["counts"]["projects"])
        self.assertFalse(BlogPost.objects.filter(brands=self.web, published=True).exists())
        self.assertFalse(Portfolio.objects.filter(brands=self.web, published=True).exists())
        self.assertGreater(result.images, 0)
        for post in BlogPost.objects.filter(brands=self.web):
            for url in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", post.content):
                self.assertNotIn("optimole.com", url, post.slug)
                self.assertNotIn("adbwebdesigns.co.uk/wp-content", url, post.slug)

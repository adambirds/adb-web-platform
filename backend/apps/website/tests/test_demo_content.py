from io import StringIO
from tempfile import TemporaryDirectory

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from apps.core.models import Brand
from apps.website.models import FAQ, BlogPost, Portfolio, Testimonial


class WebDesignsDemoContentTests(TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.settings_override = override_settings(DEBUG=True, MEDIA_ROOT=self.directory.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.web = Brand.objects.get(slug="adb-web-designs")
        self.software = Brand.objects.get(slug="adb-software-solutions")

    def seed(self, **options: bool) -> None:
        call_command("seed_web_designs_demo", stdout=StringIO(), **options)

    def test_preview_is_published_scoped_and_repeatable(self) -> None:
        self.seed()
        self.seed()
        self.assertEqual(Portfolio.objects.filter(slug__startswith="demo-wd-").count(), 12)
        self.assertEqual(BlogPost.objects.filter(slug__startswith="demo-wd-").count(), 12)
        self.assertEqual(Testimonial.objects.filter(client_name__startswith="Demo WD /").count(), 3)
        self.assertEqual(FAQ.objects.filter(category__slug__startswith="demo-wd-").count(), 10)
        self.assertFalse(
            Portfolio.objects.filter(slug__startswith="demo-wd-", brands=self.software).exists()
        )
        response = self.client.get(
            "/api/public/collections/portfolio", {"brand": str(self.web.slug), "page": "2"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total"], 12)
        self.assertEqual(len(response.json()["items"]), 3)
        item = Portfolio.objects.get(slug="demo-wd-project-1")
        assert item.featured_image.name is not None
        self.assertTrue(item.featured_image.storage.exists(item.featured_image.name))

    def test_refresh_changes_only_demo_images_and_preserves_content(self) -> None:
        self.seed()
        item = Portfolio.objects.get(slug="demo-wd-project-1")
        item.description = "My edited demo copy"
        item.featured_image.save("edited-demo.png", ContentFile(b"previous demo image"))
        previous = item.featured_image.name
        assert previous is not None
        item.save()
        self.seed()
        item.refresh_from_db()
        self.assertEqual(item.featured_image.name, previous)
        self.seed(refresh_images=True)
        item.refresh_from_db()
        self.assertEqual(item.description, "My edited demo copy")
        self.assertFalse(item.featured_image.storage.exists(previous))
        with item.featured_image.open("rb") as image:
            self.assertTrue(image.read().startswith(b"\x89PNG"))

    def test_cleanup_keeps_real_content_and_deletes_demo_images(self) -> None:
        real = Portfolio.objects.create(
            title="Real project",
            slug="real-project",
            description="Real",
            challenge="",
            solution="",
            results="",
            technologies="",
            published=True,
        )
        real.brands.set([self.web])
        self.seed()
        image = Portfolio.objects.get(slug="demo-wd-project-1").featured_image
        name = image.name
        assert name is not None
        self.seed(clear=True)
        self.assertFalse(image.storage.exists(name))
        self.assertFalse(Portfolio.objects.filter(slug__startswith="demo-wd-").exists())
        self.assertFalse(BlogPost.objects.filter(slug__startswith="demo-wd-").exists())
        self.assertTrue(Portfolio.objects.filter(pk=real.pk).exists())

    @override_settings(DEBUG=False)
    def test_production_configuration_cannot_seed_demo_content(self) -> None:
        with self.assertRaises(CommandError):
            self.seed()
        self.assertFalse(Portfolio.objects.filter(slug__startswith="demo-wd-").exists())

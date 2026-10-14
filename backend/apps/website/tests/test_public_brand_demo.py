import tempfile
from io import StringIO
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from apps.core.models import Brand
from apps.website.models import FAQ, BlogPost, FAQCategory, Portfolio, Testimonial


@override_settings(DEBUG=True)
class PublicBrandDemoTests(TestCase):
    def setUp(self) -> None:
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        override = override_settings(MEDIA_ROOT=self.media.name)
        override.enable()
        self.addCleanup(override.disable)
        self.software = Brand.objects.get(slug="adb-software-solutions")
        self.technology = Brand.objects.get(slug="adb-technology")
        self.web = Brand.objects.get(slug="adb-web-designs")

    def seed(self, brand: str = "all", *, clear: bool = False) -> None:
        call_command("seed_public_brand_demo", brand=brand, clear=clear, stdout=StringIO())

    def test_both_brands_are_populated_without_cross_brand_content(self) -> None:
        self.seed()
        for brand in [self.software, self.technology]:
            self.assertEqual(Portfolio.objects.filter(brands=brand, published=True).count(), 3)
            self.assertEqual(BlogPost.objects.filter(brands=brand, published=True).count(), 3)
            self.assertEqual(Testimonial.objects.filter(brands=brand, published=True).count(), 2)
            self.assertEqual(FAQ.objects.filter(brands=brand, published=True).count(), 6)
        self.assertFalse(Portfolio.objects.filter(brands=self.web).exists())
        self.assertFalse(
            Portfolio.objects.filter(brands=self.software).filter(brands=self.technology).exists()
        )
        self.assertFalse(
            Testimonial.objects.filter(brands=self.software)
            .exclude(quote__icontains="fictional")
            .exists()
        )

    def test_repeat_seed_preserves_edits_and_images(self) -> None:
        self.seed("software")
        item = Portfolio.objects.get(slug="demo-ss-project-1")
        item.description = "Edited demonstration copy"
        item.save()
        previous = item.featured_image.name
        self.seed("software")
        item.refresh_from_db()
        self.assertEqual(item.description, "Edited demonstration copy")
        self.assertEqual(item.featured_image.name, previous)
        self.assertEqual(Portfolio.objects.count(), 3)
        self.assertFalse(Portfolio.objects.filter(brands=self.technology).exists())

    def test_selected_cleanup_preserves_other_brand_and_real_content(self) -> None:
        self.seed()
        real = Portfolio.objects.create(title="Real draft", slug="real-software", technologies="")
        real.brands.set([self.software])
        item = Portfolio.objects.get(slug="demo-ss-project-1")
        image = item.featured_image
        filename = image.name
        assert filename is not None
        real_faq = FAQ.objects.create(
            question="Real question",
            answer="Real answer",
            category=FAQCategory.objects.get(slug="demo-ss-questions"),
        )
        real_faq.brands.set([self.software])
        self.seed("software", clear=True)
        self.assertTrue(FAQ.objects.filter(pk=real_faq.pk).exists())
        self.assertFalse(image.storage.exists(filename))
        self.assertTrue(Portfolio.objects.filter(pk=real.pk).exists())
        self.assertEqual(Portfolio.objects.filter(brands=self.technology).count(), 3)
        self.assertFalse(FAQ.objects.filter(question__startswith="Demo SS / ").exists())

    @override_settings(DEBUG=False)
    def test_production_mode_cannot_seed_or_clear(self) -> None:
        for clear in [False, True]:
            with self.assertRaises(CommandError):
                self.seed(clear=clear)

    def test_remote_database_is_rejected(self) -> None:
        with (
            patch.dict(settings.DATABASES["default"], {"HOST": "production.example"}),
            self.assertRaises(CommandError),
        ):
            self.seed()

    def test_reserved_slug_collision_does_not_adopt_existing_content(self) -> None:
        existing = Portfolio.objects.create(
            title="Existing", slug="demo-ss-project-1", technologies=""
        )
        existing.brands.set([self.web])
        with self.assertRaises(CommandError):
            self.seed("software")
        self.assertEqual(list(existing.brands.all()), [self.web])
        self.assertFalse(BlogPost.objects.exists())

from datetime import timedelta
from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image

from apps.core.models import Brand
from apps.website.models import BlogCategory, BlogPost, FAQCategory, Portfolio, Testimonial
from authentication.models import User


class PublishingAndMediaTests(TestCase):
    def setUp(self) -> None:
        self.web = Brand.objects.get(slug="adb-web-designs")
        self.software = Brand.objects.get(slug="adb-software-solutions")
        self.user = User.objects.create_user(
            email="cms@example.com",
            first_name="CMS",
            last_name="Editor",
            password="test-password",
            is_staff=True,
        )
        self.item = Portfolio.objects.create(
            title="CMS image",
            slug="cms-image",
            description="Image project",
            challenge="Before",
            solution="Work",
            results="After",
        )
        self.item.brands.add(self.web)
        self.url = f"/api/admin/website/media/portfolio/{self.item.pk}/image"

    def image(self) -> SimpleUploadedFile:
        output = BytesIO()
        Image.new("RGB", (20, 10), color="cyan").save(output, "PNG")
        return SimpleUploadedFile("test.png", output.getvalue(), content_type="image/png")

    def grant(self, capability: str) -> None:
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label="website", codename=capability)
        )
        self.client.force_login(self.user)

    def test_drafts_and_scheduled_articles_are_not_public(self) -> None:
        draft = Testimonial.objects.create(quote="Not published", client_name="Client")
        draft.brands.add(self.web)
        post = BlogPost.objects.create(
            title="Scheduled",
            slug="scheduled",
            published=True,
            published_at=timezone.now() + timedelta(days=1),
        )
        post.brands.add(self.web)
        for kind in ["portfolio", "testimonials", "blog"]:
            response = self.client.get(f"/api/public/collections/{kind}", {"brand": self.web.slug})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["total"], 0)
        self.assertEqual(
            self.client.get(
                "/api/public/blog/posts/scheduled", {"brand": self.web.slug}
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(
                "/api/public/portfolio/cms-image", {"brand": self.web.slug}
            ).status_code,
            404,
        )

    def test_collection_pagination_and_service_filter_do_not_leak_other_brands(self) -> None:
        for index in range(5):
            item = Portfolio.objects.create(
                title=f"Project {index}",
                slug=f"project-{index}",
                published=True,
                service_slugs=["website-rescue"],
            )
            item.brands.add(self.web if index < 4 else self.software)
        response = self.client.get(
            "/api/public/collections/portfolio",
            {"brand": self.web.slug, "page": "2", "page_size": "2", "service": "website-rescue"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total"], 4)
        self.assertEqual(len(response.json()["items"]), 2)
        self.assertTrue(
            all(item["brand_slugs"] == [self.web.slug] for item in response.json()["items"])
        )
        self.assertEqual(
            self.client.get(
                "/api/public/collections/portfolio", {"brand": self.web.slug, "page_size": "100"}
            ).status_code,
            400,
        )

    def test_nested_taxonomy_does_not_leak_other_brands(self) -> None:
        private = BlogCategory.objects.create(name="Software only", slug="software-only")
        private.brands.add(self.software)
        post = BlogPost.objects.create(
            title="Shared article", slug="shared-article", published=True
        )
        post.brands.add(self.web)
        post.categories.add(private)
        response = self.client.get(
            "/api/public/blog/posts/shared-article", {"brand": self.web.slug}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["categories"], [])

    def test_upload_requires_authentication_and_change_capability(self) -> None:
        self.assertEqual(self.client.post(self.url, {"image": self.image()}).status_code, 401)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(self.url, {"image": self.image()}).status_code, 403)
        self.assertEqual(self.client.delete(self.url).status_code, 403)
        self.grant("view_portfolio")
        self.assertEqual(self.client.post(self.url, {"image": self.image()}).status_code, 403)

    def test_upload_normalizes_image_and_can_remove_it(self) -> None:
        self.grant("change_portfolio")
        with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            response = self.client.post(self.url, {"image": self.image()})
            self.assertEqual(response.status_code, 200)
            self.item.refresh_from_db()
            self.assertTrue(str(self.item.image.name).endswith(".webp"))
            with Image.open(self.item.image.path) as image:
                self.assertEqual(image.format, "WEBP")
            self.assertEqual(self.client.delete(self.url).status_code, 200)
            self.item.refresh_from_db()
            self.assertFalse(self.item.image)

    def test_media_links_use_public_storage_origin_with_private_ssr_host(self) -> None:
        self.grant("change_portfolio")
        with (
            TemporaryDirectory() as directory,
            override_settings(
                MEDIA_ROOT=directory,
                MEDIA_URL="https://media.example.test/media/",
                ALLOWED_HOSTS=["internal-api"],
            ),
        ):
            response = self.client.post(self.url, {"image": self.image()}, HTTP_HOST="internal-api")
            self.assertEqual(response.status_code, 200)
            self.assertTrue(
                response.json()["image_url"].startswith("https://media.example.test/media/")
            )

    def test_upload_rejects_oversized_raster(self) -> None:
        self.grant("change_portfolio")
        oversized = SimpleUploadedFile(
            "large.png", b"x" * (8 * 1024 * 1024 + 1), content_type="image/png"
        )
        self.assertEqual(self.client.post(self.url, {"image": oversized}).status_code, 413)

    def test_upload_rejects_non_images_and_invalid_fields(self) -> None:
        self.grant("change_portfolio")
        invalid = SimpleUploadedFile(
            "test.svg", b'<svg onload="alert(1)"/>', content_type="image/svg+xml"
        )
        self.assertEqual(self.client.post(self.url, {"image": invalid}).status_code, 400)
        self.assertEqual(
            self.client.post(
                self.url.replace("/image", "/title"), {"image": self.image()}
            ).status_code,
            400,
        )

    def test_publishing_requires_model_capability_and_rejects_unsafe_project_links(self) -> None:
        self.item.published = True
        self.item.save()
        payload = {
            "title": "Project",
            "slug": "project",
            "description": "Description",
            "challenge": "Before",
            "solution": "Work",
            "results": "After",
            "technologies": [],
            "published": True,
            "brand_ids": [self.web.id],
        }
        self.client.force_login(self.user)
        self.assertEqual(
            self.client.put(
                f"/api/admin/website/portfolio/{self.item.pk}",
                payload,
                content_type="application/json",
            ).status_code,
            403,
        )
        self.grant("change_portfolio")
        payload["project_url"] = "javascript:alert(1)"
        self.assertEqual(
            self.client.put(
                f"/api/admin/website/portfolio/{self.item.pk}",
                payload,
                content_type="application/json",
            ).status_code,
            422,
        )

    def test_faq_category_must_match_brand_and_failed_create_rolls_back(self) -> None:
        from apps.website.models import FAQ

        self.grant("add_faq")
        category = FAQCategory.objects.create(name="Software", slug="software")
        category.brands.add(self.software)
        response = self.client.post(
            "/api/admin/website/faqs",
            {
                "question": "Mismatched?",
                "answer": "Answer",
                "category_id": category.id,
                "brand_ids": [self.web.id],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(FAQ.objects.filter(question="Mismatched?").exists())

    def test_invalid_brand_rolls_back_created_record(self) -> None:
        self.grant("add_testimonial")
        response = self.client.post(
            "/api/admin/website/testimonials",
            {"quote": "Invalid", "client_name": "Client", "brand_ids": [999999]},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Testimonial.objects.filter(quote="Invalid").exists())


class WebsiteContactTests(TestCase):
    def setUp(self) -> None:
        from apps.ticketing.models import TicketQueue

        self.web = Brand.objects.get(slug="adb-web-designs")
        TicketQueue.objects.get_or_create(
            brand=self.web, key="sales", defaults={"name": "Sales", "purpose": "Sales enquiries"}
        )

    def test_contact_creates_brand_aware_lead_and_ticket(self) -> None:
        from apps.crm.models import Lead
        from apps.ticketing.models import Ticket

        response = self.client.post(
            "/api/website/contact?brand=adb-web-designs",
            {
                "name": "Website Visitor",
                "email": "visitor@example.com",
                "message": "Please discuss recovering my hacked website.",
                "company": "Visitor Co",
                "source_path": "/contact/",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        lead = Lead.objects.get(email="visitor@example.com")
        self.assertEqual(lead.brand, self.web)
        self.assertIn("/contact/", lead.message)
        self.assertTrue(
            Ticket.objects.filter(
                messages__provider_message_id=f"website-contact-form:{lead.id}", brand=self.web
            ).exists()
        )

    def test_honeypot_does_not_create_leads(self) -> None:
        from apps.crm.models import Lead

        response = self.client.post(
            "/api/website/contact?brand=adb-web-designs",
            {
                "name": "Spam",
                "email": "spam@example.com",
                "message": "An unwanted advertising message",
                "website": "https://spam.invalid",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Lead.objects.filter(email="spam@example.com").exists())

    def test_contact_rejects_invalid_email_or_brand(self) -> None:
        payload = {
            "name": "Visitor",
            "email": "not-an-email",
            "message": "Please discuss a new website.",
        }
        self.assertEqual(
            self.client.post(
                "/api/website/contact?brand=adb-web-designs",
                payload,
                content_type="application/json",
            ).status_code,
            422,
        )
        payload["email"] = "visitor@example.com"
        self.assertEqual(
            self.client.post(
                "/api/website/contact?brand=unknown", payload, content_type="application/json"
            ).status_code,
            404,
        )


class WebsiteContactThrottlingTests(TestCase):
    @override_settings(
        RATE_LIMIT_DISABLED=False,
        SESSION_ENGINE="django.contrib.sessions.backends.db",
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "website-contact-limit",
            }
        },
    )
    def test_sixth_enquiry_in_window_is_throttled(self) -> None:
        payload = {
            "name": "Visitor",
            "email": "visitor@example.com",
            "message": "An advertising message.",
            "website": "spam",
        }
        for _ in range(5):
            self.assertEqual(
                self.client.post(
                    "/api/website/contact?brand=adb-web-designs",
                    payload,
                    content_type="application/json",
                    REMOTE_ADDR="192.0.2.30",
                ).status_code,
                200,
            )
        response = self.client.post(
            "/api/website/contact?brand=adb-web-designs",
            payload,
            content_type="application/json",
            REMOTE_ADDR="192.0.2.30",
        )
        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response.headers)

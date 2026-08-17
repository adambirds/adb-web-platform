from django.contrib.auth.models import Permission
from django.test import TestCase

from apps.core.models import Brand
from apps.website.models import FAQ, BlogPost, FAQCategory, Portfolio, Testimonial
from authentication.models import User


class BrandAwarePublicContentTests(TestCase):
    def setUp(self) -> None:
        self.software = Brand.objects.get(slug="adb-software-solutions")
        self.web = Brand.objects.get(slug="adb-web-designs")

        software_testimonial = Testimonial.objects.create(
            quote="Software testimonial",
            client_name="Software Client",
            company="Software Co",
        )
        software_testimonial.brands.add(self.software)

        web_testimonial = Testimonial.objects.create(
            quote="Web testimonial",
            client_name="Web Client",
            company="Web Co",
        )
        web_testimonial.brands.add(self.web)

        software_post = BlogPost.objects.create(
            title="Software post",
            slug="software-post",
            excerpt="Software",
            content="Software body",
            published=True,
        )
        software_post.brands.add(self.software)

        web_post = BlogPost.objects.create(
            title="Web post",
            slug="web-post",
            excerpt="Web",
            content="Web body",
            published=True,
        )
        web_post.brands.add(self.web)

        software_category = FAQCategory.objects.create(
            name="Software FAQs",
            slug="software-faqs",
        )
        software_category.brands.add(self.software)
        software_faq = FAQ.objects.create(
            question="Software question?",
            answer="Software answer",
            category=software_category,
        )
        software_faq.brands.add(self.software)

        web_category = FAQCategory.objects.create(
            name="Web FAQs",
            slug="web-faqs",
        )
        web_category.brands.add(self.web)
        web_faq = FAQ.objects.create(
            question="Web question?",
            answer="Web answer",
            category=web_category,
        )
        web_faq.brands.add(self.web)

        software_portfolio = Portfolio.objects.create(
            title="Software case study",
            slug="software-case-study",
            description="Software project",
            challenge="Challenge",
            solution="Solution",
            results="Results",
        )
        software_portfolio.brands.add(self.software)

        web_portfolio = Portfolio.objects.create(
            title="Web case study",
            slug="web-case-study",
            description="Web project",
            challenge="Challenge",
            solution="Solution",
            results="Results",
        )
        web_portfolio.brands.add(self.web)

    def test_testimonials_are_scoped_to_requested_brand(self) -> None:
        response = self.client.get(
            "/api/public/testimonials",
            {"brand": self.software.slug},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["quote"], "Software testimonial")
        self.assertEqual(payload[0]["brand_slugs"], [self.software.slug])

    def test_blog_posts_are_scoped_to_requested_brand(self) -> None:
        response = self.client.get(
            "/api/public/blog/posts",
            {"brand": self.software.slug},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([post["slug"] for post in payload], ["software-post"])

    def test_faqs_are_scoped_to_requested_brand(self) -> None:
        response = self.client.get(
            "/api/public/faqs",
            {"brand": self.software.slug},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([faq["question"] for faq in payload], ["Software question?"])

    def test_portfolio_is_scoped_to_requested_brand(self) -> None:
        response = self.client.get(
            "/api/public/portfolio",
            {"brand": self.software.slug},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([item["slug"] for item in payload], ["software-case-study"])
        self.assertEqual(payload[0]["brand_slugs"], [self.software.slug])

    def test_unknown_brand_does_not_return_cross_brand_content(self) -> None:
        response = self.client.get(
            "/api/public/testimonials",
            {"brand": "does-not-exist"},
        )

        self.assertEqual(response.status_code, 404)


class CMSAdminPermissionTests(TestCase):
    def setUp(self) -> None:
        self.software = Brand.objects.get(slug="adb-software-solutions")
        self.web = Brand.objects.get(slug="adb-web-designs")
        self.staff = User.objects.create_user(
            email="cms-staff@example.com",
            password="correct-horse-battery-staple",
            first_name="CMS",
            last_name="Staff",
            is_staff=True,
        )
        self.client.force_login(self.staff)

    def grant(self, codename: str) -> None:
        permission = Permission.objects.get(
            content_type__app_label="website",
            codename=codename,
        )
        self.staff.user_permissions.add(permission)

    def assert_brands(self, item, expected: set[str]) -> None:
        self.assertSetEqual(
            set(item.brands.values_list("slug", flat=True)),
            expected,
        )

    def test_staff_without_capability_cannot_list_testimonials(self) -> None:
        response = self.client.get("/api/admin/website/testimonials")
        self.assertEqual(response.status_code, 403)

    def test_staff_with_view_capability_can_list_testimonials(self) -> None:
        self.grant("view_testimonial")
        testimonial = Testimonial.objects.create(
            quote="Visible testimonial",
            client_name="Client",
        )
        testimonial.brands.add(self.software)

        response = self.client.get("/api/admin/website/testimonials")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["brand_slugs"], [self.software.slug])

    def test_create_persists_selected_brands(self) -> None:
        self.grant("add_testimonial")

        response = self.client.post(
            "/api/admin/website/testimonials",
            data={
                "quote": "Cross-brand testimonial",
                "client_name": "Client",
                "company": "Company",
                "rating": 5,
                "featured": True,
                "brand_ids": [self.software.id, self.web.id],
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        testimonial = Testimonial.objects.get(quote="Cross-brand testimonial")
        self.assert_brands(testimonial, {self.software.slug, self.web.slug})

    def test_create_blog_post_persists_selected_brands(self) -> None:
        self.grant("add_blogpost")

        response = self.client.post(
            "/api/admin/website/blog/posts",
            data={
                "title": "Shared post",
                "slug": "shared-post",
                "excerpt": "Shared",
                "content": "Shared body",
                "brand_ids": [self.software.id, self.web.id],
                "category_ids": [],
                "tag_ids": [],
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assert_brands(
            BlogPost.objects.get(slug="shared-post"),
            {self.software.slug, self.web.slug},
        )

    def test_create_faq_persists_selected_brands(self) -> None:
        self.grant("add_faq")
        category = FAQCategory.objects.create(name="Shared", slug="shared")
        category.brands.add(self.software, self.web)

        response = self.client.post(
            "/api/admin/website/faqs",
            data={
                "question": "Shared question?",
                "answer": "Shared answer",
                "category_id": category.id,
                "brand_ids": [self.software.id, self.web.id],
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assert_brands(
            FAQ.objects.get(question="Shared question?"),
            {self.software.slug, self.web.slug},
        )

    def test_create_portfolio_persists_selected_brands(self) -> None:
        self.grant("add_portfolio")

        response = self.client.post(
            "/api/admin/website/portfolio",
            data={
                "title": "Shared case study",
                "slug": "shared-case-study",
                "description": "Description",
                "challenge": "Challenge",
                "solution": "Solution",
                "results": "Results",
                "technologies": ["Django", "Next.js"],
                "brand_ids": [self.software.id, self.web.id],
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assert_brands(
            Portfolio.objects.get(slug="shared-case-study"),
            {self.software.slug, self.web.slug},
        )

    def test_create_rejects_unknown_brand_id(self) -> None:
        self.grant("add_testimonial")

        response = self.client.post(
            "/api/admin/website/testimonials",
            data={
                "quote": "Invalid brand testimonial",
                "client_name": "Client",
                "rating": 5,
                "brand_ids": [999999],
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

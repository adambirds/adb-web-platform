from django.test import TestCase

from apps.core.models import Brand
from apps.website.models import Testimonial


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

    def test_testimonials_are_scoped_to_requested_brand(self) -> None:
        response = self.client.get(
            "/api/public/testimonials",
            {"brand": self.software.slug},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["quote"], "Software testimonial")

    def test_unknown_brand_does_not_return_cross_brand_content(self) -> None:
        response = self.client.get(
            "/api/public/testimonials",
            {"brand": "does-not-exist"},
        )

        self.assertEqual(response.status_code, 404)

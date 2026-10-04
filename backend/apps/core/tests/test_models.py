from django.test import TestCase

from apps.core.models import AuditEvent, Brand
from authentication.models import User


class BrandFoundationTests(TestCase):
    def test_initial_brands_are_seeded(self) -> None:
        self.assertSetEqual(
            set(Brand.objects.values_list("slug", flat=True)),
            {
                "adb-software-solutions",
                "adb-web-designs",
                "adb-technology",
            },
        )


class AuditEventTests(TestCase):
    def test_record_does_not_require_a_target(self) -> None:
        user = User.objects.create_user(
            email="admin@example.com",
            password="not-a-real-password",
            first_name="Admin",
            last_name="User",
        )

        event = AuditEvent.record(
            actor=user,
            action="permissions.changed",
            metadata={"permission_count": 3},
        )

        self.assertEqual(event.actor, user)
        self.assertEqual(event.action, "permissions.changed")
        self.assertEqual(event.target_type, "")
        self.assertEqual(event.metadata, {"permission_count": 3})

from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.test import TestCase

from apps.ticketing.models import TicketQueue, Vendor, VendorSenderRule
from authentication.models import User


class VendorSettingsApiTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="vendor-settings@example.test",
            password="not-a-real-password",
            first_name="Vendor",
            last_name="Admin",
            is_staff=True,
        )
        self.client.force_login(self.user)
        self.vendor_queue = TicketQueue.objects.get(key="vendors-services")

    def _grant(self, *codenames: str) -> None:
        permissions = Permission.objects.filter(
            content_type__app_label="ticketing",
            codename__in=codenames,
        )
        self.user.user_permissions.add(*permissions)

    def test_vendor_list_requires_view_permission(self) -> None:
        response = self.client.get("/api/admin/settings/ticketing/vendors")

        self.assertEqual(response.status_code, 403)

    def test_vendor_and_sender_rule_can_be_configured(self) -> None:
        self._grant("configure_vendors", "view_vendor", "view_vendorsenderrule")

        vendor_response = self.client.post(
            "/api/admin/settings/ticketing/vendors",
            data={"name": "Cloudflare", "website_url": "https://www.cloudflare.com"},
            content_type="application/json",
        )
        self.assertEqual(vendor_response.status_code, 200)
        vendor_id = vendor_response.json()["id"]

        rule_response = self.client.post(
            "/api/admin/settings/ticketing/vendor-sender-rules",
            data={
                "vendor_id": vendor_id,
                "match_type": "domain",
                "match_value": "@Cloudflare.com",
                "target_queue_id": self.vendor_queue.id,
                "priority": "low",
            },
            content_type="application/json",
        )

        self.assertEqual(rule_response.status_code, 200)
        rule = VendorSenderRule.objects.get(vendor_id=vendor_id)
        self.assertEqual(rule.match_value, "cloudflare.com")
        self.assertEqual(rule.target_queue, self.vendor_queue)
        self.assertEqual(rule_response.json()["vendor_name"], "Cloudflare")

    def test_duplicate_sender_rule_is_rejected(self) -> None:
        self._grant("configure_vendors")
        github = Vendor.objects.get(name="GitHub")

        response = self.client.post(
            "/api/admin/settings/ticketing/vendor-sender-rules",
            data={
                "vendor_id": github.id,
                "match_type": "domain",
                "match_value": "GITHUB.COM",
                "target_queue_id": self.vendor_queue.id,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "duplicate_sender_rule")

    def test_vendor_and_rule_can_be_disabled_without_deleting_history(self) -> None:
        self._grant("configure_vendors")
        github = Vendor.objects.get(name="GitHub")
        rule = github.sender_rules.get(match_type="domain", match_value="github.com")

        vendor_response = self.client.put(
            f"/api/admin/settings/ticketing/vendors/{github.id}/enabled",
            data={"enabled": False},
            content_type="application/json",
        )
        rule_response = self.client.put(
            f"/api/admin/settings/ticketing/vendor-sender-rules/{rule.id}/enabled",
            data={"enabled": False},
            content_type="application/json",
        )

        self.assertEqual(vendor_response.status_code, 200)
        self.assertEqual(rule_response.status_code, 200)
        github.refresh_from_db()
        rule.refresh_from_db()
        self.assertFalse(github.enabled)
        self.assertFalse(rule.enabled)

    @patch.dict("os.environ", {"TICKETING_MALWARE_SCANNING_ENABLED": "1"})
    def test_runtime_reports_malware_scanning_policy(self) -> None:
        self._grant("view_ticket")

        response = self.client.get("/api/admin/settings/ticketing/runtime")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["malware_scanning_enabled"])

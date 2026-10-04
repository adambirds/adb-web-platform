from datetime import datetime
from datetime import timezone as datetime_timezone

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.clients.models import Client
from apps.core.models import Brand
from apps.ticketing.models import Ticket, TicketQueue, Vendor, VendorSenderRule
from apps.ticketing.services.contracts import CanonicalMessage
from apps.ticketing.services.ingestion import TicketIngestionSource, ingest_source_message
from apps.ticketing.services.vendor_resolution import resolve_vendor_sender


class VendorRoutingTests(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.create(
            name="ADB Test",
            slug="adb-test",
            domain="adb-test.example.test",
        )
        self.support_queue = TicketQueue.objects.create(
            name="Support",
            key="test-support",
            brand=self.brand,
            default_priority=Ticket.Priority.NORMAL,
        )
        self.vendor_queue = TicketQueue.objects.get(key="vendors-services")
        self.vendor = Vendor.objects.create(name="Example Hosting")
        self.domain_rule = VendorSenderRule.objects.create(
            vendor=self.vendor,
            match_type=VendorSenderRule.MatchType.DOMAIN,
            match_value="ExampleVendor.test",
            target_queue=self.vendor_queue,
            priority=Ticket.Priority.LOW,
        )

    def _canonical(self, sender: str, *, provider_id: str) -> CanonicalMessage:
        return CanonicalMessage(
            provider="microsoft_graph",
            provider_message_id=provider_id,
            provider_conversation_id="conversation-id",
            internet_message_id=f"<{provider_id}@example.test>",
            in_reply_to="",
            references=(),
            sender_name="External Sender",
            sender_address=sender,
            to_recipients=("support@adb-test.example.test",),
            cc_recipients=(),
            bcc_recipients=(),
            subject="Service notification",
            body_html="",
            body_text="An external service notification.",
            sent_or_received_at=datetime(
                2026,
                8,
                19,
                1,
                0,
                tzinfo=datetime_timezone.utc,
            ),
        )

    def _source(self) -> TicketIngestionSource:
        return TicketIngestionSource(
            brand=self.brand,
            queue=self.support_queue,
            source=Ticket.Source.EMAIL,
            purpose="support",
        )

    def test_vendor_domain_routes_out_of_customer_queue(self) -> None:
        result = ingest_source_message(
            self._source(),
            self._canonical("alerts@notify.examplevendor.test", provider_id="vendor-domain"),
        )

        self.assertEqual(result.ticket.vendor, self.vendor)
        self.assertEqual(result.ticket.classification, Ticket.Classification.VENDOR)
        self.assertEqual(result.ticket.queue, self.vendor_queue)
        self.assertEqual(result.ticket.priority, Ticket.Priority.LOW)

    def test_exact_sender_rule_wins_over_domain_rule(self) -> None:
        security_queue = TicketQueue.objects.create(
            name="Operations",
            key="test-operations",
            brand=self.brand,
            default_priority=Ticket.Priority.HIGH,
        )
        security_vendor = Vendor.objects.create(name="Example Hosting Security")
        exact_rule = VendorSenderRule.objects.create(
            vendor=security_vendor,
            match_type=VendorSenderRule.MatchType.EMAIL,
            match_value="security@examplevendor.test",
            target_queue=security_queue,
            priority=Ticket.Priority.URGENT,
        )

        match = resolve_vendor_sender("SECURITY@EXAMPLEVENDOR.TEST")

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.vendor, security_vendor)
        self.assertEqual(match.rule, exact_rule)

    def test_known_client_sender_takes_precedence_over_vendor_domain(self) -> None:
        client = Client.objects.create(
            name="Known Client",
            email="person@examplevendor.test",
            status="active",
        )

        result = ingest_source_message(
            self._source(),
            self._canonical("person@examplevendor.test", provider_id="known-client"),
        )

        self.assertEqual(result.ticket.client, client)
        self.assertIsNone(result.ticket.vendor)
        self.assertEqual(result.ticket.classification, Ticket.Classification.CLIENT_SUPPORT)
        self.assertEqual(result.ticket.queue, self.support_queue)

    def test_disabled_vendor_rule_falls_back_to_normal_classification(self) -> None:
        self.domain_rule.enabled = False
        self.domain_rule.save(update_fields=["enabled"])

        result = ingest_source_message(
            self._source(),
            self._canonical("hello@examplevendor.test", provider_id="disabled-rule"),
        )

        self.assertIsNone(result.ticket.vendor)
        self.assertEqual(result.ticket.classification, Ticket.Classification.UNKNOWN)
        self.assertEqual(result.ticket.queue, self.support_queue)

    def test_seeded_vendor_rule_routes_github_messages(self) -> None:
        github = Vendor.objects.get(name="GitHub")

        result = ingest_source_message(
            self._source(),
            self._canonical("notifications@github.com", provider_id="github-seeded"),
        )

        self.assertEqual(result.ticket.vendor, github)
        self.assertEqual(result.ticket.queue, self.vendor_queue)
        self.assertEqual(result.ticket.classification, Ticket.Classification.VENDOR)

    def test_sender_rule_normalises_and_validates_match_values(self) -> None:
        rule = VendorSenderRule(
            vendor=self.vendor,
            match_type=VendorSenderRule.MatchType.DOMAIN,
            match_value="@Sub.ExampleVendor.test",
        )
        rule.full_clean()
        self.assertEqual(rule.match_value, "sub.examplevendor.test")

        invalid = VendorSenderRule(
            vendor=self.vendor,
            match_type=VendorSenderRule.MatchType.DOMAIN,
            match_value="invalid-domain",
        )
        with self.assertRaises(ValidationError):
            invalid.full_clean()

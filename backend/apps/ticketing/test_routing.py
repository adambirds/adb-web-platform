from django.test import TestCase

from apps.core.models import Brand
from apps.ticketing.models import Ticket, TicketQueue
from apps.ticketing.services.routing import route_queue_for_classification


class TicketRoutingTests(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.create(
            name="ADB Test",
            slug="adb-test",
            domain="adb-test.example.test",
        )
        self.support = TicketQueue.objects.create(
            name="Support",
            key="adb-test-support",
            brand=self.brand,
            purpose="Client support and service requests",
            ordering=10,
        )
        self.operations = TicketQueue.objects.create(
            name="Operations",
            key="adb-test-operations",
            brand=self.brand,
            purpose="Monitoring, automated messages, vendors and operational notices",
            ordering=20,
        )
        self.quarantine = TicketQueue.objects.create(
            name="Quarantine",
            key="adb-test-quarantine",
            brand=self.brand,
            purpose="Probable spam and suspicious messages",
            ordering=30,
        )

    def test_probable_spam_routes_to_quarantine(self) -> None:
        queue = route_queue_for_classification(
            self.brand,
            self.support,
            Ticket.Classification.PROBABLE_SPAM,
        )

        self.assertEqual(queue, self.quarantine)

    def test_monitoring_and_automated_messages_route_to_operations(self) -> None:
        for classification in (
            Ticket.Classification.MONITORING,
            Ticket.Classification.AUTOMATED_SYSTEM,
        ):
            with self.subTest(classification=classification):
                queue = route_queue_for_classification(
                    self.brand,
                    self.support,
                    classification,
                )
                self.assertEqual(queue, self.operations)

    def test_normal_classifications_keep_source_default_queue(self) -> None:
        for classification in (
            Ticket.Classification.CLIENT_SUPPORT,
            Ticket.Classification.SALES,
            Ticket.Classification.ACCOUNTS,
            Ticket.Classification.UNKNOWN,
        ):
            with self.subTest(classification=classification):
                queue = route_queue_for_classification(
                    self.brand,
                    self.support,
                    classification,
                )
                self.assertEqual(queue, self.support)

    def test_missing_special_queue_falls_back_to_source_default(self) -> None:
        self.quarantine.enabled = False
        self.quarantine.save(update_fields=["enabled"])

        queue = route_queue_for_classification(
            self.brand,
            self.support,
            Ticket.Classification.PROBABLE_SPAM,
        )

        self.assertEqual(queue, self.support)

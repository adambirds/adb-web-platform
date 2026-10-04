from unittest.mock import Mock, patch

from django.test import TestCase

from apps.core.models import Brand
from apps.crm.models import Lead, LeadSource
from apps.ticketing.models import Ticket, TicketMessage, TicketQueue


class WebsiteContactTicketIntegrationTests(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.create(
            name="ADB Test",
            slug="adb-test",
            domain="adb-test.example.test",
        )
        self.sales_queue = TicketQueue.objects.create(
            name="Sales",
            key="sales",
            brand=self.brand,
            purpose="sales",
        )
        self.payload = {
            "name": "Prospective Customer",
            "email": "prospect@example.com",
            "phone": "01234 567890",
            "company": "Prospect Ltd",
            "message": "We would like to discuss a new software project.",
        }

    def test_public_contact_submission_creates_lead_and_ticket(self) -> None:
        response = self.client.post(
            "/api/website/contact?brand=adb-test",
            data=self.payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        lead = Lead.objects.get()
        ticket = Ticket.objects.get()
        message = TicketMessage.objects.get()
        self.assertEqual(lead.brand, self.brand)
        self.assertEqual(ticket.brand, self.brand)
        self.assertEqual(ticket.queue, self.sales_queue)
        self.assertEqual(ticket.source, Ticket.Source.CONTACT_FORM)
        self.assertEqual(ticket.classification, Ticket.Classification.SALES)
        self.assertEqual(message.ticket, ticket)
        self.assertEqual(message.provider_message_id, f"website-contact-form:{lead.id}")

    def test_contact_submission_still_succeeds_when_ticket_queue_is_missing(self) -> None:
        self.sales_queue.delete()

        response = self.client.post(
            "/api/website/contact?brand=adb-test",
            data=self.payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(Ticket.objects.count(), 0)

    @patch(
        "apps.ticketing.signals.ingest_website_contact_lead",
        side_effect=RuntimeError("ticketing unavailable"),
    )
    def test_ticket_ingestion_failure_does_not_lose_public_lead(self, ingest: Mock) -> None:
        response = self.client.post(
            "/api/website/contact?brand=adb-test",
            data=self.payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(Ticket.objects.count(), 0)
        ingest.assert_called_once()

    def test_non_contact_form_lead_does_not_create_ticket(self) -> None:
        referral = LeadSource.objects.create(name="Referral")

        Lead.objects.create(
            brand=self.brand,
            name="Referral Lead",
            email="referral@example.test",
            source=referral,
        )

        self.assertEqual(Ticket.objects.count(), 0)

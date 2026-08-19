from django.test import TestCase

from apps.clients.models import Client, ClientContact
from apps.core.models import Brand
from apps.crm.models import Lead
from apps.ticketing.models import Ticket, TicketMessage, TicketQueue
from apps.ticketing.services.contact_forms import (
    CONTACT_FORM_PROVIDER,
    contact_form_queue_for_brand,
    ingest_website_contact_lead,
)


class WebsiteContactTicketIngestionTests(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.create(
            name="ADB Test",
            slug="adb-test",
            domain="adb-test.example.test",
        )
        self.support_queue = TicketQueue.objects.create(
            name="Support",
            key="support",
            brand=self.brand,
            purpose="support",
            ordering=1,
        )
        self.sales_queue = TicketQueue.objects.create(
            name="Sales",
            key="sales",
            brand=self.brand,
            purpose="sales",
            default_priority=Ticket.Priority.NORMAL,
            ordering=2,
        )

    def _lead(
        self,
        *,
        email: str = "prospect@example.test",
        message: str = "We would like a new website.",
    ) -> Lead:
        return Lead.objects.create(
            brand=self.brand,
            name="Prospective Customer",
            email=email,
            phone="01234 567890",
            company="Prospect Ltd",
            message=message,
        )

    def test_sales_queue_is_preferred_for_contact_forms(self) -> None:
        self.assertEqual(contact_form_queue_for_brand(self.brand), self.sales_queue)

    def test_contact_lead_creates_sales_ticket_and_normalised_message(self) -> None:
        lead = self._lead()

        result = ingest_website_contact_lead(lead)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertTrue(result.created)
        self.assertEqual(result.ticket.brand, self.brand)
        self.assertEqual(result.ticket.queue, self.sales_queue)
        self.assertIsNone(result.ticket.mailbox)
        self.assertEqual(result.ticket.source, Ticket.Source.CONTACT_FORM)
        self.assertEqual(result.ticket.classification, Ticket.Classification.SALES)
        self.assertEqual(result.ticket.status, Ticket.Status.NEW)
        self.assertEqual(result.message.provider, CONTACT_FORM_PROVIDER)
        self.assertEqual(result.message.provider_message_id, f"website-contact-form:{lead.id}")
        self.assertEqual(result.message.sender_address, "prospect@example.test")
        self.assertIn("Company: Prospect Ltd", result.message.body_text)
        self.assertIn("Phone: 01234 567890", result.message.body_text)
        self.assertIn("We would like a new website.", result.message.body_text_normalised)

    def test_contact_lead_ingestion_is_idempotent_per_lead(self) -> None:
        lead = self._lead()

        first = ingest_website_contact_lead(lead)
        second = ingest_website_contact_lead(lead)

        assert first is not None
        assert second is not None
        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(second.ticket.id, first.ticket.id)
        self.assertEqual(Ticket.objects.count(), 1)
        self.assertEqual(TicketMessage.objects.count(), 1)

    def test_known_contact_is_resolved_through_shared_sender_resolution(self) -> None:
        client = Client.objects.create(
            name="Existing Client",
            email="billing@example.test",
        )
        contact = ClientContact.objects.create(
            client=client,
            name="Existing Contact",
            email="contact@example.test",
            is_primary=True,
        )
        lead = self._lead(email="CONTACT@example.test")

        result = ingest_website_contact_lead(lead)

        assert result is not None
        self.assertEqual(result.ticket.client, client)
        self.assertEqual(result.ticket.primary_contact, contact)
        self.assertEqual(result.message.matched_contact, contact)
        self.assertEqual(result.ticket.classification, Ticket.Classification.SALES)

    def test_probable_spam_is_retained_as_low_priority_ticket(self) -> None:
        lead = self._lead(message="Guest post placements and link building packages available.")

        result = ingest_website_contact_lead(lead)

        assert result is not None
        self.assertEqual(result.ticket.classification, Ticket.Classification.PROBABLE_SPAM)
        self.assertEqual(result.ticket.priority, Ticket.Priority.LOW)
        self.assertEqual(result.ticket.status, Ticket.Status.NEW)

    def test_missing_ticket_queue_does_not_create_partial_ticket(self) -> None:
        self.sales_queue.delete()
        self.support_queue.delete()
        lead = self._lead()

        result = ingest_website_contact_lead(lead)

        self.assertIsNone(result)
        self.assertEqual(Ticket.objects.count(), 0)
        self.assertEqual(TicketMessage.objects.count(), 0)

from typing import Any, cast
from unittest.mock import patch

from django.http import HttpRequest
from django.test import RequestFactory, TestCase

from apps.clients.models import Client
from apps.core.models import Brand
from apps.credentials.models import StoredCredential
from apps.crm.models import Lead
from apps.crm.ninja.email_schemas import LeadEmailIn, LeadEmailOptionsOut, LeadEmailOut
from apps.crm.ninja.email_views import email_lead, lead_conversations, lead_email_options
from apps.crm.ninja.schemas import LeadTicketOut
from apps.crm.services import convert_lead
from apps.ticketing.models import (
    Mailbox,
    MicrosoftGraphConnection,
    Ticket,
    TicketMessage,
    TicketQueue,
)
from authentication.models import User


class LeadEmailApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            email="lead-email@example.com",
            password="test-password",
            first_name="Lead",
            last_name="Mailer",
        )
        self.brand = Brand.objects.create(
            name="ADB Software Solutions",
            slug="adb-software-solutions-test",
            domain="software-test.example.com",
        )
        self.queue = TicketQueue.objects.create(
            name="Sales",
            key="sales-test",
            brand=self.brand,
            default_priority="normal",
        )
        credential = StoredCredential.objects.create(name="Graph test credential")
        connection = MicrosoftGraphConnection.objects.create(
            name="Graph test",
            tenant_id="tenant-test",
            client_id="client-test",
            authentication_method=MicrosoftGraphConnection.AuthenticationMethod.CERTIFICATE,
            credential=credential,
        )
        self.mailbox = Mailbox.objects.create(
            graph_connection=connection,
            email_address="enquiries@example.com",
            display_name="ADB Enquiries",
            brand=self.brand,
            purpose=Mailbox.Purpose.SALES,
            default_queue=self.queue,
        )
        self.lead = Lead.objects.create(
            brand=self.brand,
            name="Prospective Customer",
            company="Prospect Ltd",
            email="prospect@example.com",
            message="Please tell me about a new software project.",
        )

    def _request(self, method: str = "get") -> HttpRequest:
        request = getattr(self.factory, method)(f"/api/admin/leads/{self.lead.id}/email")
        request.user = self.user
        return request

    def test_email_options_prefer_available_brand_mailbox(self) -> None:
        result = lead_email_options(self._request(), self.lead.id)
        options = cast(LeadEmailOptionsOut, result)

        self.assertTrue(options.can_email)
        self.assertEqual(len(options.mailboxes), 1)
        self.assertEqual(options.mailboxes[0].id, self.mailbox.id)
        self.assertEqual(options.mailboxes[0].purpose, Mailbox.Purpose.SALES)

    @patch("apps.crm.ninja.email_views.deliver_lead_email_task.delay")
    def test_email_lead_creates_auditable_sales_conversation(self, delay: Any) -> None:
        result = email_lead(
            self._request("post"),
            self.lead.id,
            LeadEmailIn(
                mailbox_id=self.mailbox.id,
                subject="Your software enquiry",
                body_text="Thanks for getting in touch.",
            ),
        )

        self.assertIsInstance(result, tuple)
        status, payload = result
        self.assertEqual(status, 202)
        detail = cast(LeadEmailOut, payload)
        ticket = Ticket.objects.get(id=detail.ticket_id)
        message = TicketMessage.objects.get(id=detail.message_id)
        self.assertEqual(ticket.classification, Ticket.Classification.SALES)
        self.assertEqual(ticket.source, Ticket.Source.MANUAL)
        self.assertEqual(ticket.mailbox, self.mailbox)
        self.assertEqual(message.to_recipients, [self.lead.email])
        self.assertEqual(message.delivery_status, "queued")
        delay.assert_called_once_with(message.id)

        conversations = cast(
            list[LeadTicketOut],
            lead_conversations(self._request(), self.lead.id),
        )
        self.assertEqual(len(conversations), 1)
        self.assertEqual(conversations[0].id, ticket.id)

        conversion = convert_lead(self.lead, self.user)
        ticket.refresh_from_db()
        self.assertEqual(conversion.linked_ticket_count, 1)
        self.assertIsInstance(ticket.client, Client)
        self.assertEqual(ticket.client, conversion.client)

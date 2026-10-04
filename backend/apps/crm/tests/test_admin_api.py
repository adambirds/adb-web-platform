from typing import Any, cast

from django.contrib.auth.models import Permission
from django.http import HttpRequest
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.clients.models import Client, ClientContact
from apps.core.models import Brand
from apps.crm.models import Lead, LeadSource, LeadStatus
from apps.crm.ninja.admin_views import (
    convert_lead_to_client,
    create_lead,
    get_lead,
    update_lead,
    update_lead_assignment,
)
from apps.crm.ninja.schemas import LeadAssignmentIn, LeadConversionOut, LeadDetailOut, LeadIn
from apps.ticketing.models import Ticket, TicketMessage, TicketQueue
from authentication.models import User


class LeadAdminApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="test-password",
            first_name="Admin",
            last_name="User",
        )
        self.brand = Brand.objects.get(slug="adb-software-solutions")
        self.status = LeadStatus.objects.create(name="Qualified", order=20)
        self.source = LeadSource.objects.create(name="Referral")

    def _request(self, user: User, method: str = "post") -> HttpRequest:
        request = getattr(self.factory, method)("/api/admin/leads")
        request.user = user
        return request

    def _payload(self, **overrides: Any) -> LeadIn:
        values: dict[str, Any] = {
            "name": "Jane Prospect",
            "email": "JANE@EXAMPLE.COM",
            "phone": "0161 555 0100",
            "company": "Example Prospect Ltd",
            "brand_id": self.brand.id,
            "status_id": self.status.id,
            "source_id": self.source.id,
            "message": "We need a new internal platform.",
            "notes": "Follow up next week.",
        }
        values.update(overrides)
        return LeadIn(**values)

    def _staff_user(self, email: str) -> User:
        return User.objects.create_user(
            email=email,
            password="test-password",
            first_name="Staff",
            last_name="User",
            is_staff=True,
        )

    def _grant_permission(self, user: User, app_label: str, codename: str) -> None:
        permission = Permission.objects.get(
            content_type__app_label=app_label,
            codename=codename,
        )
        user.user_permissions.add(permission)

    def _staff_with_permission(self, codename: str) -> User:
        user = self._staff_user(f"{codename}@example.com")
        self._grant_permission(user, "crm", codename)
        return user

    def test_superuser_can_create_and_update_lead(self) -> None:
        result = create_lead(self._request(self.superuser), self._payload())

        self.assertIsInstance(result, tuple)
        status_code, created = result
        self.assertEqual(status_code, 201)
        detail = cast(LeadDetailOut, created)
        lead = Lead.objects.get(id=detail.id)
        self.assertEqual(lead.email, "jane@example.com")
        self.assertEqual(lead.brand, self.brand)
        self.assertEqual(lead.status, self.status)
        self.assertEqual(lead.source, self.source)

        update_result = update_lead(
            self._request(self.superuser, "put"),
            lead.id,
            self._payload(company="Example Group", notes="Proposal sent."),
        )

        self.assertIsInstance(update_result, LeadDetailOut)
        lead.refresh_from_db()
        self.assertEqual(lead.company, "Example Group")
        self.assertEqual(lead.notes, "Proposal sent.")

    def test_unknown_lookup_is_rejected_without_saving(self) -> None:
        result = create_lead(
            self._request(self.superuser),
            self._payload(status_id=999999),
        )

        self.assertIsInstance(result, tuple)
        status_code, problem = cast(tuple[int, dict[str, Any]], result)
        self.assertEqual(status_code, 404)
        self.assertEqual(problem["code"], "not_found")
        self.assertEqual(Lead.objects.count(), 0)

    def test_related_email_ticket_is_exposed_on_lead_detail(self) -> None:
        lead = Lead.objects.create(
            name="Jane Prospect",
            email="jane@example.com",
            brand=self.brand,
            status=self.status,
            source=self.source,
        )
        queue = TicketQueue.objects.create(
            name="Lead Test Sales",
            key="lead-test-sales",
            brand=self.brand,
            purpose="Sales enquiries",
        )
        now = timezone.now()
        ticket = Ticket.objects.create(
            brand=self.brand,
            queue=queue,
            subject="Website project enquiry",
            classification=Ticket.Classification.SALES,
            source=Ticket.Source.CONTACT_FORM,
            last_message_at=now,
        )
        TicketMessage.objects.create(
            ticket=ticket,
            direction=TicketMessage.Direction.INBOUND,
            sender_name="Jane Prospect",
            sender_address="jane@example.com",
            subject=ticket.subject,
            body_text="Can you help with our website?",
            sent_or_received_at=now,
        )

        result = get_lead(self._request(self.superuser, "get"), lead.id)

        self.assertIsInstance(result, LeadDetailOut)
        detail = cast(LeadDetailOut, result)
        self.assertEqual([row.id for row in detail.related_tickets], [ticket.id])

    def test_staff_without_change_permission_cannot_update_lead(self) -> None:
        user = self._staff_with_permission("view_lead")
        lead = Lead.objects.create(name="Restricted Lead", email="lead@example.com")

        result = update_lead(
            self._request(user, "put"),
            lead.id,
            self._payload(email="lead@example.com"),
        )

        self.assertIsInstance(result, tuple)
        status_code, problem = cast(tuple[int, dict[str, Any]], result)
        self.assertEqual(status_code, 403)
        self.assertEqual(problem["code"], "forbidden")

    def test_superuser_can_assign_lead_to_staff_with_lead_access(self) -> None:
        lead = Lead.objects.create(name="Assign Me", email="assign@example.com")
        assignee = self._staff_user("sales@example.com")
        self._grant_permission(assignee, "crm", "view_lead")

        result = update_lead_assignment(
            self._request(self.superuser),
            lead.id,
            LeadAssignmentIn(assigned_to_id=assignee.id),
        )

        self.assertIsInstance(result, LeadDetailOut)
        lead.refresh_from_db()
        self.assertEqual(lead.assigned_to, assignee)
        self.assertEqual(cast(LeadDetailOut, result).assigned_to_name, "Staff User")

    def test_assignment_rejects_staff_without_lead_access(self) -> None:
        lead = Lead.objects.create(name="Assign Me", email="assign@example.com")
        assignee = self._staff_user("no-access@example.com")

        result = update_lead_assignment(
            self._request(self.superuser),
            lead.id,
            LeadAssignmentIn(assigned_to_id=assignee.id),
        )

        self.assertIsInstance(result, tuple)
        status_code, problem = cast(tuple[int, dict[str, Any]], result)
        self.assertEqual(status_code, 400)
        self.assertEqual(problem["code"], "assignee_unavailable")

    def test_conversion_creates_client_contact_and_relinks_unmatched_history(self) -> None:
        lead = Lead.objects.create(
            name="Jane Prospect",
            email="jane@example.com",
            phone="0161 555 0100",
            company="Example Prospect Ltd",
            brand=self.brand,
            status=self.status,
            source=self.source,
            notes="Commercial notes.",
        )
        queue = TicketQueue.objects.create(
            name="Lead Conversion Sales",
            key="lead-conversion-sales",
            brand=self.brand,
            purpose="Sales enquiries",
        )
        now = timezone.now()
        ticket = Ticket.objects.create(
            brand=self.brand,
            queue=queue,
            subject="Convert this conversation",
            classification=Ticket.Classification.SALES,
            source=Ticket.Source.EMAIL,
            last_message_at=now,
        )
        message = TicketMessage.objects.create(
            ticket=ticket,
            direction=TicketMessage.Direction.INBOUND,
            sender_name=lead.name,
            sender_address=lead.email,
            subject=ticket.subject,
            body_text="Please proceed.",
            sent_or_received_at=now,
        )
        existing_client = Client.objects.create(
            name="Existing Customer",
            email="existing@example.com",
        )
        protected_ticket = Ticket.objects.create(
            brand=self.brand,
            queue=queue,
            client=existing_client,
            subject="Already owned conversation",
            classification=Ticket.Classification.SALES,
            source=Ticket.Source.EMAIL,
            last_message_at=now,
        )
        TicketMessage.objects.create(
            ticket=protected_ticket,
            direction=TicketMessage.Direction.INBOUND,
            sender_name=lead.name,
            sender_address=lead.email,
            subject=protected_ticket.subject,
            body_text="Do not reassign this client ticket.",
            sent_or_received_at=now,
        )

        result = convert_lead_to_client(self._request(self.superuser), lead.id)

        self.assertIsInstance(result, LeadConversionOut)
        conversion = cast(LeadConversionOut, result)
        self.assertEqual(conversion.linked_ticket_count, 1)

        lead.refresh_from_db()
        self.assertIsNotNone(lead.converted_at)
        self.assertEqual(lead.converted_by, self.superuser)
        self.assertEqual(lead.converted_client_id, conversion.client_id)
        self.assertEqual(lead.converted_contact_id, conversion.contact_id)

        client = Client.objects.get(id=conversion.client_id)
        contact = ClientContact.objects.get(id=conversion.contact_id)
        self.assertEqual(client.company, lead.company)
        self.assertEqual(client.email, lead.email)
        self.assertEqual(client.notes, lead.notes)
        self.assertEqual(contact.client, client)
        self.assertEqual(contact.email, lead.email)
        self.assertTrue(contact.is_primary)

        ticket.refresh_from_db()
        message.refresh_from_db()
        protected_ticket.refresh_from_db()
        self.assertEqual(ticket.client, client)
        self.assertEqual(ticket.primary_contact, contact)
        self.assertEqual(message.matched_contact, contact)
        self.assertEqual(protected_ticket.client, existing_client)

        second_result = convert_lead_to_client(self._request(self.superuser), lead.id)
        self.assertIsInstance(second_result, tuple)
        status_code, problem = cast(tuple[int, dict[str, Any]], second_result)
        self.assertEqual(status_code, 400)
        self.assertEqual(problem["code"], "conversion_invalid")

    def test_conversion_requires_client_creation_permissions(self) -> None:
        user = self._staff_user("converter@example.com")
        self._grant_permission(user, "crm", "convert_lead")
        lead = Lead.objects.create(name="Prospect", email="prospect@example.com")

        result = convert_lead_to_client(self._request(user), lead.id)

        self.assertIsInstance(result, tuple)
        status_code, problem = cast(tuple[int, dict[str, Any]], result)
        self.assertEqual(status_code, 403)
        self.assertEqual(problem["code"], "forbidden")
        self.assertIsNone(lead.converted_at)

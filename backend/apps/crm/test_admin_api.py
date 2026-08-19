from typing import Any, cast

from django.contrib.auth.models import Permission
from django.http import HttpRequest
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.core.models import Brand
from apps.crm.models import Lead, LeadSource, LeadStatus
from apps.crm.ninja.admin_views import create_lead, get_lead, update_lead
from apps.crm.ninja.schemas import LeadDetailOut, LeadIn
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
        self.brand = Brand.objects.create(
            name="ADB Software Solutions",
            slug="adb-software-solutions",
            domain="adbsoftwaresolutions.co.uk",
        )
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

    def _staff_with_permission(self, codename: str) -> User:
        user = User.objects.create_user(
            email=f"{codename}@example.com",
            password="test-password",
            first_name="Staff",
            last_name="User",
            is_staff=True,
        )
        permission = Permission.objects.get(
            content_type__app_label="crm",
            codename=codename,
        )
        user.user_permissions.add(permission)
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
            name="Sales",
            key="sales",
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

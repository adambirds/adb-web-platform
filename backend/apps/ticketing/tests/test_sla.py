from __future__ import annotations

from datetime import timedelta

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone

from apps.access_control.models import StaffAccessProfile
from apps.clients.models import Client
from apps.core.models import Brand
from apps.ticketing.models import Ticket, TicketQueue
from apps.ticketing.services.operations import move_ticket_queue
from apps.ticketing.services.sla import evaluate_ticket_sla
from authentication.models import User


class TicketSLATests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="sla@example.test",
            password="test-password",
            first_name="SLA",
            last_name="User",
            is_staff=True,
        )
        self.client_record = Client.objects.create(
            name="Allowed",
            company="Allowed Ltd",
            email="allowed@example.test",
        )
        self.hidden_client = Client.objects.create(
            name="Hidden",
            company="Hidden Ltd",
            email="hidden@example.test",
        )
        self.brand = Brand.objects.create(
            name="SLA Brand",
            slug="sla-brand",
            domain="sla.example.test",
        )
        self.queue = TicketQueue.objects.create(
            name="Support",
            key="sla-support",
            brand=self.brand,
            first_response_sla_minutes=60,
            resolution_sla_minutes=240,
        )
        self.hidden_queue = TicketQueue.objects.create(
            name="Hidden",
            key="sla-hidden",
            brand=self.brand,
            first_response_sla_minutes=30,
            resolution_sla_minutes=120,
        )
        profile = StaffAccessProfile.objects.create(user=self.user)
        profile.client_grants.create(client=self.client_record)
        profile.ticket_queue_grants.create(queue=self.queue)
        self.client.force_login(self.user)

    def _grant(self, codename: str) -> None:
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="ticketing",
                codename=codename,
            )
        )

    def _ticket(self, **overrides: object) -> Ticket:
        values: dict[str, object] = {
            "brand": self.brand,
            "queue": self.queue,
            "client": self.client_record,
            "subject": "SLA ticket",
            "source": Ticket.Source.MANUAL,
        }
        values.update(overrides)
        return Ticket.objects.create(**values)

    def test_new_ticket_receives_queue_deadlines(self) -> None:
        ticket = self._ticket()

        self.assertIsNotNone(ticket.first_response_due_at)
        self.assertIsNotNone(ticket.resolution_due_at)
        assert ticket.first_response_due_at is not None
        assert ticket.resolution_due_at is not None
        self.assertLess(ticket.first_response_due_at, ticket.resolution_due_at)

    def test_waiting_customer_suppresses_active_escalation(self) -> None:
        ticket = self._ticket(status=Ticket.Status.WAITING_CUSTOMER)
        now = timezone.now()
        ticket.first_response_due_at = now - timedelta(hours=1)
        ticket.resolution_due_at = now - timedelta(minutes=30)
        ticket.save(update_fields=["first_response_due_at", "resolution_due_at"])

        health = evaluate_ticket_sla(ticket, now=now)

        self.assertEqual(health.overall_status, "waiting_customer")
        self.assertEqual(health.severity, "info")
        self.assertEqual(health.first_response_status, "breached")

    def test_queue_move_restarts_unmet_deadlines_from_destination_policy(self) -> None:
        destination = TicketQueue.objects.create(
            name="Escalations",
            key="sla-escalations",
            brand=self.brand,
            first_response_sla_minutes=15,
            resolution_sla_minutes=60,
        )
        ticket = self._ticket()
        before = timezone.now()

        move_ticket_queue(ticket, destination)
        ticket.refresh_from_db()

        assert ticket.first_response_due_at is not None
        assert ticket.resolution_due_at is not None
        self.assertGreaterEqual(ticket.first_response_due_at, before + timedelta(minutes=14))
        self.assertGreaterEqual(ticket.resolution_due_at, before + timedelta(minutes=59))

    def test_sla_list_obeys_queue_and_client_scope(self) -> None:
        self._grant("view_ticket")
        visible = self._ticket(subject="Visible breached ticket")
        visible.first_response_due_at = timezone.now() - timedelta(minutes=5)
        visible.save(update_fields=["first_response_due_at"])
        hidden_queue_ticket = Ticket.objects.create(
            brand=self.brand,
            queue=self.hidden_queue,
            client=self.client_record,
            subject="Hidden queue ticket",
            source=Ticket.Source.MANUAL,
        )
        hidden_queue_ticket.first_response_due_at = timezone.now() - timedelta(minutes=5)
        hidden_queue_ticket.save(update_fields=["first_response_due_at"])
        hidden_client_ticket = Ticket.objects.create(
            brand=self.brand,
            queue=self.queue,
            client=self.hidden_client,
            subject="Hidden client ticket",
            source=Ticket.Source.MANUAL,
        )
        hidden_client_ticket.first_response_due_at = timezone.now() - timedelta(minutes=5)
        hidden_client_ticket.save(update_fields=["first_response_due_at"])

        response = self.client.get("/api/admin/ticket-sla")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["ticket_id"] for item in response.json()["items"]],
            [visible.id],
        )

    def test_queue_sla_configuration_requires_configuration_permission(self) -> None:
        self._grant("view_ticketqueue")
        denied = self.client.put(
            f"/api/admin/ticket-queues/{self.queue.id}/sla",
            data={"first_response_sla_minutes": 45, "resolution_sla_minutes": 180},
            content_type="application/json",
        )
        self.assertEqual(denied.status_code, 403)

        self._grant("configure_ticket_queues")
        allowed = self.client.put(
            f"/api/admin/ticket-queues/{self.queue.id}/sla",
            data={"first_response_sla_minutes": 45, "resolution_sla_minutes": 180},
            content_type="application/json",
        )

        self.assertEqual(allowed.status_code, 200)
        self.queue.refresh_from_db()
        self.assertEqual(self.queue.first_response_sla_minutes, 45)
        self.assertEqual(self.queue.resolution_sla_minutes, 180)

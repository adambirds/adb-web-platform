from typing import cast

from django.http import HttpRequest
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.core.models import Brand
from apps.ticketing.models import Ticket, TicketQueue
from apps.ticketing.ninja.focus_schemas import (
    TicketFocusPageOut,
    TicketQueuePreferencesIn,
    TicketQueuePreferencesOut,
)
from apps.ticketing.ninja.focus_views import ticket_focus, update_ticket_queue_preferences
from authentication.models import User


class TicketFocusApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            email="ticket-focus@example.com",
            password="test-password",
            first_name="Ticket",
            last_name="Owner",
        )
        self.brand = Brand.objects.create(
            name="Ticket Focus Brand",
            slug="ticket-focus-brand",
            domain="ticket-focus.example.com",
        )
        self.support = TicketQueue.objects.create(
            name="Support",
            key="ticket-focus-support",
            brand=self.brand,
            ordering=10,
        )
        self.sales = TicketQueue.objects.create(
            name="Sales",
            key="ticket-focus-sales",
            brand=self.brand,
            ordering=20,
        )
        self.disabled = TicketQueue.objects.create(
            name="Old Queue",
            key="ticket-focus-old",
            brand=self.brand,
            enabled=False,
            ordering=30,
        )

    def _request(self, method: str = "get") -> HttpRequest:
        request = getattr(self.factory, method)("/api/admin/ticket-focus")
        request.user = self.user
        return request

    def _ticket(
        self,
        subject: str,
        *,
        queue: TicketQueue | None = None,
        status: str = Ticket.Status.OPEN,
        priority: str = Ticket.Priority.NORMAL,
        assigned: bool = True,
    ) -> Ticket:
        return Ticket.objects.create(
            brand=self.brand,
            queue=queue or self.support,
            subject=subject,
            status=status,
            priority=priority,
            assigned_to=self.user if assigned else None,
            last_message_at=timezone.now(),
        )

    def test_default_view_is_my_actionable_work_and_waiting_customer_sorts_lower(self) -> None:
        new_ticket = self._ticket(
            "New request",
            status=Ticket.Status.NEW,
            priority=Ticket.Priority.NORMAL,
        )
        open_ticket = self._ticket(
            "Open urgent request",
            status=Ticket.Status.OPEN,
            priority=Ticket.Priority.URGENT,
        )
        waiting_ticket = self._ticket(
            "Waiting on customer",
            status=Ticket.Status.WAITING_CUSTOMER,
            priority=Ticket.Priority.URGENT,
        )
        self._ticket("Resolved history", status=Ticket.Status.RESOLVED)
        self._ticket("Someone needs to claim this", assigned=False)

        result = cast(TicketFocusPageOut, ticket_focus(self._request()))

        self.assertEqual(
            [item.id for item in result.items],
            [new_ticket.id, open_ticket.id, waiting_ticket.id],
        )
        self.assertEqual(result.counts.mine, 3)
        self.assertEqual(result.counts.unassigned, 1)
        self.assertEqual(result.counts.active, 4)
        self.assertEqual(result.counts.waiting_customer, 1)

        queue_ids = {queue.id for queue in result.queues}
        self.assertIn(self.support.id, queue_ids)
        self.assertIn(self.sales.id, queue_ids)
        self.assertNotIn(self.disabled.id, queue_ids)
        self.assertTrue(all(queue.is_default for queue in result.queues))

    def test_resolved_tickets_only_appear_when_history_view_is_requested(self) -> None:
        self._ticket("Current work")
        resolved = self._ticket("Resolved work", status=Ticket.Status.RESOLVED)

        current = cast(TicketFocusPageOut, ticket_focus(self._request()))
        history = cast(TicketFocusPageOut, ticket_focus(self._request(), view="resolved"))

        self.assertNotIn(resolved.id, [item.id for item in current.items])
        self.assertEqual([item.id for item in history.items], [resolved.id])

    def test_default_queue_preferences_scope_the_main_work_queue(self) -> None:
        support_ticket = self._ticket("Support work", queue=self.support)
        self._ticket("Sales work", queue=self.sales)

        preference_result = update_ticket_queue_preferences(
            self._request("put"),
            TicketQueuePreferencesIn(queue_ids=[self.support.id]),
        )
        preferences = cast(TicketQueuePreferencesOut, preference_result)
        self.assertEqual(preferences.queue_ids, [self.support.id])
        self.assertFalse(preferences.uses_all_accessible_queues)

        result = cast(TicketFocusPageOut, ticket_focus(self._request()))
        self.assertEqual([item.id for item in result.items], [support_ticket.id])
        self.assertTrue(
            next(queue for queue in result.queues if queue.id == self.support.id).is_default
        )
        self.assertFalse(
            next(queue for queue in result.queues if queue.id == self.sales.id).is_default
        )

        accessible_queue_ids = list(
            TicketQueue.objects.filter(enabled=True)
            .order_by("ordering", "name")
            .values_list("id", flat=True)
        )
        all_result = update_ticket_queue_preferences(
            self._request("put"),
            TicketQueuePreferencesIn(queue_ids=accessible_queue_ids),
        )
        all_preferences = cast(TicketQueuePreferencesOut, all_result)
        self.assertTrue(all_preferences.uses_all_accessible_queues)
        self.assertEqual(all_preferences.queue_ids, accessible_queue_ids)

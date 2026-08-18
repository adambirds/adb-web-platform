from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile, TicketQueueAccessGrant
from apps.clients.models import Client
from apps.core.models import Brand
from apps.ticketing.models import Ticket, TicketQueue
from authentication.models import User


class TicketOperationsApiTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="operator@example.test",
            password="not-a-real-password",
            first_name="Ticket",
            last_name="Operator",
            is_staff=True,
        )
        self.profile = StaffAccessProfile.objects.create(user=self.user)
        self.brand = Brand.objects.create(
            name="ADB Test",
            slug="adb-test",
            domain="adb-test.example.test",
        )
        self.other_brand = Brand.objects.create(
            name="Other Brand",
            slug="other-brand",
            domain="other.example.test",
        )
        self.client_account = Client.objects.create(
            name="Client A",
            email="client@example.test",
        )
        self.queue = TicketQueue.objects.create(
            name="Support",
            key="support",
            brand=self.brand,
            ordering=1,
        )
        self.second_queue = TicketQueue.objects.create(
            name="Escalations",
            key="escalations",
            brand=self.brand,
            ordering=2,
        )
        self.other_brand_queue = TicketQueue.objects.create(
            name="Other Support",
            key="other-support",
            brand=self.other_brand,
            ordering=3,
        )
        self.ticket = Ticket.objects.create(
            brand=self.brand,
            queue=self.queue,
            client=self.client_account,
            subject="Website issue",
            last_message_at=timezone.now(),
        )

        ClientAccessGrant.objects.create(profile=self.profile, client=self.client_account)
        for queue in (self.queue, self.second_queue, self.other_brand_queue):
            TicketQueueAccessGrant.objects.create(profile=self.profile, queue=queue)
        self._grant(
            self.user,
            "view_ticket",
            "change_ticket",
            "assign_ticket",
            "close_ticket",
        )

        self.agent = User.objects.create_user(
            email="agent@example.test",
            password="not-a-real-password",
            first_name="Support",
            last_name="Agent",
            is_staff=True,
        )
        agent_profile = StaffAccessProfile.objects.create(user=self.agent)
        ClientAccessGrant.objects.create(profile=agent_profile, client=self.client_account)
        TicketQueueAccessGrant.objects.create(profile=agent_profile, queue=self.queue)
        self._grant(self.agent, "view_ticket")

        self.outsider = User.objects.create_user(
            email="outsider@example.test",
            password="not-a-real-password",
            first_name="Outside",
            last_name="Agent",
            is_staff=True,
        )
        StaffAccessProfile.objects.create(user=self.outsider)
        self._grant(self.outsider, "view_ticket")

        self.client.force_login(self.user)

    def _grant(self, user: User, *codenames: str) -> None:
        permissions = Permission.objects.filter(
            content_type__app_label="ticketing",
            codename__in=codenames,
        )
        user.user_permissions.add(*permissions)

    def test_operation_options_only_expose_valid_targets(self) -> None:
        response = self.client.get(f"/api/admin/tickets/{self.ticket.id}/operations")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["can_assign"])
        self.assertTrue(payload["can_change"])
        self.assertTrue(payload["can_close"])
        self.assertEqual(
            {queue["id"] for queue in payload["queues"]},
            {self.queue.id, self.second_queue.id},
        )
        assignee_ids = {agent["id"] for agent in payload["assignees"]}
        self.assertIn(str(self.agent.id), assignee_ids)
        self.assertNotIn(str(self.outsider.id), assignee_ids)
        status_values = {status["value"] for status in payload["statuses"]}
        self.assertIn(Ticket.Status.RESOLVED, status_values)
        self.assertIn(Ticket.Status.CLOSED, status_values)

    def test_assignment_requires_target_ticket_access(self) -> None:
        response = self.client.post(
            f"/api/admin/tickets/{self.ticket.id}/assignment",
            data={"assigned_to_id": str(self.agent.id)},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["assigned_to_id"], str(self.agent.id))
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assigned_to, self.agent)

        rejected = self.client.post(
            f"/api/admin/tickets/{self.ticket.id}/assignment",
            data={"assigned_to_id": str(self.outsider.id)},
            content_type="application/json",
        )
        self.assertEqual(rejected.status_code, 400)
        self.assertEqual(rejected.json()["code"], "assignee_unavailable")

        unassigned = self.client.post(
            f"/api/admin/tickets/{self.ticket.id}/assignment",
            data={"assigned_to_id": None},
            content_type="application/json",
        )
        self.assertEqual(unassigned.status_code, 200)
        self.assertIsNone(unassigned.json()["assigned_to_id"])

    def test_priority_and_queue_changes_are_validated(self) -> None:
        priority_response = self.client.post(
            f"/api/admin/tickets/{self.ticket.id}/priority",
            data={"priority": Ticket.Priority.URGENT},
            content_type="application/json",
        )
        self.assertEqual(priority_response.status_code, 200)
        self.assertEqual(priority_response.json()["priority"], Ticket.Priority.URGENT)

        invalid_priority = self.client.post(
            f"/api/admin/tickets/{self.ticket.id}/priority",
            data={"priority": "critical"},
            content_type="application/json",
        )
        self.assertEqual(invalid_priority.status_code, 400)
        self.assertEqual(invalid_priority.json()["code"], "priority_invalid")

        queue_response = self.client.post(
            f"/api/admin/tickets/{self.ticket.id}/queue",
            data={"queue_id": self.second_queue.id},
            content_type="application/json",
        )
        self.assertEqual(queue_response.status_code, 200)
        self.assertEqual(queue_response.json()["queue_id"], self.second_queue.id)

        wrong_brand = self.client.post(
            f"/api/admin/tickets/{self.ticket.id}/queue",
            data={"queue_id": self.other_brand_queue.id},
            content_type="application/json",
        )
        self.assertEqual(wrong_brand.status_code, 400)
        self.assertEqual(wrong_brand.json()["code"], "queue_invalid")

    def test_resolve_close_and_reopen_keep_timestamps_consistent(self) -> None:
        resolved = self.client.post(
            f"/api/admin/tickets/{self.ticket.id}/status",
            data={"status": Ticket.Status.RESOLVED},
            content_type="application/json",
        )
        self.assertEqual(resolved.status_code, 200)
        self.assertIsNotNone(resolved.json()["resolved_at"])
        self.assertIsNone(resolved.json()["closed_at"])

        closed = self.client.post(
            f"/api/admin/tickets/{self.ticket.id}/status",
            data={"status": Ticket.Status.CLOSED},
            content_type="application/json",
        )
        self.assertEqual(closed.status_code, 200)
        self.assertIsNotNone(closed.json()["resolved_at"])
        self.assertIsNotNone(closed.json()["closed_at"])

        reopened = self.client.post(
            f"/api/admin/tickets/{self.ticket.id}/status",
            data={"status": Ticket.Status.OPEN},
            content_type="application/json",
        )
        self.assertEqual(reopened.status_code, 200)
        self.assertEqual(reopened.json()["status"], Ticket.Status.OPEN)
        self.assertIsNone(reopened.json()["resolved_at"])
        self.assertIsNone(reopened.json()["closed_at"])

    def test_close_capability_is_separate_from_general_changes(self) -> None:
        self.user.user_permissions.remove(
            Permission.objects.get(
                content_type__app_label="ticketing",
                codename="close_ticket",
            )
        )

        waiting = self.client.post(
            f"/api/admin/tickets/{self.ticket.id}/status",
            data={"status": Ticket.Status.WAITING_INTERNAL},
            content_type="application/json",
        )
        self.assertEqual(waiting.status_code, 200)

        resolved = self.client.post(
            f"/api/admin/tickets/{self.ticket.id}/status",
            data={"status": Ticket.Status.RESOLVED},
            content_type="application/json",
        )
        self.assertEqual(resolved.status_code, 403)

    def test_general_change_capability_is_required_for_priority(self) -> None:
        self.user.user_permissions.remove(
            Permission.objects.get(
                content_type__app_label="ticketing",
                codename="change_ticket",
            )
        )

        response = self.client.post(
            f"/api/admin/tickets/{self.ticket.id}/priority",
            data={"priority": Ticket.Priority.HIGH},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

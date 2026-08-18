from django.test import TestCase

from apps.access_control.models import (
    ClientAccessGrant,
    StaffAccessProfile,
    TicketQueueAccessGrant,
)
from apps.access_control.policies import (
    can_access_client,
    can_access_ticket_queue,
    scope_clients_for_user,
    scope_ticket_queues_for_user,
)
from apps.clients.models import Client
from apps.core.models import Brand
from apps.ticketing.models import TicketQueue
from authentication.models import User


class ClientAccessPolicyTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="staff@example.com",
            password="not-a-real-password",
            first_name="Staff",
            last_name="User",
            is_staff=True,
        )
        self.profile = StaffAccessProfile.objects.create(user=self.user)
        self.allowed_client = Client.objects.create(
            name="Allowed",
            company="Allowed Ltd",
            email="allowed@example.com",
        )
        self.denied_client = Client.objects.create(
            name="Denied",
            company="Denied Ltd",
            email="denied@example.com",
        )
        ClientAccessGrant.objects.create(
            profile=self.profile,
            client=self.allowed_client,
            granted_by=self.user,
        )

    def test_selected_client_grant_limits_scope(self) -> None:
        self.assertTrue(can_access_client(self.user, self.allowed_client))
        self.assertFalse(can_access_client(self.user, self.denied_client))
        self.assertQuerySetEqual(
            scope_clients_for_user(self.user),
            [self.allowed_client],
            transform=lambda client: client,
        )

    def test_all_clients_scope_allows_every_client(self) -> None:
        self.profile.all_clients = True
        self.profile.save(update_fields=["all_clients"])

        self.assertTrue(can_access_client(self.user, self.allowed_client))
        self.assertTrue(can_access_client(self.user, self.denied_client))
        self.assertEqual(scope_clients_for_user(self.user).count(), 2)

    def test_superuser_bypasses_object_scope(self) -> None:
        superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="not-a-real-password",
            first_name="Admin",
            last_name="User",
        )

        self.assertTrue(can_access_client(superuser, self.denied_client))
        self.assertEqual(scope_clients_for_user(superuser).count(), 2)


class TicketQueueAccessPolicyTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="ticket-agent@example.com",
            password="not-a-real-password",
            first_name="Ticket",
            last_name="Agent",
            is_staff=True,
        )
        self.profile = StaffAccessProfile.objects.create(user=self.user)
        self.brand = Brand.objects.create(
            name="ADB Test",
            slug="adb-test",
            domain="adb-test.example.test",
        )
        self.allowed_queue = TicketQueue.objects.create(
            name="Support",
            key="support",
            brand=self.brand,
        )
        self.denied_queue = TicketQueue.objects.create(
            name="Accounts",
            key="accounts",
            brand=self.brand,
        )
        TicketQueueAccessGrant.objects.create(
            profile=self.profile,
            queue=self.allowed_queue,
            granted_by=self.user,
        )

    def test_selected_queue_grant_limits_scope(self) -> None:
        self.assertTrue(can_access_ticket_queue(self.user, self.allowed_queue))
        self.assertFalse(can_access_ticket_queue(self.user, self.denied_queue))
        self.assertQuerySetEqual(
            scope_ticket_queues_for_user(self.user),
            [self.allowed_queue],
            transform=lambda queue: queue,
        )

    def test_all_ticket_queues_scope_allows_every_queue(self) -> None:
        self.profile.all_ticket_queues = True
        self.profile.save(update_fields=["all_ticket_queues"])

        self.assertTrue(can_access_ticket_queue(self.user, self.allowed_queue))
        self.assertTrue(can_access_ticket_queue(self.user, self.denied_queue))
        self.assertEqual(scope_ticket_queues_for_user(self.user).count(), 2)

    def test_superuser_bypasses_ticket_queue_scope(self) -> None:
        superuser = User.objects.create_superuser(
            email="ticket-admin@example.com",
            password="not-a-real-password",
            first_name="Ticket",
            last_name="Admin",
        )

        self.assertTrue(can_access_ticket_queue(superuser, self.denied_queue))
        self.assertEqual(scope_ticket_queues_for_user(superuser).count(), 2)

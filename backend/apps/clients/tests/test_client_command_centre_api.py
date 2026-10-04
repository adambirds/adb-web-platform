from datetime import timedelta
from decimal import Decimal
from typing import cast

from django.contrib.auth.models import Permission
from django.http import HttpRequest
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.access_control.models import StaffAccessProfile, TicketQueueAccessGrant
from apps.clients.models import Client, ClientContact, Project, TimeEntry
from apps.clients.ninja.command_centre_schemas import ClientCommandCentreOut
from apps.clients.ninja.command_centre_views import client_command_centre
from apps.core.models import Brand
from apps.core.ownership import OwnershipType
from apps.tasks.models import Task
from apps.ticketing.models import Ticket, TicketQueue
from authentication.models import User


class ClientCommandCentreApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.client_record = Client.objects.create(
            name="Example Client",
            company="Example Ltd",
            email="client@example.test",
        )

    def _request(self, user: User) -> HttpRequest:
        request = self.factory.get(f"/api/admin/clients/{self.client_record.id}/command-centre")
        request.user = user
        return request

    def _staff_user(self) -> User:
        return User.objects.create_user(
            email="staff@example.test",
            password="test-password",
            first_name="Staff",
            last_name="User",
            is_staff=True,
        )

    def _grant(self, user: User, *codenames: str) -> None:
        permissions = Permission.objects.filter(codename__in=codenames)
        user.user_permissions.add(*permissions)

    def test_command_centre_returns_current_first_counts_and_period_time(self) -> None:
        user = User.objects.create_superuser(
            email="command-centre@example.test",
            password="test-password",
            first_name="Command",
            last_name="Centre",
        )
        today = timezone.localdate()
        ClientContact.objects.create(
            client=self.client_record,
            name="Current Contact",
            email="current@example.test",
            is_active=True,
        )
        ClientContact.objects.create(
            client=self.client_record,
            name="Former Contact",
            email="former@example.test",
            is_active=False,
        )
        active_project = Project.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_record,
            name="Current delivery",
            status="active",
            start_date=today,
        )
        Project.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_record,
            name="Completed delivery",
            status="completed",
            start_date=today - timedelta(days=60),
        )
        Task.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_record,
            project=active_project,
            title="Overdue work",
            due_date=today - timedelta(days=1),
            priority=3,
        )
        Task.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_record,
            title="Completed work",
            due_date=today - timedelta(days=2),
            completed_at=timezone.now(),
        )
        TimeEntry.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_record,
            project=active_project,
            user=user,
            date=today,
            duration_hours=Decimal("2.5000"),
            description="Current work",
            billable=True,
        )
        TimeEntry.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_record,
            user=user,
            date=today - timedelta(days=45),
            duration_hours=Decimal("9.0000"),
            description="Old work",
            billable=True,
        )

        result = cast(
            ClientCommandCentreOut,
            client_command_centre(
                self._request(user),
                self.client_record.id,
                period_days=30,
            ),
        )

        self.assertEqual(result.stats.active_contacts, 1)
        self.assertEqual(result.stats.current_projects, 1)
        self.assertEqual(result.stats.open_tasks, 1)
        self.assertEqual(result.stats.overdue_tasks, 1)
        self.assertEqual(result.stats.period_hours, Decimal("2.5000"))
        self.assertEqual(result.stats.period_billable_hours, Decimal("2.5000"))
        self.assertEqual([project.name for project in result.projects], ["Current delivery"])
        self.assertEqual([task.title for task in result.tasks], ["Overdue work"])
        self.assertTrue(result.tasks[0].is_overdue)

    def test_command_centre_hides_domains_without_capability_permissions(self) -> None:
        user = self._staff_user()
        StaffAccessProfile.objects.create(user=user, all_clients=True)
        self._grant(user, "view_client")
        Project.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_record,
            name="Hidden project",
            status="active",
            start_date=timezone.localdate(),
        )
        Task.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_record,
            title="Hidden task",
        )

        result = cast(
            ClientCommandCentreOut,
            client_command_centre(self._request(user), self.client_record.id),
        )

        self.assertFalse(result.capabilities.projects)
        self.assertFalse(result.capabilities.tasks)
        self.assertFalse(result.capabilities.tickets)
        self.assertEqual(result.stats.current_projects, 0)
        self.assertEqual(result.stats.open_tasks, 0)
        self.assertEqual(result.projects, [])
        self.assertEqual(result.tasks, [])
        self.assertEqual(result.tickets, [])
        self.assertEqual({item.kind for item in result.activity}, {"client"})

    def test_ticket_summary_respects_ticket_queue_scope(self) -> None:
        user = self._staff_user()
        profile = StaffAccessProfile.objects.create(user=user, all_clients=True)
        self._grant(user, "view_client", "view_ticket")
        brand = Brand.objects.create(
            name="ADB Test",
            slug="adb-test",
            domain="test.example.test",
        )
        visible_queue = TicketQueue.objects.create(name="Visible", key="visible", brand=brand)
        hidden_queue = TicketQueue.objects.create(name="Hidden", key="hidden", brand=brand)
        TicketQueueAccessGrant.objects.create(profile=profile, queue=visible_queue)
        visible_ticket = Ticket.objects.create(
            brand=brand,
            queue=visible_queue,
            client=self.client_record,
            subject="Visible ticket",
            status=Ticket.Status.OPEN,
        )
        Ticket.objects.create(
            brand=brand,
            queue=hidden_queue,
            client=self.client_record,
            subject="Hidden ticket",
            status=Ticket.Status.OPEN,
        )

        result = cast(
            ClientCommandCentreOut,
            client_command_centre(self._request(user), self.client_record.id),
        )

        self.assertTrue(result.capabilities.tickets)
        self.assertEqual(result.stats.actionable_tickets, 1)
        self.assertEqual([ticket.id for ticket in result.tickets], [visible_ticket.id])
        ticket_activity = [item for item in result.activity if item.kind == "ticket"]
        self.assertEqual([item.label for item in ticket_activity], [visible_ticket.reference])

from django.contrib.auth.models import Permission
from django.test import TestCase

from apps.access_control.models import StaffAccessProfile
from apps.clients.models import Client
from apps.core.models import AuditEvent, Brand, DashboardPreference
from apps.core.ownership import OwnershipType
from apps.tasks.models import Task, TaskStatus
from apps.ticketing.models import Ticket, TicketQueue
from authentication.models import User


class DashboardWorkspaceAPITests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="dashboard.staff@example.com",
            password="test-password",
            first_name="Dashboard",
            last_name="Staff",
            is_staff=True,
        )
        self.client_a = Client.objects.create(
            name="Client A",
            company="Client A Ltd",
            email="client-a@example.test",
        )
        self.client_b = Client.objects.create(
            name="Client B",
            company="Client B Ltd",
            email="client-b@example.test",
        )
        self.brand = Brand.objects.create(
            name="ADB Dashboard Test",
            slug="adb-dashboard-test",
            domain="dashboard-test.example.test",
        )
        self.queue_a = TicketQueue.objects.create(
            name="Support",
            key="dashboard-support",
            brand=self.brand,
            ordering=1,
        )
        self.queue_b = TicketQueue.objects.create(
            name="Accounts",
            key="dashboard-accounts",
            brand=self.brand,
            ordering=2,
        )
        profile = StaffAccessProfile.objects.create(user=self.user)
        profile.client_grants.create(client=self.client_a)
        profile.ticket_queue_grants.create(queue=self.queue_a)
        profile.default_ticket_queues.add(self.queue_a)

        self.status = TaskStatus.objects.create(name="Dashboard Open", order=1)
        self.internal_task = Task.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            title="Internal task",
            status=self.status,
            assigned_to=self.user,
        )
        self.client_task = Task.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_a,
            title="Allowed client task",
            status=self.status,
            assigned_to=self.user,
        )
        self.hidden_task = Task.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_b,
            title="Hidden client task",
            status=self.status,
            assigned_to=self.user,
        )
        self.allowed_ticket = Ticket.objects.create(
            brand=self.brand,
            queue=self.queue_a,
            client=self.client_a,
            subject="Allowed ticket",
            assigned_to=self.user,
            source=Ticket.Source.MANUAL,
        )
        self.hidden_queue_ticket = Ticket.objects.create(
            brand=self.brand,
            queue=self.queue_b,
            client=self.client_a,
            subject="Hidden queue ticket",
            assigned_to=self.user,
            source=Ticket.Source.MANUAL,
        )
        self.hidden_client_ticket = Ticket.objects.create(
            brand=self.brand,
            queue=self.queue_a,
            client=self.client_b,
            subject="Hidden client ticket",
            assigned_to=self.user,
            source=Ticket.Source.MANUAL,
        )
        self.client.force_login(self.user)

    def _grant(self, app_label: str, codename: str) -> None:
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label=app_label, codename=codename)
        )

    def test_default_dashboard_only_exposes_authorised_scoped_work(self) -> None:
        self._grant("tasks", "view_task")
        self._grant("ticketing", "view_ticket")

        response = self.client.get("/api/admin/dashboard")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        keys = [item["key"] for item in payload["layout"]]
        self.assertEqual(keys, ["my_tasks", "my_tickets", "agenda"])
        task_titles = {item["title"] for item in payload["my_tasks"]["items"]}
        self.assertEqual(task_titles, {"Internal task", "Allowed client task"})
        ticket_subjects = {item["subject"] for item in payload["my_tickets"]["items"]}
        self.assertEqual(ticket_subjects, {"Allowed ticket"})
        self.assertEqual(payload["my_tickets"]["mine_count"], 1)

    def test_preferences_persist_and_follow_account(self) -> None:
        self._grant("tasks", "view_task")
        response = self.client.put(
            "/api/admin/dashboard/preferences",
            data={"layout": [{"key": "my_tasks", "span": 12}]},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["layout"], [{"key": "my_tasks", "span": 12}])
        self.assertIsNone(response.json()["my_tickets"])
        preference = DashboardPreference.objects.get(user=self.user)
        self.assertEqual(preference.layout, [{"key": "my_tasks", "span": 12}])

        loaded = self.client.get("/api/admin/dashboard")
        self.assertEqual(loaded.json()["layout"], [{"key": "my_tasks", "span": 12}])

    def test_empty_preference_remains_empty(self) -> None:
        self._grant("tasks", "view_task")

        response = self.client.put(
            "/api/admin/dashboard/preferences",
            data={"layout": []},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["layout"], [])
        self.assertEqual(DashboardPreference.objects.get(user=self.user).layout, [])
        loaded = self.client.get("/api/admin/dashboard")
        self.assertEqual(loaded.json()["layout"], [])
        self.assertIsNone(loaded.json()["my_tasks"])

    def test_cannot_enable_widget_without_its_capability(self) -> None:
        self._grant("tasks", "view_task")

        response = self.client.put(
            "/api/admin/dashboard/preferences",
            data={"layout": [{"key": "my_tickets", "span": 6}]},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(DashboardPreference.objects.filter(user=self.user).exists())

    def test_permission_loss_hides_previously_saved_widget(self) -> None:
        self._grant("tasks", "view_task")
        view_ticket = Permission.objects.get(
            content_type__app_label="ticketing",
            codename="view_ticket",
        )
        self.user.user_permissions.add(view_ticket)
        DashboardPreference.objects.create(
            user=self.user,
            layout=[
                {"key": "my_tasks", "span": 6},
                {"key": "my_tickets", "span": 6},
            ],
        )
        self.user.user_permissions.remove(view_ticket)

        response = self.client.get("/api/admin/dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["layout"], [{"key": "my_tasks", "span": 6}])
        self.assertIsNone(response.json()["my_tickets"])

    def test_technical_health_requires_check_and_incident_capabilities(self) -> None:
        self._grant("monitoring", "view_monitorincident")

        response = self.client.get("/api/admin/dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("technical_health", [item["key"] for item in response.json()["layout"]])
        self.assertIsNone(response.json()["technical_health"])

        self._grant("monitoring", "view_monitorcheck")
        response = self.client.get("/api/admin/dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertIn("technical_health", [item["key"] for item in response.json()["layout"]])
        self.assertEqual(response.json()["technical_health"]["active_incident_count"], 0)

    def test_recent_activity_only_exposes_current_users_audit_events(self) -> None:
        self._grant("core", "view_auditevent")
        other_user = User.objects.create_user(
            email="other.dashboard.staff@example.com",
            password="test-password",
            first_name="Other",
            last_name="Staff",
            is_staff=True,
        )
        AuditEvent.record(
            actor=self.user,
            action="dashboard.personal_action",
            target_label="Visible personal action",
        )
        AuditEvent.record(
            actor=other_user,
            action="client.sensitive_action",
            target_label="Hidden client label",
        )

        response = self.client.get("/api/admin/dashboard")

        self.assertEqual(response.status_code, 200)
        activity = response.json()["recent_activity"]
        self.assertIsNotNone(activity)
        labels = {item["target_label"] for item in activity}
        self.assertIn("Visible personal action", labels)
        self.assertNotIn("Hidden client label", labels)

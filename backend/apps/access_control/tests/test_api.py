from unittest.mock import MagicMock, patch

from django.contrib.auth.models import Group, Permission
from django.test import TestCase

from apps.access_control.models import StaffAccessProfile, TicketQueueAccessGrant
from apps.clients.models import Client
from apps.core.models import AuditEvent, Brand
from apps.ticketing.models import TicketQueue
from authentication.models import User


class StaffAccessAPITests(TestCase):
    def setUp(self) -> None:
        self.operator = User.objects.create_user(
            email="access-admin@example.test",
            password="test-password",
            first_name="Access",
            last_name="Admin",
            is_staff=True,
        )
        self.manage_permission = Permission.objects.get(
            content_type__app_label="access_control",
            codename="manage_staff_access",
        )
        self.operator.user_permissions.add(self.manage_permission)
        StaffAccessProfile.objects.create(
            user=self.operator,
            all_clients=True,
            all_ticket_queues=True,
        )

        self.target = User.objects.create_user(
            email="staff-user@example.test",
            password="test-password",
            first_name="Staff",
            last_name="User",
            is_staff=True,
        )
        StaffAccessProfile.objects.create(user=self.target)

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
            name="ADB Access Test",
            slug="adb-access-test",
            domain="access-test.example.test",
        )
        self.queue_a = TicketQueue.objects.create(
            name="Support",
            key="access-support",
            brand=self.brand,
            ordering=1,
        )
        self.queue_b = TicketQueue.objects.create(
            name="Accounts",
            key="access-accounts",
            brand=self.brand,
            ordering=2,
        )
        self.queue_disabled = TicketQueue.objects.create(
            name="Disabled",
            key="access-disabled",
            brand=self.brand,
            enabled=False,
            ordering=3,
        )

        self.task_view = Permission.objects.get(
            content_type__app_label="tasks",
            codename="view_task",
        )
        self.credential_reveal = Permission.objects.get(
            content_type__app_label="credentials",
            codename="reveal_storedcredential",
        )
        self.operations_group = Group.objects.create(name="Operations Test")
        self.operations_group.permissions.add(self.task_view)
        self.client.force_login(self.operator)

    def test_manage_capability_is_required(self) -> None:
        self.operator.user_permissions.remove(self.manage_permission)

        response = self.client.get("/api/admin/access/users")

        self.assertEqual(response.status_code, 403)

    def test_auth_me_projects_restricted_ticket_queue_scope(self) -> None:
        TicketQueueAccessGrant.objects.create(
            profile=self.target.access_profile,
            queue=self.queue_a,
            granted_by=self.operator,
        )
        self.client.force_login(self.target)

        response = self.client.get("/api/auth/me")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["user"]["scope"]["ticket_queues"]["all"])
        self.assertEqual(
            response.json()["user"]["scope"]["ticket_queues"]["ids"],
            [self.queue_a.id],
        )

    def test_options_include_sensitive_business_capabilities_only(self) -> None:
        response = self.client.get("/api/admin/access/options")

        self.assertEqual(response.status_code, 200)
        capabilities = {item["code"]: item for item in response.json()["capabilities"]}
        reveal = capabilities["credentials.reveal_storedcredential"]
        self.assertTrue(reveal["sensitive"])
        self.assertIn("access_control.manage_staff_access", capabilities)
        self.assertNotIn("auth.change_permission", capabilities)
        self.assertNotIn("authentication.change_user", capabilities)
        self.assertNotIn("access_control.change_staffaccessprofile", capabilities)

    def test_groups_with_excluded_permissions_are_hidden_and_rejected(self) -> None:
        raw_permission = Permission.objects.get(
            content_type__app_label="auth",
            codename="change_permission",
        )
        unsafe_group = Group.objects.create(name="Unsafe legacy group")
        unsafe_group.permissions.add(self.task_view, raw_permission)

        options = self.client.get("/api/admin/access/options")
        group_ids = {group["id"] for group in options.json()["groups"]}

        self.assertEqual(options.status_code, 200)
        self.assertNotIn(unsafe_group.id, group_ids)

        payload = {
            "group_ids": [unsafe_group.id],
            "direct_permission_ids": [],
            "all_clients": True,
            "client_ids": [],
            "all_ticket_queues": True,
            "ticket_queue_ids": [],
            "default_ticket_queue_ids": [],
        }
        response = self.client.put(
            f"/api/admin/access/users/{self.target.id}/access",
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.target.groups.count(), 0)

    def test_update_access_sets_groups_permissions_and_scopes_atomically(self) -> None:
        payload = {
            "group_ids": [self.operations_group.id],
            "direct_permission_ids": [self.credential_reveal.id],
            "all_clients": False,
            "client_ids": [self.client_a.id],
            "all_ticket_queues": False,
            "ticket_queue_ids": [self.queue_a.id, self.queue_b.id],
            "default_ticket_queue_ids": [self.queue_a.id],
        }

        response = self.client.put(
            f"/api/admin/access/users/{self.target.id}/access",
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.target.refresh_from_db()
        profile = self.target.access_profile
        self.assertEqual(
            list(self.target.groups.values_list("id", flat=True)), [self.operations_group.id]
        )
        self.assertEqual(
            list(self.target.user_permissions.values_list("id", flat=True)),
            [self.credential_reveal.id],
        )
        self.assertEqual(
            list(profile.client_grants.values_list("client_id", flat=True)),
            [self.client_a.id],
        )
        self.assertEqual(
            set(profile.ticket_queue_grants.values_list("queue_id", flat=True)),
            {self.queue_a.id, self.queue_b.id},
        )
        self.assertEqual(
            list(profile.default_ticket_queues.values_list("id", flat=True)),
            [self.queue_a.id],
        )
        effective = {
            item["code"]: item for item in response.json()["access"]["effective_permissions"]
        }
        self.assertIn("tasks.view_task", effective)
        self.assertIn("Group: Operations Test", effective["tasks.view_task"]["sources"])
        self.assertIn("credentials.reveal_storedcredential", effective)
        self.assertEqual(effective["credentials.reveal_storedcredential"]["sources"], ["Direct"])
        self.assertTrue(
            AuditEvent.objects.filter(
                action="staff_access.updated", target_id=str(self.target.id)
            ).exists()
        )

    def test_default_queue_must_be_enabled_and_inside_new_scope(self) -> None:
        payload = {
            "group_ids": [],
            "direct_permission_ids": [],
            "all_clients": False,
            "client_ids": [],
            "all_ticket_queues": False,
            "ticket_queue_ids": [self.queue_a.id],
            "default_ticket_queue_ids": [self.queue_disabled.id],
        }

        response = self.client.put(
            f"/api/admin/access/users/{self.target.id}/access",
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.target.groups.count(), 0)
        self.assertEqual(self.target.access_profile.ticket_queue_grants.count(), 0)

    def test_non_superuser_cannot_change_own_access(self) -> None:
        payload = {
            "group_ids": [],
            "direct_permission_ids": [],
            "all_clients": True,
            "client_ids": [],
            "all_ticket_queues": True,
            "ticket_queue_ids": [],
            "default_ticket_queue_ids": [],
        }

        response = self.client.put(
            f"/api/admin/access/users/{self.operator.id}/access",
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_non_superuser_cannot_change_superuser(self) -> None:
        superuser = User.objects.create_superuser(
            email="root@example.test",
            password="test-password",
            first_name="Root",
            last_name="Admin",
        )
        payload = {
            "group_ids": [],
            "direct_permission_ids": [],
            "all_clients": True,
            "client_ids": [],
            "all_ticket_queues": True,
            "ticket_queue_ids": [],
            "default_ticket_queue_ids": [],
        }

        response = self.client.put(
            f"/api/admin/access/users/{superuser.id}/access",
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    @patch("apps.access_control.services.send_mail", return_value=1)
    def test_invite_creates_staff_account_with_access_and_setup_token(
        self, mocked_send_mail: MagicMock
    ) -> None:
        payload = {
            "email": "new.staff@example.com",
            "first_name": "New",
            "last_name": "Staff",
            "group_ids": [self.operations_group.id],
            "direct_permission_ids": [self.credential_reveal.id],
            "all_clients": False,
            "client_ids": [self.client_b.id],
            "all_ticket_queues": False,
            "ticket_queue_ids": [self.queue_b.id],
            "default_ticket_queue_ids": [],
        }

        response = self.client.post(
            "/api/admin/access/users/invite",
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        invited = User.objects.get(email="new.staff@example.com")
        self.assertTrue(invited.is_staff)
        self.assertTrue(invited.is_active)
        self.assertFalse(invited.email_verified)
        self.assertFalse(invited.has_usable_password())
        self.assertIsNotNone(invited.password_reset_token)
        self.assertTrue(response.json()["user"]["setup_pending"])
        self.assertEqual(
            list(invited.access_profile.client_grants.values_list("client_id", flat=True)),
            [self.client_b.id],
        )
        self.assertEqual(
            list(invited.access_profile.ticket_queue_grants.values_list("queue_id", flat=True)),
            [self.queue_b.id],
        )
        self.assertTrue(response.json()["invitation_email_sent"])
        mocked_send_mail.assert_called_once()
        self.assertTrue(
            AuditEvent.objects.filter(
                action="staff_access.invited", target_id=str(invited.id)
            ).exists()
        )

    @patch("apps.access_control.services.send_mail", return_value=1)
    def test_pending_invitation_can_be_resent(self, mocked_send_mail: MagicMock) -> None:
        invited = User.objects.create_user(
            email="pending.staff@example.test",
            password="unused-test-password",
            first_name="Pending",
            last_name="Staff",
            is_staff=True,
        )
        invited.set_unusable_password()
        invited.save(update_fields=["password"])
        StaffAccessProfile.objects.create(user=invited)
        old_token = invited.password_reset_token

        response = self.client.post(f"/api/admin/access/users/{invited.id}/resend-invitation")

        self.assertEqual(response.status_code, 200)
        invited.refresh_from_db()
        self.assertNotEqual(invited.password_reset_token, old_token)
        self.assertIsNotNone(invited.password_reset_token_created)
        self.assertTrue(response.json()["invitation_email_sent"])
        mocked_send_mail.assert_called_once()
        self.assertTrue(
            AuditEvent.objects.filter(
                action="staff_access.invitation_resent", target_id=str(invited.id)
            ).exists()
        )

    def test_configured_account_cannot_use_invitation_resend(self) -> None:
        response = self.client.post(f"/api/admin/access/users/{self.target.id}/resend-invitation")

        self.assertEqual(response.status_code, 400)

    def test_deactivate_and_activate_are_audited(self) -> None:
        deactivate = self.client.post(f"/api/admin/access/users/{self.target.id}/deactivate")
        self.target.refresh_from_db()
        self.assertEqual(deactivate.status_code, 200)
        self.assertFalse(self.target.is_active)
        self.assertTrue(
            AuditEvent.objects.filter(
                action="staff_access.deactivated", target_id=str(self.target.id)
            ).exists()
        )

        activate = self.client.post(f"/api/admin/access/users/{self.target.id}/activate")
        self.target.refresh_from_db()
        self.assertEqual(activate.status_code, 200)
        self.assertTrue(self.target.is_active)
        self.assertTrue(
            AuditEvent.objects.filter(
                action="staff_access.activated", target_id=str(self.target.id)
            ).exists()
        )

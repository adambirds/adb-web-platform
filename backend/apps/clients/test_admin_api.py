from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import RequestFactory, TestCase

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client
from apps.clients.ninja.admin_views import create_client, update_client
from apps.clients.ninja.schemas import ClientDetailOut, ClientIn


class ClientAdminApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.superuser = get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="test-password",
            first_name="Admin",
            last_name="User",
        )

    def _request(self, user, method: str = "post"):
        request = getattr(self.factory, method)("/api/admin/clients")
        request.user = user
        return request

    def _payload(self, **overrides) -> ClientIn:
        values = {
            "name": "Jane Example",
            "company": "Example Ltd",
            "email": "JANE@EXAMPLE.COM",
            "phone": "0161 555 0100",
            "address": "1 Example Street",
            "city": "Manchester",
            "state": "Greater Manchester",
            "country": "United Kingdom",
            "postal_code": "M1 1AA",
            "status": "active",
            "notes": "Primary account notes",
        }
        values.update(overrides)
        return ClientIn(**values)

    def _staff_with_permission(self, codename: str):
        user = get_user_model().objects.create_user(
            email=f"{codename}@example.com",
            password="test-password",
            first_name="Staff",
            last_name="User",
            is_staff=True,
        )
        permission = Permission.objects.get(
            content_type__app_label="clients",
            codename=codename,
        )
        user.user_permissions.add(permission)
        return user

    def test_superuser_can_create_and_update_client(self) -> None:
        create_result = create_client(self._request(self.superuser), self._payload())

        self.assertIsInstance(create_result, tuple)
        status_code, detail = create_result
        self.assertEqual(status_code, 201)
        self.assertIsInstance(detail, ClientDetailOut)

        client = Client.objects.get(id=detail.id)
        self.assertEqual(client.company, "Example Ltd")
        self.assertEqual(client.email, "jane@example.com")

        update_result = update_client(
            self._request(self.superuser, "put"),
            client.id,
            self._payload(company="Example Group", status="inactive"),
        )

        self.assertIsInstance(update_result, ClientDetailOut)
        client.refresh_from_db()
        self.assertEqual(client.company, "Example Group")
        self.assertEqual(client.status, "inactive")

    def test_created_client_is_added_to_restricted_staff_scope(self) -> None:
        user = self._staff_with_permission("add_client")
        profile = StaffAccessProfile.objects.create(user=user, all_clients=False)

        result = create_client(self._request(user), self._payload(email="new@example.com"))

        self.assertIsInstance(result, tuple)
        status_code, detail = result
        self.assertEqual(status_code, 201)
        self.assertTrue(
            ClientAccessGrant.objects.filter(profile=profile, client_id=detail.id).exists()
        )

    def test_staff_cannot_update_client_outside_scope(self) -> None:
        user = self._staff_with_permission("change_client")
        StaffAccessProfile.objects.create(user=user, all_clients=False)
        client = Client.objects.create(
            name="Restricted Client",
            company="Restricted Ltd",
            email="restricted@example.com",
        )

        result = update_client(
            self._request(user, "put"),
            client.id,
            self._payload(email="restricted@example.com"),
        )

        self.assertIsInstance(result, tuple)
        status_code, problem = result
        self.assertEqual(status_code, 404)
        self.assertEqual(problem["code"], "not_found")

from typing import Any, cast

from django.contrib.auth.models import Permission
from django.http import HttpRequest
from django.test import RequestFactory, TestCase

from apps.access_control.models import ClientAccessGrant, StaffAccessProfile
from apps.clients.models import Client, ClientContact
from apps.clients.ninja.admin_views import create_client_contact, update_client_contact
from apps.clients.ninja.schemas import ClientContactIn, ClientContactOut
from authentication.models import User


class ClientContactAdminApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="test-password",
            first_name="Admin",
            last_name="User",
        )
        self.client = Client.objects.create(
            name="Jane Example",
            company="Example Ltd",
            email="jane@example.com",
        )

    def _request(self, user: User, method: str = "post") -> HttpRequest:
        request = getattr(self.factory, method)(f"/api/admin/clients/{self.client.id}/contacts")
        request.user = user
        return request

    def _payload(self, **overrides: Any) -> ClientContactIn:
        values: dict[str, Any] = {
            "name": "Alex Contact",
            "email": "ALEX@EXAMPLE.COM",
            "phone": "0161 555 0101",
            "role": "Operations Manager",
            "is_active": True,
            "is_primary": False,
            "is_billing": False,
            "is_technical": False,
        }
        values.update(overrides)
        return ClientContactIn(**values)

    def _staff_with_permission(self, codename: str) -> User:
        user = User.objects.create_user(
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

    def test_superuser_can_create_contact_and_email_is_normalised(self) -> None:
        result = create_client_contact(
            self._request(self.superuser),
            self.client.id,
            self._payload(is_primary=True),
        )

        self.assertIsInstance(result, tuple)
        status_code, response = result
        self.assertEqual(status_code, 201)
        contact = cast(ClientContactOut, response)
        saved = ClientContact.objects.get(id=contact.id)
        self.assertEqual(saved.email, "alex@example.com")
        self.assertTrue(saved.is_primary)

    def test_new_primary_contact_replaces_existing_primary(self) -> None:
        existing = ClientContact.objects.create(
            client=self.client,
            name="Existing Contact",
            email="existing@example.com",
            is_primary=True,
        )

        result = create_client_contact(
            self._request(self.superuser),
            self.client.id,
            self._payload(is_primary=True),
        )

        self.assertIsInstance(result, tuple)
        self.assertEqual(result[0], 201)
        existing.refresh_from_db()
        self.assertFalse(existing.is_primary)

    def test_staff_cannot_create_contact_for_client_outside_scope(self) -> None:
        user = self._staff_with_permission("add_clientcontact")
        StaffAccessProfile.objects.create(user=user, all_clients=False)

        result = create_client_contact(
            self._request(user),
            self.client.id,
            self._payload(),
        )

        self.assertIsInstance(result, tuple)
        status_code, problem = cast(tuple[int, dict[str, Any]], result)
        self.assertEqual(status_code, 404)
        self.assertEqual(problem["code"], "not_found")
        self.assertEqual(ClientContact.objects.count(), 0)

    def test_deactivating_contact_clears_operational_responsibilities(self) -> None:
        user = self._staff_with_permission("change_clientcontact")
        profile = StaffAccessProfile.objects.create(user=user, all_clients=False)
        ClientAccessGrant.objects.create(profile=profile, client=self.client, granted_by=user)
        contact = ClientContact.objects.create(
            client=self.client,
            name="Alex Contact",
            email="alex@example.com",
            is_primary=True,
            is_billing=True,
            is_technical=True,
        )

        result = update_client_contact(
            self._request(user, "put"),
            self.client.id,
            contact.id,
            self._payload(email="alex@example.com", is_active=False, is_primary=True, is_billing=True),
        )

        self.assertIsInstance(result, ClientContactOut)
        contact.refresh_from_db()
        self.assertFalse(contact.is_active)
        self.assertFalse(contact.is_primary)
        self.assertFalse(contact.is_billing)
        self.assertFalse(contact.is_technical)

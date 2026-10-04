from typing import cast

from django.http import HttpRequest
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.clients.models import Client, ClientContact, Project
from apps.clients.ninja.overview_schemas import ClientOverviewOut
from apps.clients.ninja.overview_views import client_overview
from apps.core.ownership import OwnershipType
from authentication.models import User


class ClientOverviewApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            email="client-overview@example.com",
            password="test-password",
            first_name="Client",
            last_name="Overview",
        )

    def _request(self) -> HttpRequest:
        request = self.factory.get("/api/admin/client-overview")
        request.user = self.user
        return request

    def test_overview_defaults_to_active_clients_and_active_contact_stats(self) -> None:
        active = Client.objects.create(
            name="Active Contact",
            company="Active Company",
            email="active@example.com",
            status="active",
        )
        Client.objects.create(
            name="Inactive Contact",
            company="Inactive Company",
            email="inactive@example.com",
            status="inactive",
        )
        ClientContact.objects.create(
            client=active,
            name="Current Person",
            email="current@example.com",
            is_active=True,
        )
        ClientContact.objects.create(
            client=active,
            name="Former Person",
            email="former@example.com",
            is_active=False,
        )

        overview = cast(ClientOverviewOut, client_overview(self._request()))

        self.assertEqual(overview.total, 1)
        self.assertEqual(overview.stats.total, 1)
        self.assertEqual(overview.stats.active, 1)
        self.assertEqual(overview.stats.inactive, 0)
        self.assertEqual(overview.stats.contacts, 1)
        self.assertEqual(overview.items[0].id, active.id)
        self.assertEqual(overview.items[0].contact_count, 1)

    def test_overview_filters_paginates_and_returns_scope_stats(self) -> None:
        clients = []
        for index in range(28):
            status = "active" if index < 20 else "inactive"
            clients.append(
                Client.objects.create(
                    name=f"Contact {index:02d}",
                    company=f"Company {index:02d}",
                    email=f"client-{index:02d}@example.com",
                    status=status,
                )
            )

        ClientContact.objects.create(
            client=clients[0],
            name="Finance Person",
            email="finance@example.com",
        )
        Project.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=clients[0],
            name="Active delivery",
            status="active",
            start_date=timezone.localdate(),
        )

        result = client_overview(
            self._request(),
            page=2,
            page_size=10,
            status="active",
        )
        overview = cast(ClientOverviewOut, result)

        self.assertEqual(overview.stats.total, 20)
        self.assertEqual(overview.stats.active, 20)
        self.assertEqual(overview.stats.inactive, 0)
        self.assertEqual(overview.stats.contacts, 1)
        self.assertEqual(overview.stats.projects, 1)
        self.assertEqual(overview.stats.active_projects, 1)
        self.assertEqual(overview.total, 20)
        self.assertEqual(overview.total_pages, 2)
        self.assertEqual(overview.page, 2)
        self.assertEqual(len(overview.items), 10)

        search_result = client_overview(
            self._request(),
            search="Finance Person",
        )
        search_overview = cast(ClientOverviewOut, search_result)
        self.assertEqual(search_overview.total, 1)
        self.assertEqual(search_overview.items[0].id, clients[0].id)
        self.assertEqual(search_overview.items[0].active_project_count, 1)

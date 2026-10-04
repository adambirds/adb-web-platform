from typing import cast

from django.http import HttpRequest
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.crm.models import Lead, LeadSource, LeadStatus
from apps.crm.ninja.overview_schemas import LeadOverviewOut
from apps.crm.ninja.overview_views import lead_overview
from authentication.models import User


class LeadOverviewApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            email="lead-overview@example.com",
            password="test-password",
            first_name="Lead",
            last_name="Owner",
        )
        self.other_user = User.objects.create_user(
            email="other-owner@example.com",
            password="test-password",
            first_name="Other",
            last_name="Owner",
            is_staff=True,
        )
        self.status_new = LeadStatus.objects.create(name="New", order=10)
        self.status_qualified = LeadStatus.objects.create(name="Qualified", order=20)
        self.status_won = LeadStatus.objects.create(name="Won", order=50)
        self.status_lost = LeadStatus.objects.create(name="Lost", order=60)
        self.source = LeadSource.objects.create(name="Referral")

    def _request(self) -> HttpRequest:
        request = self.factory.get("/api/admin/lead-overview")
        request.user = self.user
        return request

    def test_default_view_only_returns_my_active_leads(self) -> None:
        mine = Lead.objects.create(
            name="My active lead",
            email="mine@example.com",
            status=self.status_new,
            source=self.source,
            assigned_to=self.user,
        )
        Lead.objects.create(
            name="Someone else's lead",
            email="other@example.com",
            status=self.status_qualified,
            source=self.source,
            assigned_to=self.other_user,
        )
        Lead.objects.create(
            name="My won lead",
            email="won@example.com",
            status=self.status_won,
            source=self.source,
            assigned_to=self.user,
        )
        Lead.objects.create(
            name="My lost lead",
            email="lost@example.com",
            status=self.status_lost,
            source=self.source,
            assigned_to=self.user,
        )

        overview = cast(LeadOverviewOut, lead_overview(self._request()))

        self.assertEqual(overview.total, 1)
        self.assertEqual(overview.items[0].id, mine.id)
        self.assertEqual(overview.stats.mine, 1)
        self.assertEqual(overview.stats.active, 2)
        self.assertEqual(overview.stats.unassigned, 0)
        self.assertEqual(self.status_won.outcome, LeadStatus.Outcome.WON)
        self.assertEqual(self.status_lost.outcome, LeadStatus.Outcome.LOST)

    def test_historical_views_are_explicit_and_active_stats_remain_actionable(self) -> None:
        Lead.objects.create(
            name="Active",
            email="active@example.com",
            status=self.status_new,
            source=self.source,
            assigned_to=self.user,
        )
        won = Lead.objects.create(
            name="Won opportunity",
            email="won-history@example.com",
            status=self.status_won,
            source=self.source,
            assigned_to=self.user,
        )
        lost = Lead.objects.create(
            name="Lost opportunity",
            email="lost-history@example.com",
            status=self.status_lost,
            source=self.source,
            assigned_to=self.user,
        )

        won_overview = cast(LeadOverviewOut, lead_overview(self._request(), view="won"))
        lost_overview = cast(LeadOverviewOut, lead_overview(self._request(), view="lost"))

        self.assertEqual(won_overview.total, 1)
        self.assertEqual(won_overview.items[0].id, won.id)
        self.assertEqual(won_overview.items[0].outcome, LeadStatus.Outcome.WON)
        self.assertEqual(lost_overview.total, 1)
        self.assertEqual(lost_overview.items[0].id, lost.id)
        self.assertEqual(lost_overview.items[0].outcome, LeadStatus.Outcome.LOST)
        self.assertEqual(won_overview.stats.active, 1)

    def test_unassigned_and_search_filters_work_inside_active_queue(self) -> None:
        Lead.objects.create(
            name="Assigned",
            email="assigned@example.com",
            status=self.status_new,
            source=self.source,
            assigned_to=self.user,
        )
        target = Lead.objects.create(
            name="Search Target",
            email="target@example.com",
            company="Useful Prospect",
            status=self.status_qualified,
            source=self.source,
            message="Website redesign enquiry",
        )
        converted = Lead.objects.create(
            name="Converted",
            email="converted@example.com",
            status=self.status_new,
            source=self.source,
        )
        converted.converted_at = timezone.now()
        converted.save(update_fields=["converted_at"])

        unassigned = cast(
            LeadOverviewOut,
            lead_overview(self._request(), view="unassigned", search="redesign"),
        )

        self.assertEqual(unassigned.total, 1)
        self.assertEqual(unassigned.items[0].id, target.id)
        self.assertEqual(unassigned.stats.active, 2)
        self.assertEqual(unassigned.stats.unassigned, 1)

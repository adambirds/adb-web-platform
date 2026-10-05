from typing import cast

from django.contrib.auth.models import Permission
from django.http import HttpRequest
from django.test import RequestFactory, TestCase

from apps.crm.models import LeadSource, LeadStatus
from apps.crm.ninja.admin_views import create_lead_source, create_lead_status, lead_options
from apps.crm.ninja.schemas import LeadLookupOut, LeadOptionsOut, LeadSourceIn, LeadStatusIn
from authentication.models import User


class LeadOptionsTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="catalogue@example.test",
            password="test-password",
            first_name="Catalogue",
            last_name="User",
            is_staff=True,
        )
        self.factory = RequestFactory()

    def request(self) -> HttpRequest:
        request = self.factory.post("/api/admin/lead-sources")
        request.user = self.user
        return request

    def grant(self, *codenames: str) -> None:
        self.user.user_permissions.add(
            *Permission.objects.filter(content_type__app_label="crm", codename__in=codenames)
        )
        self.user = User.objects.get(pk=self.user.pk)

    def test_defaults_are_available_without_demo_seeding(self) -> None:
        self.grant("add_lead")
        options = cast(LeadOptionsOut, lead_options(self.request()))
        self.assertTrue(
            {"Email", "Phone", "Website", "Referral", "LinkedIn", "Instagram"}.issubset(
                {source.name for source in options.sources}
            )
        )
        self.assertTrue(
            {"New", "Contacted", "Qualified", "Proposal", "Won", "Lost"}.issubset(
                {status.name for status in options.statuses}
            )
        )
        self.assertEqual(LeadStatus.objects.get(name="Won").outcome, "won")
        self.assertEqual(LeadStatus.objects.get(name="Lost").outcome, "lost")

    def test_lead_creation_permission_does_not_allow_catalogue_writes(self) -> None:
        self.grant("add_lead")
        self.assertEqual(create_lead_source(self.request(), LeadSourceIn(name="Partner"))[0], 403)
        self.assertEqual(create_lead_status(self.request(), LeadStatusIn(name="Follow-up"))[0], 403)
        self.assertFalse(LeadSource.objects.filter(name="Partner").exists())
        self.assertFalse(LeadStatus.objects.filter(name="Follow-up").exists())

    def test_authorised_catalogue_creation_preserves_explicit_outcome(self) -> None:
        self.grant("add_leadsource", "add_leadstatus")
        status, created = create_lead_source(self.request(), LeadSourceIn(name="  Partner  "))
        self.assertEqual(status, 201)
        self.assertEqual(cast(LeadLookupOut, created).name, "Partner")
        status, created = create_lead_status(
            self.request(), LeadStatusIn(name="Contract signed", outcome="won")
        )
        self.assertEqual(status, 201)
        self.assertEqual(LeadStatus.objects.get(id=cast(LeadLookupOut, created).id).outcome, "won")

    def test_blank_and_case_insensitive_duplicate_names_are_rejected(self) -> None:
        self.grant("add_leadsource", "add_leadstatus")
        for name in ["   ", "email"]:
            self.assertEqual(create_lead_source(self.request(), LeadSourceIn(name=name))[0], 400)
        for name in ["   ", "new"]:
            self.assertEqual(create_lead_status(self.request(), LeadStatusIn(name=name))[0], 400)

    def test_non_staff_cannot_manage_catalogue_even_with_capabilities(self) -> None:
        self.grant("add_leadsource", "add_leadstatus")
        self.user.is_staff = False
        self.user.save(update_fields=["is_staff"])
        self.assertEqual(create_lead_source(self.request(), LeadSourceIn(name="Partner"))[0], 403)
        self.assertEqual(create_lead_status(self.request(), LeadStatusIn(name="Follow-up"))[0], 403)

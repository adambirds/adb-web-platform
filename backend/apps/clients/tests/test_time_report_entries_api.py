from datetime import date, timedelta
from decimal import Decimal
from typing import cast

from django.http import HttpRequest
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.clients.models import Client, Project, TimeEntry
from apps.clients.ninja.time_report_schemas import TimeReportEntriesOut, TimeReportSummaryOut
from apps.clients.ninja.time_report_views import (
    _period_dates,
    time_report_entries,
    time_report_summary,
)
from apps.core.ownership import OwnershipType
from authentication.models import User


class TimeReportEntriesApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            email="time-drilldown@example.com",
            password="test-password",
            first_name="Time",
            last_name="Drilldown",
        )
        self.client_record = Client.objects.create(
            name="Drilldown Client",
            company="Drilldown Client Ltd",
            email="drilldown@example.com",
        )
        self.client_project = Project.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_record,
            name="Client Delivery",
            start_date=timezone.localdate(),
        )
        self.internal_project = Project.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Internal Platform",
            start_date=timezone.localdate(),
        )

    def _request(self) -> HttpRequest:
        request = self.factory.get("/api/admin/time-reports/entries")
        request.user = self.user
        return request

    def test_week_periods_use_monday_to_sunday_boundaries(self) -> None:
        thursday = date(2026, 8, 20)

        this_week_from, this_week_to = _period_dates("this_week", thursday)
        last_week_from, last_week_to = _period_dates("last_week", thursday)

        self.assertEqual(this_week_from, date(2026, 8, 17))
        self.assertEqual(this_week_to, thursday)
        self.assertEqual(last_week_from, date(2026, 8, 10))
        self.assertEqual(last_week_to, date(2026, 8, 16))

    def test_client_drilldown_filters_entries_to_selected_period(self) -> None:
        today = timezone.localdate()
        previous_month = today.replace(day=1) - timedelta(days=1)
        TimeEntry.objects.create(
            project=self.client_project,
            user=self.user,
            date=today,
            duration_hours=Decimal("2.5000"),
            description="Current month delivery",
            billable=True,
        )
        TimeEntry.objects.create(
            project=self.client_project,
            user=self.user,
            date=previous_month,
            duration_hours=Decimal("1.0000"),
            description="Previous month delivery",
            billable=True,
        )
        TimeEntry.objects.create(
            project=self.internal_project,
            user=self.user,
            date=today,
            duration_hours=Decimal("0.7500"),
            description="Internal work",
            billable=False,
        )

        result = time_report_entries(
            self._request(),
            period="this_month",
            client_id=self.client_record.id,
        )

        report = cast(TimeReportEntriesOut, result)
        self.assertEqual(report.total, 1)
        self.assertEqual(report.tracked_hours, Decimal("2.5000"))
        self.assertEqual(report.billable_hours, Decimal("2.5000"))
        self.assertEqual(report.items[0].description, "Current month delivery")
        self.assertEqual(report.items[0].client_id, self.client_record.id)

    def test_project_and_internal_filters_are_available_for_workspace_drilldown(self) -> None:
        today = timezone.localdate()
        TimeEntry.objects.create(
            project=self.client_project,
            user=self.user,
            date=today,
            duration_hours=Decimal("1.5000"),
            description="Project delivery",
            billable=True,
        )
        TimeEntry.objects.create(
            project=self.internal_project,
            user=self.user,
            date=today,
            duration_hours=Decimal("0.5000"),
            description="Internal maintenance",
            billable=False,
        )

        project_result = time_report_entries(
            self._request(),
            period="this_month",
            project_id=self.client_project.id,
        )
        internal_result = time_report_summary(
            self._request(),
            period="this_month",
            ownership_type=OwnershipType.INTERNAL,
        )

        project_report = cast(TimeReportEntriesOut, project_result)
        internal_report = cast(TimeReportSummaryOut, internal_result)
        self.assertEqual(project_report.total, 1)
        self.assertEqual(project_report.items[0].project_id, self.client_project.id)
        self.assertEqual(internal_report.tracked_hours, Decimal("0.5000"))
        self.assertEqual(internal_report.internal_hours, Decimal("0.5000"))
        self.assertEqual(internal_report.client_hours, Decimal(0))

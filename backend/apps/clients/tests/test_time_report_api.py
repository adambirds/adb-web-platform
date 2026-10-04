from decimal import Decimal
from typing import cast

from django.http import HttpRequest
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.clients.models import Client, Project, TimeEntry
from apps.clients.ninja.time_report_schemas import TimeReportSummaryOut
from apps.clients.ninja.time_report_views import time_report_summary
from apps.core.ownership import OwnershipType
from authentication.models import User


class TimeReportApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            email="time-report@example.com",
            password="test-password",
            first_name="Time",
            last_name="Reporter",
        )
        self.client_account = Client.objects.create(
            name="Report Client",
            company="Report Client Ltd",
            email="report-client@example.com",
        )
        self.client_project = Project.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_account,
            name="Report Project",
            start_date=timezone.localdate(),
        )
        self.internal_project = Project.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Internal Platform",
            start_date=timezone.localdate(),
        )

    def _request(self) -> HttpRequest:
        request = self.factory.get("/api/admin/time-reports/summary")
        request.user = self.user
        return request

    def test_this_month_summary_aggregates_client_and_internal_time(self) -> None:
        today = timezone.localdate()
        TimeEntry.objects.create(
            project=self.client_project,
            user=self.user,
            date=today,
            duration_hours=Decimal("2.5000"),
            description="Billable delivery",
            billable=True,
        )
        TimeEntry.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_account,
            user=self.user,
            date=today,
            duration_hours=Decimal("1.2500"),
            description="Non-billable client work",
            billable=False,
        )
        TimeEntry.objects.create(
            project=self.internal_project,
            user=self.user,
            date=today,
            duration_hours=Decimal("0.7500"),
            description="Internal platform work",
            billable=False,
        )

        result = time_report_summary(self._request(), period="this_month")

        report = cast(TimeReportSummaryOut, result)
        self.assertEqual(report.period, "this_month")
        self.assertEqual(report.date_from, today.replace(day=1))
        self.assertEqual(report.date_to, today)
        self.assertEqual(report.tracked_hours, Decimal("4.5000"))
        self.assertEqual(report.billable_hours, Decimal("2.5000"))
        self.assertEqual(report.non_billable_hours, Decimal("2.0000"))
        self.assertEqual(report.client_hours, Decimal("3.7500"))
        self.assertEqual(report.internal_hours, Decimal("0.7500"))
        self.assertEqual(report.entry_count, 3)

        self.assertEqual(len(report.clients), 1)
        client = report.clients[0]
        self.assertEqual(client.client_id, self.client_account.id)
        self.assertEqual(client.client_name, "Report Client Ltd")
        self.assertEqual(client.tracked_hours, Decimal("3.7500"))
        self.assertEqual(client.billable_hours, Decimal("2.5000"))
        self.assertEqual(client.non_billable_hours, Decimal("1.2500"))
        self.assertEqual(client.entry_count, 2)
        self.assertEqual(client.project_count, 1)

        self.assertEqual(len(report.daily), 1)
        self.assertEqual(report.daily[0].date, today)
        self.assertEqual(report.daily[0].tracked_hours, Decimal("4.5000"))
        self.assertEqual(report.daily[0].billable_hours, Decimal("2.5000"))

    def test_empty_summary_returns_zero_totals(self) -> None:
        report = cast(
            TimeReportSummaryOut,
            time_report_summary(self._request(), period="this_month"),
        )

        self.assertEqual(report.tracked_hours, Decimal(0))
        self.assertEqual(report.billable_hours, Decimal(0))
        self.assertEqual(report.non_billable_hours, Decimal(0))
        self.assertEqual(report.client_hours, Decimal(0))
        self.assertEqual(report.internal_hours, Decimal(0))
        self.assertEqual(report.entry_count, 0)
        self.assertEqual(report.clients, [])
        self.assertEqual(report.daily, [])

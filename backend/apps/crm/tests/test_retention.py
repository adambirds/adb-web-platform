from typing import cast
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.http import HttpRequest
from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.clients.models import Client, TimeEntry
from apps.core.models import AuditEvent, Brand
from apps.crm.models import Lead, LeadRetentionReview, LeadStatus
from apps.crm.ninja.retention_views import (
    RetentionDecision,
    RetentionPage,
    decide_review,
    list_reviews,
    scan_reviews,
)
from apps.crm.retention import (
    add_months,
    approve_retention_review,
    assess_lead,
    cleanup_retention_files,
    defer_retention_review,
    refresh_retention_reviews,
)
from apps.ticketing.models import Ticket, TicketAttachment, TicketMessage, TicketQueue
from authentication.models import User


class RetentionTests(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.get(slug="adb-web-designs")
        self.lost = LeadStatus.objects.get(outcome="lost")
        self.old = add_months(timezone.now(), -37)
        self.admin = User.objects.create_superuser(
            email="retention@example.com", password="password", first_name="Admin", last_name="User"
        )
        self.queue = TicketQueue.objects.create(
            brand=self.brand, key="retention-sales", name="Sales"
        )
        self.lead = Lead.objects.create(
            brand=self.brand,
            status=self.lost,
            name="Previous enquiry",
            email="enquiry@example.com",
            notes="Keep these previous notes.",
        )
        Lead.objects.filter(pk=self.lead.pk).update(created_at=self.old, updated_at=self.old)
        self.lead.refresh_from_db()

    def ticket(self) -> Ticket:
        ticket = Ticket.objects.create(
            brand=self.brand,
            queue=self.queue,
            subject="Earlier enquiry",
            status=Ticket.Status.CLOSED,
            source=Ticket.Source.CONTACT_FORM,
            last_message_at=self.old,
        )
        message = TicketMessage.objects.create(
            ticket=ticket,
            direction="inbound",
            sender_address=self.lead.email,
            body_text="Earlier conversation",
            sent_or_received_at=self.old,
        )
        Ticket.objects.filter(pk=ticket.pk).update(created_at=self.old, updated_at=self.old)
        TicketMessage.objects.filter(pk=message.pk).update(created_at=self.old)
        return ticket

    def review(self) -> LeadRetentionReview:
        refresh_retention_reviews()
        return LeadRetentionReview.objects.get(lead=self.lead)

    def request(self, user: User) -> HttpRequest:
        request = RequestFactory().post("/api/admin/retention/leads")
        request.user = user
        return request

    def staff(self, *permissions: str) -> User:
        user = User.objects.create_user(
            email="staff-retention@example.com",
            password="password",
            first_name="Staff",
            last_name="User",
            is_staff=True,
        )
        for capability in permissions:
            app, name = capability.split(".")
            user.user_permissions.add(
                Permission.objects.get(content_type__app_label=app, codename=name)
            )
        return user

    def test_scan_is_repeatable_and_never_deletes_without_approval(self) -> None:
        self.ticket()
        self.review()
        refresh_retention_reviews()
        self.assertEqual(LeadRetentionReview.objects.count(), 1)
        self.assertTrue(Lead.objects.filter(pk=self.lead.pk).exists())
        self.assertTrue(TicketMessage.objects.filter(sender_address=self.lead.email).exists())

    def test_next_year_return_preserves_history_and_refresh_cancels_stale_review(self) -> None:
        review = self.review()
        Lead.objects.filter(pk=self.lead.pk).update(updated_at=timezone.now())
        with self.assertRaises(ValueError):
            approve_retention_review(review.pk, self.admin)
        refresh_retention_reviews()
        review.refresh_from_db()
        self.assertEqual(review.status, review.Status.CANCELLED)
        self.assertEqual(Lead.objects.get(pk=self.lead.pk).notes, "Keep these previous notes.")

    def test_recent_email_resets_period_even_when_lead_is_unchanged(self) -> None:
        ticket = self.ticket()
        TicketMessage.objects.create(
            ticket=ticket,
            direction="inbound",
            sender_address="ENQUIRY@EXAMPLE.COM",
            sent_or_received_at=timezone.now(),
        )
        self.assertFalse(assess_lead(self.lead).eligible)
        self.assertEqual(refresh_retention_reviews()["queued"], 0)

    def test_active_and_client_records_are_protected(self) -> None:
        self.lead.status = LeadStatus.objects.get(name="New")
        self.lead.save()
        self.assertFalse(assess_lead(self.lead).eligible)
        self.lead.status = self.lost
        self.lead.save()
        Client.objects.create(name="Client", email=self.lead.email)
        self.assertFalse(assess_lead(self.lead).eligible)

    def test_open_or_unrelated_conversation_prevents_review(self) -> None:
        ticket = self.ticket()
        Ticket.objects.filter(pk=ticket.pk).update(status=Ticket.Status.OPEN)
        self.assertFalse(assess_lead(self.lead).eligible)
        Ticket.objects.filter(pk=ticket.pk).update(
            status=Ticket.Status.CLOSED,
            source=Ticket.Source.EMAIL,
            classification=Ticket.Classification.ACCOUNTS,
        )
        self.assertFalse(assess_lead(self.lead).eligible)

    def test_rejection_requires_reason_and_returns_after_review_date(self) -> None:
        review = self.review()
        with self.assertRaises(ValueError):
            defer_retention_review(review.pk, self.admin, "", 6)
        kept = defer_retention_review(review.pk, self.admin, "A documented outstanding query", 6)
        refresh_retention_reviews()
        kept.refresh_from_db()
        self.assertEqual(kept.status, kept.Status.DEFERRED)
        refresh_retention_reviews(now=add_months(timezone.now(), 7))
        kept.refresh_from_db()
        self.assertEqual(kept.status, kept.Status.PENDING)
        self.assertTrue(Lead.objects.filter(pk=self.lead.pk).exists())

    def test_approval_removes_bundle_and_tracks_storage_retry_without_personal_audit_data(
        self,
    ) -> None:
        ticket = self.ticket()
        attachment = TicketAttachment.objects.create(
            message=ticket.messages.get(),
            original_filename="private.pdf",
            storage_key="attachments/random-object",
        )
        review = self.review()
        with (
            patch(
                "apps.crm.retention.default_storage.delete", side_effect=OSError("Storage offline")
            ),
            self.captureOnCommitCallbacks(execute=True),
        ):
            approve_retention_review(review.pk, self.admin)
        self.assertFalse(Lead.objects.filter(pk=self.lead.pk).exists())
        self.assertFalse(Ticket.objects.filter(pk=ticket.pk).exists())
        self.assertFalse(TicketAttachment.objects.filter(pk=attachment.pk).exists())
        review.refresh_from_db()
        self.assertIsNone(review.lead_id)
        self.assertEqual(review.pending_storage_keys, ["attachments/random-object"])
        with patch("apps.crm.retention.default_storage.delete") as delete:
            self.assertEqual(cleanup_retention_files(), 1)
            delete.assert_called_once_with("attachments/random-object")
        self.assertNotIn(self.lead.email, str(list(AuditEvent.objects.values())))

    def test_shared_history_is_preserved_until_last_lead_approval(self) -> None:
        ticket = self.ticket()
        sibling = Lead.objects.create(
            brand=self.brand, status=self.lost, name="Old related lead", email=self.lead.email
        )
        Lead.objects.filter(pk=sibling.pk).update(created_at=self.old, updated_at=self.old)
        approve_retention_review(self.review().pk, self.admin)
        self.assertTrue(Ticket.objects.filter(pk=ticket.pk).exists())

    def test_review_permissions_and_ticket_scope_are_enforced(self) -> None:
        self.ticket()
        review = self.review()
        staff = self.staff(
            "crm.view_lead",
            "crm.view_leadretentionreview",
            "crm.change_leadretentionreview",
            "crm.delete_lead",
            "ticketing.view_ticket",
            "ticketing.delete_ticket",
        )
        result = list_reviews(self.request(staff))
        self.assertFalse(cast(RetentionPage, result).items[0].can_approve)  # scoped ticket denial
        decision = decide_review(
            self.request(staff), review.pk, RetentionDecision(action="approve")
        )
        self.assertIsInstance(decision, tuple)
        self.assertEqual(cast(tuple[int, object], decision)[0], 403)
        self.assertTrue(Lead.objects.filter(pk=self.lead.pk).exists())

    def test_unprivileged_users_cannot_view_scan_or_decide(self) -> None:
        review = self.review()
        staff = self.staff("crm.view_lead")
        for result in [
            list_reviews(self.request(staff)),
            scan_reviews(self.request(staff)),
            decide_review(
                self.request(staff),
                review.pk,
                RetentionDecision(action="keep", reason="Keep", months=6),
            ),
        ]:
            self.assertIsInstance(result, tuple)
            self.assertEqual(cast(tuple[int, object], result)[0], 403)
        with self.assertRaises(PermissionError):
            approve_retention_review(review.pk, staff)

    def test_calendar_months_handle_leap_day(self) -> None:
        date = timezone.now().replace(year=2024, month=2, day=29)
        self.assertEqual(add_months(date, 36).day, 28)
        self.assertEqual(add_months(date, 36).year, 2027)

    def test_time_linked_conversation_is_protected(self) -> None:
        ticket = self.ticket()
        TimeEntry.objects.create(
            ticket=ticket, user=self.admin, date=self.old.date(), duration_hours=1
        )
        self.assertFalse(assess_lead(self.lead).eligible)
        self.assertEqual(refresh_retention_reviews()["queued"], 0)

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils import timezone

from apps.clients.models import Client, ClientContact
from apps.core.models import Brand
from apps.ticketing.models import (
    Mailbox,
    MicrosoftGraphConnection,
    Ticket,
    TicketAttachment,
    TicketMessage,
    TicketNote,
    TicketQueue,
)

DEMO_PREFIX = "[DEMO]"


class Command(BaseCommand):
    help = "Populate ticketing development data with realistic multi-message support threads."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--reset", action="store_true")
        parser.add_argument("--scale", type=int, default=1)
        parser.add_argument("--force", action="store_true")

    def handle(self, *args: Any, **options: Any) -> None:
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "Refusing to seed ticketing data when DEBUG is disabled. Use --force in disposable environments."
            )

        scale = max(1, options["scale"])
        if options["reset"]:
            Ticket.objects.filter(subject__startswith=DEMO_PREFIX).delete()
            Mailbox.objects.filter(display_name__startswith=DEMO_PREFIX).delete()
            MicrosoftGraphConnection.objects.filter(name__startswith=DEMO_PREFIX).delete()
            TicketQueue.objects.filter(key__startswith="demo-").delete()

        brands = list(Brand.objects.filter(is_active=True).order_by("id"))
        clients = list(
            Client.objects.filter(status="active").prefetch_related("contacts").order_by("id")
        )
        if not brands:
            raise CommandError("Seed the core platform first so active brands exist.")
        if not clients:
            raise CommandError("Seed the core platform first so active clients exist.")

        queues = self._create_queues(brands)
        graph_connection = self._create_graph_connection()
        mailboxes = self._create_mailboxes(graph_connection, brands, queues)
        staff_user = get_user_model().objects.filter(is_staff=True).order_by("id").first()
        now = timezone.now()
        ticket_count = max(18, 18 * scale)

        statuses = [
            Ticket.Status.NEW,
            Ticket.Status.OPEN,
            Ticket.Status.WAITING_CUSTOMER,
            Ticket.Status.WAITING_INTERNAL,
            Ticket.Status.RESOLVED,
            Ticket.Status.CLOSED,
        ]
        priorities = [
            Ticket.Priority.NORMAL,
            Ticket.Priority.NORMAL,
            Ticket.Priority.HIGH,
            Ticket.Priority.URGENT,
            Ticket.Priority.LOW,
        ]
        classifications = [
            Ticket.Classification.CLIENT_SUPPORT,
            Ticket.Classification.CLIENT_SUPPORT,
            Ticket.Classification.SALES,
            Ticket.Classification.ACCOUNTS,
            Ticket.Classification.VENDOR,
            Ticket.Classification.AUTOMATED_SYSTEM,
            Ticket.Classification.PROBABLE_SPAM,
        ]

        created = 0
        for index in range(ticket_count):
            brand = brands[index % len(brands)]
            queue_key = "support"
            mailbox_key = "support"
            classification = classifications[index % len(classifications)]
            if classification == Ticket.Classification.SALES:
                queue_key = "sales"
                mailbox_key = "sales"
            elif classification == Ticket.Classification.ACCOUNTS:
                queue_key = "accounts"
                mailbox_key = "accounts"
            elif classification in {
                Ticket.Classification.VENDOR,
                Ticket.Classification.AUTOMATED_SYSTEM,
            }:
                queue_key = "operations"
                mailbox_key = "operations"
            elif classification == Ticket.Classification.PROBABLE_SPAM:
                queue_key = "quarantine"

            queue = queues[(brand.id, queue_key)]
            mailbox = mailboxes[(brand.id, mailbox_key)]
            client = (
                clients[index % len(clients)]
                if classification != Ticket.Classification.PROBABLE_SPAM
                else None
            )
            contact = None
            if client is not None:
                contact = client.contacts.filter(is_active=True).order_by("id").first()

            last_message_at = now - timedelta(hours=index * 3)
            status = statuses[index % len(statuses)]
            ticket = Ticket.objects.create(
                brand=brand,
                queue=queue,
                mailbox=mailbox,
                client=client,
                primary_contact=contact,
                subject=f"{DEMO_PREFIX} {self._subject_for(index, classification)}",
                status=status,
                priority=priorities[index % len(priorities)],
                classification=classification,
                source=Ticket.Source.EMAIL if index % 4 else Ticket.Source.CONTACT_FORM,
                assigned_to=staff_user if index % 3 else None,
                first_response_at=last_message_at + timedelta(minutes=24) if index % 4 else None,
                last_message_at=last_message_at,
                resolved_at=last_message_at if status == Ticket.Status.RESOLVED else None,
                closed_at=last_message_at if status == Ticket.Status.CLOSED else None,
            )
            self._create_thread(ticket, contact, staff_user, last_message_at, index)
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created} demo tickets across {len(queues)} queues and {len(mailboxes)} mailboxes."
            )
        )

    def _create_graph_connection(self) -> MicrosoftGraphConnection:
        connection, _ = MicrosoftGraphConnection.objects.update_or_create(
            tenant_id="00000000-0000-0000-0000-000000000001",
            client_id="00000000-0000-0000-0000-000000000002",
            defaults={
                "name": f"{DEMO_PREFIX} Microsoft 365",
                "authentication_method": MicrosoftGraphConnection.AuthenticationMethod.CERTIFICATE,
                "credential": None,
                "enabled": True,
                "last_error": "",
            },
        )
        return connection

    def _create_queues(self, brands: list[Brand]) -> dict[tuple[int, str], TicketQueue]:
        result: dict[tuple[int, str], TicketQueue] = {}
        definitions = [
            ("support", "Support", "Customer support", 10),
            ("sales", "Sales", "Sales and pre-sales enquiries", 20),
            ("accounts", "Accounts", "Billing and accounts", 30),
            ("operations", "Operations", "Vendors, systems and operational mail", 40),
            ("quarantine", "Quarantine", "Probable spam and suspicious mail", 90),
        ]
        for brand in brands:
            for key, name, purpose, ordering in definitions:
                queue, _ = TicketQueue.objects.update_or_create(
                    key=f"demo-{brand.slug}-{key}",
                    defaults={
                        "name": f"{brand.name} {name}",
                        "brand": brand,
                        "purpose": purpose,
                        "default_priority": Ticket.Priority.NORMAL,
                        "enabled": True,
                        "ordering": ordering,
                    },
                )
                result[(brand.id, key)] = queue
        return result

    def _create_mailboxes(
        self,
        connection: MicrosoftGraphConnection,
        brands: list[Brand],
        queues: dict[tuple[int, str], TicketQueue],
    ) -> dict[tuple[int, str], Mailbox]:
        result: dict[tuple[int, str], Mailbox] = {}
        purposes = [
            (Mailbox.Purpose.SUPPORT, "support"),
            (Mailbox.Purpose.SALES, "sales"),
            (Mailbox.Purpose.ACCOUNTS, "accounts"),
            (Mailbox.Purpose.OPERATIONS, "operations"),
        ]
        for brand in brands:
            for purpose, queue_key in purposes:
                mailbox, _ = Mailbox.objects.update_or_create(
                    graph_connection=connection,
                    email_address=f"demo-{purpose}@{brand.domain}",
                    defaults={
                        "display_name": f"{DEMO_PREFIX} {brand.name} {purpose.title()}",
                        "brand": brand,
                        "purpose": purpose,
                        "default_queue": queues[(brand.id, queue_key)],
                        "enabled": True,
                        "last_error": "",
                    },
                )
                result[(brand.id, queue_key)] = mailbox
        return result

    def _create_thread(
        self,
        ticket: Ticket,
        contact: ClientContact | None,
        staff_user: Any | None,
        last_message_at: datetime,
        index: int,
    ) -> None:
        sender_name = contact.name if contact else "Unknown Sender"
        sender_address = contact.email if contact else f"unknown-{index}@example.test"
        inbound_at = last_message_at - timedelta(hours=2)
        inbound_recipient = (
            ticket.mailbox.email_address
            if ticket.mailbox
            else f"support@{ticket.brand.domain}"
        )
        inbound = TicketMessage.objects.create(
            ticket=ticket,
            direction=TicketMessage.Direction.INBOUND,
            sender_name=sender_name,
            sender_address=sender_address,
            to_recipients=[inbound_recipient],
            matched_contact=contact,
            subject=ticket.subject.removeprefix(f"{DEMO_PREFIX} "),
            body_text=(
                "Hello, this is a realistic development ticket used to exercise the support "
                "workspace.\n\nRegards,\nDemo Customer"
            ),
            body_text_normalised=(
                "Hello, this is a realistic development ticket used to exercise the support workspace."
            ),
            provider="demo",
            provider_message_id=f"demo-inbound-{ticket.reference}",
            internet_message_id=f"<demo-inbound-{ticket.reference}@example.test>",
            sent_or_received_at=inbound_at,
            delivery_status="received",
        )

        if index % 5 == 0:
            TicketAttachment.objects.create(
                message=inbound,
                original_filename=f"diagnostic-{index}.txt",
                declared_content_type="text/plain",
                detected_content_type="text/plain",
                size=2048 + index,
                sha256=f"{index:064x}"[-64:],
                scan_status=TicketAttachment.ScanStatus.SAFE,
                scan_engine="demo-clamav",
                scan_result="No threats found",
                quarantined_at=inbound_at,
                scanned_at=inbound_at + timedelta(minutes=1),
                safe_at=inbound_at + timedelta(minutes=1),
            )

        if index % 4 != 0:
            TicketMessage.objects.create(
                ticket=ticket,
                direction=TicketMessage.Direction.OUTBOUND,
                sender_name="ADB Support",
                sender_address=inbound_recipient,
                to_recipients=[sender_address],
                subject=(
                    f"Re: [{ticket.reference}] "
                    f"{ticket.subject.removeprefix(f'{DEMO_PREFIX} ')}"
                ),
                body_text=(
                    "Thanks for getting in touch. We are looking into this and will update you shortly."
                ),
                body_text_normalised=(
                    "Thanks for getting in touch. We are looking into this and will update you shortly."
                ),
                provider="demo",
                provider_message_id=f"demo-outbound-{ticket.reference}",
                internet_message_id=f"<demo-outbound-{ticket.reference}@example.test>",
                in_reply_to=f"<demo-inbound-{ticket.reference}@example.test>",
                references=[f"<demo-inbound-{ticket.reference}@example.test>"],
                sent_or_received_at=last_message_at,
                delivery_status="sent",
                created_by=staff_user,
            )

        if index % 6 == 0:
            TicketNote.objects.create(
                ticket=ticket,
                author=staff_user,
                body=(
                    "Demo internal note: check the client's infrastructure and recent project "
                    "history before the next reply."
                ),
            )

    def _subject_for(self, index: int, classification: Ticket.Classification) -> str:
        subjects: dict[Ticket.Classification, str] = {
            Ticket.Classification.CLIENT_SUPPORT: "Website issue needs investigation",
            Ticket.Classification.SALES: "New software project enquiry",
            Ticket.Classification.ACCOUNTS: "Question about an invoice",
            Ticket.Classification.VENDOR: "Vendor renewal notice",
            Ticket.Classification.AUTOMATED_SYSTEM: "Monitoring notification received",
            Ticket.Classification.PROBABLE_SPAM: "Suspicious unsolicited message",
        }
        return f"{subjects.get(classification, 'General enquiry')} #{index + 1}"

from datetime import date
from io import StringIO

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase

from apps.clients.models import Client, Project, TimeEntry
from apps.core.ownership import OwnershipType
from apps.credentials.models import StoredCredential
from apps.infrastructure.models import (
    API,
    Bot,
    EmailSystem,
    MobileApp,
    SSLCertificate,
    WebsiteTechStack,
)
from apps.knowledge_base.models import KnowledgeBaseDocument, KnowledgeBaseSection
from apps.tasks.models import Task, TaskList


class OperationalOwnershipTests(TestCase):
    def setUp(self) -> None:
        self.client_account = Client.objects.create(
            name="Example contact",
            company="Example Client",
            email="client@example.test",
        )
        self.client_project = Project.objects.create(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_account,
            name="Client project",
            start_date=date(2026, 1, 1),
        )
        self.internal_project = Project.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            client=None,
            name="Internal project",
            start_date=date(2026, 1, 1),
        )

    def test_client_owned_project_requires_client(self) -> None:
        project = Project(
            ownership_type=OwnershipType.CLIENT,
            client=None,
            name="Invalid project",
            start_date=date(2026, 1, 1),
        )

        with self.assertRaises(ValidationError):
            project.full_clean()

    def test_internal_project_rejects_client(self) -> None:
        project = Project(
            ownership_type=OwnershipType.INTERNAL,
            client=self.client_account,
            name="Invalid internal project",
            start_date=date(2026, 1, 1),
        )

        with self.assertRaises(ValidationError):
            project.full_clean()

    def test_time_entry_derives_ownership_from_project(self) -> None:
        entry = TimeEntry.objects.create(
            project=self.client_project,
            date=date(2026, 1, 2),
            duration_hours="1.50",
            description="Project work",
        )

        self.assertEqual(entry.ownership_type, OwnershipType.CLIENT)
        self.assertEqual(entry.client, self.client_account)

    def test_internal_time_entry_can_exist_without_project(self) -> None:
        entry = TimeEntry(
            ownership_type=OwnershipType.INTERNAL,
            client=None,
            project=None,
            date=date(2026, 1, 2),
            duration_hours="0.50",
            description="Internal admin",
        )

        entry.full_clean()
        entry.save()
        self.assertIsNone(entry.client)
        self.assertIsNone(entry.project)

    def test_task_rejects_project_from_different_ownership_context(self) -> None:
        task = Task(
            ownership_type=OwnershipType.INTERNAL,
            client=None,
            project=self.client_project,
            title="Mismatched task",
        )

        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_task_list_and_task_support_standalone_internal_work(self) -> None:
        task_list = TaskList.objects.create(
            ownership_type=OwnershipType.INTERNAL,
            name="Internal operations",
        )
        task = Task(
            ownership_type=OwnershipType.INTERNAL,
            task_list=task_list,
            title="Prepare monthly invoice reminders",
        )

        task.full_clean()
        task.save()
        self.assertIsNone(task.client)
        self.assertIsNone(task.project)

    def test_knowledge_document_supports_client_ownership(self) -> None:
        section = KnowledgeBaseSection.objects.create(name="Setup")
        document = KnowledgeBaseDocument(
            ownership_type=OwnershipType.CLIENT,
            client=self.client_account,
            section=section,
            title="Client setup",
            content="# Setup",
        )

        document.full_clean()
        document.save()
        self.assertEqual(document.client, self.client_account)

    def test_credential_supports_internal_ownership(self) -> None:
        credential = StoredCredential(
            ownership_type=OwnershipType.INTERNAL,
            client=None,
            name="Internal demo credential",
        )

        credential.full_clean()
        credential.save()
        self.assertIsNone(credential.client)


class DevelopmentSeedCommandTests(TestCase):
    def test_seed_command_builds_relational_demo_dataset(self) -> None:
        output = StringIO()

        call_command("seed_development", "--reset", "--force", stdout=output)

        self.assertGreaterEqual(
            Client.objects.filter(company__startswith="[DEMO]").count(),
            18,
        )
        self.assertGreaterEqual(
            Project.objects.filter(name__startswith="[DEMO]").count(),
            28,
        )
        self.assertGreaterEqual(
            Task.objects.filter(title__startswith="[DEMO]").count(),
            100,
        )
        self.assertGreaterEqual(
            KnowledgeBaseDocument.objects.filter(title__startswith="[DEMO]").count(),
            36,
        )
        self.assertGreaterEqual(
            StoredCredential.objects.filter(name__startswith="[DEMO]").count(),
            20,
        )
        self.assertIn("Development data ready", output.getvalue())

    def test_seed_command_can_reset_without_duplicating_demo_clients(self) -> None:
        call_command(
            "seed_development",
            "--reset",
            "--force",
            stdout=StringIO(),
        )
        first_count = Client.objects.filter(company__startswith="[DEMO]").count()

        call_command(
            "seed_development",
            "--reset",
            "--force",
            stdout=StringIO(),
        )
        second_count = Client.objects.filter(company__startswith="[DEMO]").count()

        self.assertEqual(first_count, second_count)

    def test_full_seed_command_populates_extended_infrastructure(self) -> None:
        output = StringIO()

        call_command("seed_all_development", "--reset", "--force", stdout=output)

        self.assertGreater(WebsiteTechStack.objects.count(), 0)
        self.assertGreater(SSLCertificate.objects.count(), 0)
        self.assertGreater(
            MobileApp.objects.filter(name__startswith="[DEMO]").count(),
            0,
        )
        self.assertGreater(
            API.objects.filter(name__startswith="[DEMO]").count(),
            0,
        )
        self.assertGreater(
            Bot.objects.filter(name__startswith="[DEMO]").count(),
            0,
        )
        self.assertGreater(
            EmailSystem.objects.filter(notes__startswith="[DEMO]").count(),
            0,
        )
        self.assertIn("Full platform development data ready", output.getvalue())

from __future__ import annotations

import random
from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.clients.models import Client, ClientContact, Project, ProjectNote, TimeEntry
from apps.core.models import AuditEvent, Brand
from apps.credentials.models import CredentialType, StoredCredential
from apps.crm.models import Lead, LeadSource, LeadStatus
from apps.infrastructure.models import Application, Database, Domain, Licence, Server, Website
from apps.knowledge_base.models import DocumentVersion, KnowledgeBaseDocument, KnowledgeBaseSection
from apps.tasks.models import Task, TaskList, TaskStatus
from apps.website.models import (
    FAQ,
    BlogCategory,
    BlogPost,
    BlogTag,
    FAQCategory,
    Portfolio,
    Testimonial,
)

DEMO_PREFIX = "[DEMO]"


class Command(BaseCommand):
    help = "Populate the development database with deterministic, obviously fake platform data."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--reset",
            action="store_true",
            help=("Delete previously generated demo records before creating a fresh data set."),
        )
        parser.add_argument(
            "--scale",
            type=int,
            default=1,
            help="Multiply generated record counts. Defaults to 1.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help=(
                "Allow running when DEBUG is disabled. Intended only for disposable environments."
            ),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "seed_development is disabled when DEBUG=False. Use --force only "
                "in a disposable environment."
            )

        scale = max(1, options["scale"])
        rng = random.Random(20260818)

        with transaction.atomic():
            if options["reset"]:
                self._reset_demo_data()

            brands = self._seed_brands()
            clients = self._seed_clients(rng, scale)
            projects = self._seed_projects(rng, clients, scale)
            self._seed_time_entries(rng, projects, scale)
            self._seed_leads(rng, brands, scale)
            self._seed_tasks(rng, projects, scale)
            self._seed_knowledge_base(rng, clients, scale)
            self._seed_credentials(rng, clients, scale)
            infrastructure = self._seed_infrastructure(rng, scale)
            self._seed_content(rng, brands, scale)
            self._seed_audit_events(rng, clients, projects, infrastructure, scale)

        self.stdout.write(
            self.style.SUCCESS(
                f"Development data ready (scale={scale}). Run again with --reset to rebuild it."
            )
        )

    def _reset_demo_data(self) -> None:
        Portfolio.objects.filter(title__startswith=DEMO_PREFIX).delete()
        Testimonial.objects.filter(company__startswith=DEMO_PREFIX).delete()
        BlogPost.objects.filter(title__startswith=DEMO_PREFIX).delete()
        BlogCategory.objects.filter(name__startswith=DEMO_PREFIX).delete()
        BlogTag.objects.filter(name__startswith=DEMO_PREFIX).delete()
        FAQ.objects.filter(question__startswith=DEMO_PREFIX).delete()
        FAQCategory.objects.filter(name__startswith=DEMO_PREFIX).delete()

        AuditEvent.objects.filter(target_label__startswith=DEMO_PREFIX).delete()
        StoredCredential.objects.filter(name__startswith=DEMO_PREFIX).delete()
        KnowledgeBaseDocument.objects.filter(title__startswith=DEMO_PREFIX).delete()
        Task.objects.filter(title__startswith=DEMO_PREFIX).delete()
        TaskList.objects.filter(name__startswith=DEMO_PREFIX).delete()
        Lead.objects.filter(company__startswith=DEMO_PREFIX).delete()
        Application.objects.filter(name__startswith=DEMO_PREFIX).delete()
        Licence.objects.filter(name__startswith=DEMO_PREFIX).delete()
        Domain.objects.filter(domain_name__startswith="demo-").delete()
        Website.objects.filter(name__startswith=DEMO_PREFIX).delete()
        Database.objects.filter(name__startswith=DEMO_PREFIX).delete()
        Server.objects.filter(hostname__startswith="demo-").delete()
        Client.objects.filter(company__startswith=DEMO_PREFIX).delete()

    def _seed_brands(self) -> list[Brand]:
        values = [
            (
                "ADB Software Solutions",
                "adb-software-solutions",
                "adbsoftwaresolutions.co.uk",
            ),
            ("ADB Web Designs", "adb-web-designs", "adbwebdesigns.co.uk"),
            ("ADB Technology", "adb-technology", "adbtechnology.co.uk"),
        ]
        brands = []
        for name, slug, domain in values:
            brand, _ = Brand.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "domain": domain, "is_active": True},
            )
            brands.append(brand)
        return brands

    def _seed_clients(self, rng: random.Random, scale: int) -> list[Client]:
        industries = [
            "Travel",
            "Retail",
            "Hospitality",
            "Construction",
            "Media",
            "Professional Services",
        ]
        cities = [
            "Manchester",
            "Leeds",
            "Liverpool",
            "London",
            "Bristol",
            "Edinburgh",
        ]
        clients = []
        for index in range(1, (18 * scale) + 1):
            company = f"{DEMO_PREFIX} {rng.choice(industries)} Company {index:02d}"
            client, _ = Client.objects.update_or_create(
                email=f"demo-client-{index}@example.test",
                defaults={
                    "name": f"Demo Contact {index:02d}",
                    "company": company,
                    "phone": f"0161 555 {index:04d}",
                    "address": f"{index} Example Street",
                    "city": rng.choice(cities),
                    "country": "United Kingdom",
                    "postal_code": f"M{(index % 9) + 1} 1AA",
                    "status": rng.choices(
                        ["active", "inactive"],
                        weights=[9, 1],
                    )[0],
                    "notes": (
                        "Generated development client. No person or company "
                        "represented by this record is real."
                    ),
                },
            )
            clients.append(client)
            for contact_index in range(1, 4):
                ClientContact.objects.update_or_create(
                    client=client,
                    email=f"demo-contact-{index}-{contact_index}@example.test",
                    defaults={
                        "name": f"Demo Person {index}-{contact_index}",
                        "phone": f"0161 556 {index:02d}{contact_index:02d}",
                        "role": rng.choice(
                            [
                                "Director",
                                "Operations Manager",
                                "Marketing Manager",
                                "Technical Contact",
                            ]
                        ),
                        "is_active": True,
                        "is_primary": contact_index == 1,
                        "is_billing": contact_index == 2,
                        "is_technical": contact_index == 3,
                    },
                )
        return clients

    def _seed_projects(
        self,
        rng: random.Random,
        clients: list[Client],
        scale: int,
    ) -> list[Project]:
        today = timezone.localdate()
        project_types = [
            "Website rebuild",
            "Platform integration",
            "Support retainer",
            "Cloud migration",
            "Automation project",
        ]
        projects = []
        for index in range(1, (28 * scale) + 1):
            client = clients[(index - 1) % len(clients)]
            start = today - timedelta(days=rng.randint(5, 300))
            status = rng.choices(
                ["planning", "active", "paused", "completed"],
                weights=[2, 6, 1, 3],
            )[0]
            project, _ = Project.objects.update_or_create(
                client=client,
                name=f"{DEMO_PREFIX} {rng.choice(project_types)} {index:02d}",
                defaults={
                    "ownership_type": "client",
                    "description": (
                        "Generated project used to exercise the development admin interface."
                    ),
                    "status": status,
                    "start_date": start,
                    "end_date": (
                        start + timedelta(days=rng.randint(30, 150))
                        if status == "completed"
                        else None
                    ),
                    "budget": Decimal(str(rng.choice([1200, 2500, 5000, 7500, 12000]))),
                    "hourly_rate": Decimal(str(rng.choice([45, 55, 65, 75, 85]))),
                },
            )
            projects.append(project)
            for note_index in range(2):
                ProjectNote.objects.get_or_create(
                    project=project,
                    content=(
                        f"{DEMO_PREFIX} Project note {note_index + 1} for development UI testing."
                    ),
                )
        return projects

    def _seed_time_entries(
        self,
        rng: random.Random,
        projects: list[Project],
        scale: int,
    ) -> None:
        today = timezone.localdate()
        target = 140 * scale
        existing = TimeEntry.objects.filter(description__startswith=DEMO_PREFIX).count()
        for index in range(existing, target):
            TimeEntry.objects.create(
                project=projects[index % len(projects)],
                date=today - timedelta(days=rng.randint(0, 90)),
                duration_hours=Decimal(str(rng.choice([0.5, 1, 1.5, 2, 2.5, 3, 4, 6]))),
                description=f"{DEMO_PREFIX} Development work entry {index + 1}",
                billable=rng.random() > 0.2,
            )

    def _seed_leads(
        self,
        rng: random.Random,
        brands: list[Brand],
        scale: int,
    ) -> None:
        statuses = [
            ("New", 10),
            ("Contacted", 20),
            ("Qualified", 30),
            ("Proposal", 40),
            ("Won", 50),
            ("Lost", 60),
        ]
        lead_statuses = [
            LeadStatus.objects.update_or_create(
                name=name,
                defaults={"order": order},
            )[0]
            for name, order in statuses
        ]
        sources = [
            LeadSource.objects.get_or_create(name=name)[0]
            for name in [
                "Contact form",
                "Referral",
                "LinkedIn",
                "Organic search",
                "Fiverr",
                "Social media",
            ]
        ]
        for index in range(1, (45 * scale) + 1):
            Lead.objects.update_or_create(
                email=f"demo-lead-{index}@example.test",
                defaults={
                    "brand": brands[index % len(brands)],
                    "name": f"Demo Lead {index:02d}",
                    "company": f"{DEMO_PREFIX} Prospect {index:02d}",
                    "phone": f"0161 557 {index:04d}",
                    "status": rng.choice(lead_statuses),
                    "source": rng.choice(sources),
                    "message": (
                        "Generated enquiry about a website, software project or IT service."
                    ),
                    "notes": "Fake development CRM data.",
                },
            )

    def _seed_tasks(
        self,
        rng: random.Random,
        projects: list[Project],
        scale: int,
    ) -> None:
        statuses = [
            ("Backlog", "#64748b", 10),
            ("To do", "#38bdf8", 20),
            ("In progress", "#f59e0b", 30),
            ("Blocked", "#ef4444", 40),
            ("Done", "#22c55e", 50),
        ]
        task_statuses = [
            TaskStatus.objects.update_or_create(
                name=name,
                defaults={"color": color, "order": order},
            )[0]
            for name, color, order in statuses
        ]
        internal_lists = []
        for name in ["Operations", "Development", "Recurring admin"]:
            task_list, _ = TaskList.objects.update_or_create(
                name=f"{DEMO_PREFIX} {name}",
                defaults={
                    "ownership_type": "internal",
                    "client": None,
                    "project": None,
                    "description": "Generated development task list.",
                },
            )
            internal_lists.append(task_list)

        today = timezone.localdate()
        for index in range(1, (90 * scale) + 1):
            project = projects[index % len(projects)]
            title = (
                f"{DEMO_PREFIX} Task {index:03d} — {project.name.removeprefix(DEMO_PREFIX).strip()}"
            )
            Task.objects.update_or_create(
                title=title,
                defaults={
                    "ownership_type": project.ownership_type,
                    "client": project.client,
                    "project": project,
                    "description": (
                        f"Generated task for {project.client}. Used to populate operational queues."
                    ),
                    "task_list": None,
                    "status": rng.choice(task_statuses),
                    "priority": rng.choices(
                        [1, 2, 3, 4],
                        weights=[2, 6, 3, 1],
                    )[0],
                    "due_date": today + timedelta(days=rng.randint(-14, 45)),
                },
            )

        for index in range(1, (15 * scale) + 1):
            Task.objects.update_or_create(
                title=f"{DEMO_PREFIX} Internal operations task {index:03d}",
                defaults={
                    "ownership_type": "internal",
                    "client": None,
                    "project": None,
                    "description": "Generated standalone internal operational task.",
                    "task_list": rng.choice(internal_lists),
                    "status": rng.choice(task_statuses),
                    "priority": rng.choice([1, 2, 3]),
                    "due_date": today + timedelta(days=rng.randint(-7, 30)),
                },
            )

    def _seed_knowledge_base(
        self,
        rng: random.Random,
        clients: list[Client],
        scale: int,
    ) -> None:
        sections = [
            KnowledgeBaseSection.objects.update_or_create(
                name=name,
                defaults={"description": description, "order": order},
            )[0]
            for order, (name, description) in enumerate(
                [
                    ("Setup", "Initial setup and onboarding procedures"),
                    ("Deployments", "Deployment and rollback procedures"),
                    ("Maintenance", "Routine maintenance documentation"),
                    ("Troubleshooting", "Known issues and recovery procedures"),
                ],
                start=10,
            )
        ]
        for index in range(1, (36 * scale) + 1):
            client = clients[index % len(clients)]
            document, _ = KnowledgeBaseDocument.objects.update_or_create(
                title=(
                    f"{DEMO_PREFIX} "
                    f"{client.company.removeprefix(DEMO_PREFIX).strip()} "
                    f"procedure {index:02d}"
                ),
                defaults={
                    "ownership_type": "client",
                    "client": client,
                    "section": rng.choice(sections),
                    "content": (
                        "# Development article\n\n"
                        "This is generated internal documentation for exercising "
                        "search, navigation and ticket-side context.\n\n"
                        "## Procedure\n\n"
                        "1. Confirm the environment.\n"
                        "2. Review monitoring and logs.\n"
                        "3. Record the outcome."
                    ),
                },
            )
            DocumentVersion.objects.get_or_create(
                document=document,
                version_number=1,
                defaults={"content": document.content},
            )

    def _seed_credentials(
        self,
        rng: random.Random,
        clients: list[Client],
        scale: int,
    ) -> None:
        types = [
            CredentialType.objects.get_or_create(name=name)[0]
            for name in [
                "Website login",
                "SSH",
                "Database",
                "API key",
                "Microsoft 365",
            ]
        ]
        for index in range(1, (20 * scale) + 1):
            client = clients[index % len(clients)]
            StoredCredential.objects.update_or_create(
                name=(
                    f"{DEMO_PREFIX} "
                    f"{client.company.removeprefix(DEMO_PREFIX).strip()} "
                    f"credential {index:02d}"
                ),
                defaults={
                    "ownership_type": "client",
                    "client": client,
                    "credential_type": rng.choice(types),
                    "username": f"demo-user-{index}",
                    "password": "demo-password-not-a-real-secret",
                    "api_key": ("demo-api-key-not-a-real-secret" if index % 4 == 0 else ""),
                    "url": f"https://demo-{index}.example.test",
                    "notes": (
                        "Generated placeholder credential. Never replace with a real secret."
                    ),
                },
            )

    def _seed_infrastructure(
        self,
        rng: random.Random,
        scale: int,
    ) -> list[object]:
        servers = []
        for index in range(1, (14 * scale) + 1):
            server, _ = Server.objects.update_or_create(
                hostname=f"demo-web-{index:02d}.example.test",
                defaults={
                    "role": rng.choice(["web", "database", "management", "backup"]),
                    "provider": "do",
                    "region": rng.choice(["lon1", "fra1", "nyc3"]),
                    "os": "ubuntu_24",
                    "cpu": rng.choice(["2 vCPU", "4 vCPU", "8 vCPU"]),
                    "ram_gb": rng.choice([2, 4, 8, 16]),
                    "disk_gb": rng.choice([50, 80, 160, 320]),
                    "virtualization_type": "vm",
                    "notes": "Generated development infrastructure record.",
                },
            )
            servers.append(server)

        databases = []
        for index in range(1, (8 * scale) + 1):
            database, _ = Database.objects.update_or_create(
                name=f"{DEMO_PREFIX} PostgreSQL {index:02d}",
                defaults={
                    "db_type": "postgres",
                    "provider": "self_hosted",
                    "server": servers[index % len(servers)],
                    "version": "17",
                    "backup_strategy": (
                        "Nightly encrypted backup with seven-day retention (demo data)."
                    ),
                },
            )
            databases.append(database)

        websites = []
        for index in range(1, (18 * scale) + 1):
            website, _ = Website.objects.update_or_create(
                primary_url=f"https://demo-site-{index}.example.test",
                defaults={
                    "name": f"{DEMO_PREFIX} Website {index:02d}",
                    "environment_type": rng.choice(["production", "staging"]),
                    "database": databases[index % len(databases)],
                    "admin_url": f"https://demo-site-{index}.example.test/admin",
                    "github_repository": "https://github.com/example/demo-repository",
                    "has_cdn": True,
                    "cdn_provider": "Cloudflare",
                    "cache_layer": "Redis",
                    "notes": "Generated development website record.",
                },
            )
            website.servers.set([servers[index % len(servers)]])
            websites.append(website)

        domains = []
        today = timezone.localdate()
        for index, website in enumerate(websites, start=1):
            domain, _ = Domain.objects.update_or_create(
                domain_name=f"demo-{index}.example.test",
                defaults={
                    "registrar": "cloudflare",
                    "expiry_date": today + timedelta(days=rng.randint(20, 600)),
                    "auto_renew": rng.random() > 0.1,
                    "nameservers": "demo1.example.test,demo2.example.test",
                },
            )
            domain.websites.set([website])
            domains.append(domain)

        licences = []
        for index in range(1, (12 * scale) + 1):
            licence, _ = Licence.objects.update_or_create(
                name=f"{DEMO_PREFIX} Software licence {index:02d}",
                defaults={
                    "licence_type": "subscription",
                    "vendor": rng.choice(["Demo Vendor", "Example Software", "Sample Cloud"]),
                    "renewal_date": today + timedelta(days=rng.randint(5, 365)),
                    "renewal_cost": Decimal(str(rng.choice([9, 19, 49, 99, 199]))),
                    "auto_renew": rng.random() > 0.15,
                    "portal_url": "https://example.test",
                    "licence_key": "DEMO-LICENCE-KEY-NOT-REAL",
                    "notes": "Generated development licence.",
                },
            )
            licence.websites.set([websites[index % len(websites)]])
            licences.append(licence)

        applications = []
        for index in range(1, (10 * scale) + 1):
            application, _ = Application.objects.update_or_create(
                name=f"{DEMO_PREFIX} Application {index:02d}",
                defaults={
                    "app_type": rng.choice(["web_app", "saas", "api"]),
                    "description": (
                        "Generated logical application for development inventory views."
                    ),
                    "status": "active",
                    "notes": "Fake development data.",
                },
            )
            application.websites.set([websites[index % len(websites)]])
            application.servers.set([servers[index % len(servers)]])
            application.databases.set([databases[index % len(databases)]])
            application.domains.set([domains[index % len(domains)]])
            application.licences.set([licences[index % len(licences)]])
            applications.append(application)

        return [*servers, *databases, *websites, *domains, *licences, *applications]

    def _seed_content(
        self,
        rng: random.Random,
        brands: list[Brand],
        scale: int,
    ) -> None:
        blog_categories = []
        for name in [
            "Engineering",
            "Web Development",
            "Infrastructure",
            "Business Technology",
        ]:
            blog_category, _ = BlogCategory.objects.update_or_create(
                slug=f"demo-{slugify(name)}",
                defaults={
                    "name": f"{DEMO_PREFIX} {name}",
                    "description": "Generated development category.",
                },
            )
            blog_category.brands.set(brands)
            blog_categories.append(blog_category)

        tags = []
        for name in [
            "Django",
            "Next.js",
            "DevOps",
            "Cloud",
            "Automation",
            "Security",
        ]:
            tag, _ = BlogTag.objects.update_or_create(
                slug=f"demo-{slugify(name)}",
                defaults={"name": f"{DEMO_PREFIX} {name}"},
            )
            tag.brands.set(brands)
            tags.append(tag)

        now = timezone.now()
        for index in range(1, (20 * scale) + 1):
            post, _ = BlogPost.objects.update_or_create(
                slug=f"demo-development-post-{index}",
                defaults={
                    "title": f"{DEMO_PREFIX} Development article {index:02d}",
                    "excerpt": (
                        "Generated CMS content used to validate multi-brand "
                        "administration and layouts."
                    ),
                    "content": (
                        "# Demo article\n\nThis content exists only in development environments."
                    ),
                    "author": "ADB Demo Data",
                    "published": True,
                    "featured": index % 5 == 0,
                    "published_at": now - timedelta(days=index * 2),
                    "meta_description": "Generated development article.",
                },
            )
            post.brands.set(rng.sample(brands, k=rng.randint(1, len(brands))))
            post.categories.set(rng.sample(blog_categories, k=rng.randint(1, 2)))
            post.tags.set(rng.sample(tags, k=rng.randint(1, 3)))

        faq_categories = []
        for order, name in enumerate(
            ["Services", "Support", "Billing", "Projects"],
            start=10,
        ):
            faq_category, _ = FAQCategory.objects.update_or_create(
                slug=f"demo-{slugify(name)}",
                defaults={
                    "name": f"{DEMO_PREFIX} {name}",
                    "description": "Generated development FAQ category.",
                    "order": order,
                },
            )
            faq_category.brands.set(brands)
            faq_categories.append(faq_category)

        for index in range(1, (24 * scale) + 1):
            faq, _ = FAQ.objects.update_or_create(
                question=f"{DEMO_PREFIX} Frequently asked question {index:02d}?",
                defaults={
                    "answer": (
                        "This is generated development content used to exercise the CMS interface."
                    ),
                    "category": faq_categories[index % len(faq_categories)],
                    "order": index,
                },
            )
            faq.brands.set(rng.sample(brands, k=rng.randint(1, len(brands))))

        for index in range(1, (12 * scale) + 1):
            testimonial, _ = Testimonial.objects.update_or_create(
                client_name=f"Demo Client {index:02d}",
                company=f"{DEMO_PREFIX} Testimonial Company {index:02d}",
                defaults={
                    "quote": ("Generated testimonial copy for development layout testing only."),
                    "job_title": "Director",
                    "rating": 5,
                    "featured": index % 4 == 0,
                },
            )
            testimonial.brands.set(rng.sample(brands, k=rng.randint(1, len(brands))))

        for index in range(1, (10 * scale) + 1):
            portfolio, _ = Portfolio.objects.update_or_create(
                slug=f"demo-case-study-{index}",
                defaults={
                    "title": f"{DEMO_PREFIX} Case study {index:02d}",
                    "description": "Generated portfolio entry for development.",
                    "challenge": ("A fictional client needed a reliable technology solution."),
                    "solution": ("A fictional multi-service implementation was delivered."),
                    "results": ("The generated project produced excellent fictional results."),
                    "featured": index % 3 == 0,
                    "technologies": "Django, Next.js, PostgreSQL, Docker",
                    "project_url": f"https://demo-project-{index}.example.test",
                },
            )
            portfolio.brands.set(rng.sample(brands, k=rng.randint(1, len(brands))))

    def _seed_audit_events(
        self,
        rng: random.Random,
        clients: list[Client],
        projects: list[Project],
        infrastructure: list[object],
        scale: int,
    ) -> None:
        targets = [*clients, *projects, *infrastructure]
        target = 70 * scale
        existing = AuditEvent.objects.filter(target_label__startswith=DEMO_PREFIX).count()
        actions = ["viewed", "updated", "created", "exported", "access_checked"]
        for index in range(existing, target):
            obj = rng.choice(targets)
            AuditEvent.record(
                action=rng.choice(actions),
                target=obj,
                target_label=f"{DEMO_PREFIX} {obj}",
                metadata={"generated": True, "sequence": index + 1},
                ip_address="192.0.2.10",
                user_agent="ADB development seed data",
            )

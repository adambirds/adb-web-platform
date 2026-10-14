"""Removable, Brand-scoped editorial previews for the two newer public sites."""

from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils import timezone

from apps.core.models import Brand
from apps.website.models import FAQ, BlogCategory, BlogPost, FAQCategory, Portfolio, Testimonial

BRANDS = {
    "software": ("adb-software-solutions", "demo-ss-", "Demo SS / "),
    "technology": ("adb-technology", "demo-tech-", "Demo Tech / "),
}
PROJECTS = {
    "software": [
        ("Order workspace", "web-applications", "Next.js, Django"),
        ("System connections", "api-integrations", "Python, APIs"),
        ("Field notes", "mobile-applications", "Mobile application, Django"),
    ],
    "technology": [
        ("Release workspace", "deployment-pipelines", "GitHub Actions, Docker"),
        ("Migration plan", "cloud-migrations", "Linux, PostgreSQL"),
        ("Server handover", "server-rebuilds", "Linux, Configuration management"),
    ],
}
ARTICLES = {
    "software": [
        "Planning an application around the work your team does",
        "What to include in an API integration brief",
        "Preparing an AI-built application for a code review",
    ],
    "technology": [
        "What belongs in a deployment pipeline",
        "Planning a migration with a rollback route",
        "What to document when handing over a server",
    ],
}
QUESTIONS = {
    "software": [
        "How does a software project start?",
        "Can you connect tools we already use?",
        "Can you review an app built with AI?",
        "Do you build mobile applications?",
        "Can the application be deployed as well?",
        "What should I include in an enquiry?",
    ],
    "technology": [
        "Can you help deploy an existing application?",
        "Can an existing server be rebuilt?",
        "How is a migration planned?",
        "Can you build a deployment pipeline?",
        "What is included in a handover?",
        "How are ongoing responsibilities agreed?",
    ],
}

QUESTION_SERVICES = {
    "software": [
        "web-applications",
        "api-integrations",
        "ai-code-review",
        "mobile-applications",
        "web-applications",
        None,
    ],
    "technology": [
        "app-deployment",
        "server-rebuilds",
        "cloud-migrations",
        "deployment-pipelines",
        None,
        "server-management",
    ],
}


def cover(kind: str, index: int) -> ContentFile:
    path = Path(__file__).resolve().parents[2] / "fixtures" / "public_brand_demo"
    return ContentFile((path / f"{kind}-{index + 1}.png").read_bytes())


def assign_brand(
    item: Portfolio | BlogPost | BlogCategory | FAQCategory | FAQ | Testimonial,
    created: bool,
    brand: Brand,
) -> None:
    if created:
        item.brands.set([brand])
    elif not item.brands.filter(pk=brand.pk).exists():
        raise CommandError("A reserved demo identifier already belongs to another record.")


class Command(BaseCommand):
    help = "Create clearly labelled local Software/Technology CMS previews; --clear removes them."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--brand", choices=["all", *BRANDS], default="all")
        parser.add_argument("--clear", action="store_true")

    def handle(self, *args: Any, **options: Any) -> None:
        if not settings.DEBUG or settings.DATABASES["default"]["HOST"] not in {
            "db",
            "localhost",
            "127.0.0.1",
            "postgres",
            "postgresql",
            "",
        }:
            raise CommandError(
                "Demo content is restricted to DEBUG mode and a local database host."
            )
        kinds = list(BRANDS) if options["brand"] == "all" else [options["brand"]]
        with transaction.atomic():
            for kind in kinds:
                slug, prefix, label = BRANDS[kind]
                try:
                    brand = Brand.objects.get(slug=slug)
                except Brand.DoesNotExist as error:
                    raise CommandError(
                        f"Create the platform Brand {slug} before seeding."
                    ) from error
                if options["clear"]:
                    self.clear(brand, prefix, label)
                else:
                    self.seed(kind, brand, prefix, label)
        self.stdout.write(
            self.style.SUCCESS(
                "Selected local demo content cleared."
                if options["clear"]
                else "Local CMS demos ready: 3 projects, 3 articles, 2 testimonials and 6 FAQs per selected Brand."
            )
        )

    def seed(self, kind: str, brand: Brand, prefix: str, label: str) -> None:
        category, created = BlogCategory.objects.get_or_create(
            slug=f"{prefix}notes",
            defaults={"name": f"{label}Notes", "description": "Fictional local preview content."},
        )
        assign_brand(category, created, brand)
        questions, created = FAQCategory.objects.get_or_create(
            slug=f"{prefix}questions",
            defaults={"name": f"{label}Questions"},
        )
        assign_brand(questions, created, brand)
        for index, (name, service, technologies) in enumerate(PROJECTS[kind]):
            item, created = Portfolio.objects.get_or_create(
                slug=f"{prefix}project-{index + 1}",
                defaults={
                    "title": f"{name} (demo)",
                    "description": "Fictional local preview project. This is not real client work.",
                    "challenge": f"## The starting point\n\n**Fictional demo:** {name} illustrates how a {brand.name} case study can describe a project. No real customer or engagement is represented.",
                    "solution": "## The approach\n\nThis sample shows where the agreed scope, implementation and technical decisions would be explained. The accompanying image is an original HTML/CSS concept with fictional data.",
                    "results": "## The handover\n\nThis is layout-preview content, not a claim of delivered results. A genuine case study would describe the completed work and handover.",
                    "technologies": technologies,
                    "service_slugs": [service],
                    "published": True,
                    "featured": index < 2,
                    "featured_image_alt": f"{name}: fictional application concept for local preview",
                },
            )
            assign_brand(item, created, brand)
            if created:
                item.featured_image.save(f"{prefix}project-{index + 1}.png", cover(kind, index))
        for index, title in enumerate(ARTICLES[kind]):
            post, created = BlogPost.objects.get_or_create(
                slug=f"{prefix}article-{index + 1}",
                defaults={
                    "title": f"{title} (demo)",
                    "excerpt": "Clearly labelled local demo article for reviewing the blog layout and navigation.",
                    "content": "## Local editorial preview\n\nThis is **fictional demonstration content**, not published advice or a record of client work.\n\n## A useful structure\n\nA real article can explain the starting situation, the decisions involved and the next useful step.\n\n- Describe the requirements.\n- Explain the options.\n- Make the practical details understandable.\n\n## Discuss your project\n\nUse the [contact form](/contact/) to talk about real work. Remove this demo before production launch.",
                    "author": "Demo editorial content",
                    "published": True,
                    "featured": index < 2,
                    "published_at": timezone.now(),
                    "featured_image_alt": "Fictional application concept used as a local editorial preview image",
                },
            )
            assign_brand(post, created, brand)
            if created:
                post.categories.set([category])
                post.featured_image.save(f"{prefix}article-{index + 1}.png", cover(kind, index))
        for index in range(2):
            quote, created = Testimonial.objects.get_or_create(
                client_name=f"{label}Sample client {index + 1}",
                defaults={
                    "company": "Fictional preview company",
                    "job_title": "Demonstration testimonial",
                    "quote": "This is a fictional testimonial for reviewing the design. It is not a real client endorsement.",
                    "published": True,
                    "featured": True,
                },
            )
            assign_brand(quote, created, brand)
        for index, question in enumerate(QUESTIONS[kind]):
            faq, created = FAQ.objects.get_or_create(
                question=f"{label}{question}",
                defaults={
                    "category": questions,
                    "answer": "**Local demo answer.** This placeholder demonstrates the FAQ layout. Replace it with the relevant answer in the CMS before publishing real content.",
                    "published": True,
                    "order": index,
                    "service_slugs": [QUESTION_SERVICES[kind][index]]
                    if QUESTION_SERVICES[kind][index]
                    else [],
                },
            )
            assign_brand(faq, created, brand)

    def clear(self, brand: Brand, prefix: str, label: str) -> None:
        for item in Portfolio.objects.filter(brands=brand, slug__startswith=prefix):
            item.image.delete(save=False)
            item.featured_image.delete(save=False)
            item.delete()
        for post in BlogPost.objects.filter(brands=brand, slug__startswith=prefix):
            post.featured_image.delete(save=False)
            post.delete()
        Testimonial.objects.filter(brands=brand, client_name__startswith=label).delete()
        FAQ.objects.filter(brands=brand, question__startswith=label).delete()
        for category in BlogCategory.objects.filter(brands=brand, slug__startswith=prefix):
            if not category.posts.exists():
                category.delete()
        for faq_category in FAQCategory.objects.filter(brands=brand, slug__startswith=prefix):
            if not faq_category.faqs.exists():
                faq_category.delete()

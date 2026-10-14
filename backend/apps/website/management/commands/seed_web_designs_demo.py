"""Local, removable editorial fixtures for the Web Designs design review."""

from pathlib import Path
from typing import Any, Literal

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils import timezone

from apps.core.models import Brand
from apps.website.models import FAQ, BlogCategory, BlogPost, FAQCategory, Portfolio, Testimonial

PREFIX = "demo-wd-"
CLIENT_PREFIX = "Demo WD / "
PROJECTS = [
    ("Fieldwork Studio", "web-design", "Next.js"),
    ("North & Grain", "ecommerce", "Shopify"),
    ("The Everyday Edit", "wordpress", "WordPress"),
    ("Common Ground", "website-rescue", "WordPress"),
    ("Chapter House", "web-design", "Next.js"),
    ("Slow Supply", "ecommerce", "Shopify"),
    ("Wildflower Kitchen", "website-maintenance", "Squarespace"),
    ("Good Company", "hosting", "WordPress"),
    ("The Local Workshop", "search-engine-optimisation", "WordPress"),
    ("Westward Goods", "ecommerce", "Shopify"),
    ("The Paper Room", "wordpress", "WordPress"),
    ("Neighbourhood Notes", "web-design", "Next.js"),
]
ARTICLES = [
    "What a useful website brief includes",
    "Choosing between WordPress and Next.js",
    "Planning an ecommerce website",
    "What to check before a website migration",
    "Technical SEO starts with the structure",
    "A practical website maintenance checklist",
    "Understanding a hacked website recovery",
    "Making website feedback more useful",
    "Designing for mobile visitors",
    "Keeping a website easy to edit",
    "Working remotely on a website project",
    "What belongs in a website handover",
]


def cover(kind: Literal["project", "article"], index: int) -> bytes:
    """Native HTML/CSS website concepts, rendered as bundled CMS fixture images."""
    path = Path(__file__).resolve().parents[2] / "fixtures" / "web_designs_demo"
    return (path / f"{kind}-{index + 1}.png").read_bytes()


class Command(BaseCommand):
    help = "Create published, clearly labelled Web Designs CMS demos in local development; --clear removes them."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Remove only this command's demo records and images.",
        )

        parser.add_argument(
            "--refresh-images",
            action="store_true",
            help="Replace only this command's Web Designs demo images with the bundled concepts.",
        )

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
        brand = Brand.objects.get(slug="adb-web-designs")
        if options["clear"]:
            self.clear(brand)
            return
        with transaction.atomic():
            category, _ = BlogCategory.objects.get_or_create(
                slug=f"{PREFIX}website-notes",
                defaults={
                    "name": "Website notes (demo)",
                    "description": "Fictional preview articles.",
                },
            )
            category.brands.set([brand])
            faq_category, _ = FAQCategory.objects.get_or_create(
                slug=f"{PREFIX}questions",
                defaults={
                    "name": "Working together (demo)",
                    "description": "Sample FAQs for design preview.",
                },
            )
            faq_category.brands.set([brand])
            for index, (name, service, technology) in enumerate(PROJECTS):
                item, created = Portfolio.objects.get_or_create(
                    slug=f"{PREFIX}project-{index + 1}",
                    defaults={
                        "title": f"{name} (demo)",
                        "description": "Fictional project for previewing the website design. This is not real client work.",
                        "challenge": "## A clearer starting point\n\nThis fictional business needs a website that makes its services and next steps easier to understand.\n\n- A useful page structure\n- Clear navigation\n- A readable mobile experience",
                        "solution": "## A website built around the brief\n\nThis sample case study demonstrates how project detail pages present the approach, platform and implementation. No real engagement is described here.",
                        "results": "## Ready for the next conversation\n\nThis is demonstration content, not a claim of delivered results. The actual case study would describe the work completed and agreed handover.",
                        "technologies": technology,
                        "published": True,
                        "featured": index < 2,
                        "service_slugs": [service],
                        "meta_description": "Clearly labelled fictional Web Designs project for local preview.",
                        "featured_image_alt": f"Fictional website design concept for {name}, local demo",
                    },
                )
                if created:
                    item.brands.set([brand])
                if created or (
                    options["refresh_images"] and item.brands.filter(pk=brand.pk).exists()
                ):
                    content = ContentFile(cover("project", index))
                    item.featured_image.delete(save=False)
                    item.featured_image_alt = (
                        f"Fictional website design concept for {name}, local demo"
                    )
                    item.featured_image.save(f"{PREFIX}project-{index + 1}.png", content, save=True)
            for index, title in enumerate(ARTICLES):
                post, created = BlogPost.objects.get_or_create(
                    slug=f"{PREFIX}article-{index + 1}",
                    defaults={
                        "title": f"{title} (demo)",
                        "excerpt": "Sample editorial content for reviewing the layout, typography and navigation. This article is a local demonstration.",
                        "content": "## Start with the purpose\n\nThis is a **demonstration article** for the design review, not published advice or a record of client work.\n\nA real article can include headings, useful explanations, lists and links. The page should remain comfortable to read on a phone as well as a larger screen.\n\n## Give the information a structure\n\n- Describe the starting situation.\n- Explain the decisions that matter.\n- Make the next step easy to find.\n\n> This quotation demonstrates the article layout.\n\n## A useful next step\n\nYou can [discuss a website project](/contact/) through the contact form.",
                        "author": "Demo editorial content",
                        "published": True,
                        "featured": index < 2,
                        "published_at": timezone.now(),
                        "meta_description": "Sample Web Designs editorial content for local design preview.",
                        "featured_image_alt": "Clearly labelled illustrative article cover",
                    },
                )
                if created:
                    post.brands.set([brand])
                    post.categories.set([category])
                if created or (
                    options["refresh_images"] and post.brands.filter(pk=brand.pk).exists()
                ):
                    content = ContentFile(cover("article", index))
                    post.featured_image.delete(save=False)
                    post.featured_image.save(f"{PREFIX}article-{index + 1}.png", content, save=True)
            for index in range(3):
                quote, created = Testimonial.objects.get_or_create(
                    client_name=f"{CLIENT_PREFIX}Sample client {index + 1}",
                    defaults={
                        "company": "Fictional business · Preview content",
                        "job_title": "Demonstration testimonial",
                        "quote": "This is a sample testimonial for reviewing the page design and text layout. It is not a real client endorsement.",
                        "published": True,
                        "featured": True,
                    },
                )
                if created:
                    quote.brands.set([brand])
            for index, question in enumerate(
                [
                    "How does a website project start?",
                    "Can an existing website be rebuilt?",
                    "What should I include in an enquiry?",
                    "How is a project handed over?",
                    "Can we work together remotely?",
                    "What about hosting and maintenance?",
                    "Can a hacked website be recovered?",
                    "Which platform should I choose?",
                    "How do website reviews work?",
                    "What happens after launch?",
                ]
            ):
                faq, created = FAQ.objects.get_or_create(
                    category=faq_category,
                    question=f"{question} (demo)",
                    defaults={
                        "answer": "This is a **sample answer** for previewing the FAQ layout. The actual scope and arrangements are discussed for each project. [Get in touch](/contact/) to describe the work you need.",
                        "published": True,
                        "order": index,
                        "service_slugs": ["web-design", "website-rescue"],
                    },
                )
                if created:
                    faq.brands.set([brand])
        self.stdout.write(
            self.style.SUCCESS(
                "Web Designs demo content ready: 12 projects, 12 articles, 3 testimonials and 10 FAQs. Repeat runs preserve existing records; use --clear to remove the demos."
            )
        )

    def clear(self, brand: Brand) -> None:
        with transaction.atomic():
            for model in (Portfolio, BlogPost):
                for item in model.objects.filter(slug__startswith=PREFIX, brands=brand):
                    item.featured_image.delete(save=False)
                    item.delete()
            Testimonial.objects.filter(client_name__startswith=CLIENT_PREFIX, brands=brand).delete()
            FAQ.objects.filter(category__slug__startswith=PREFIX, brands=brand).delete()
            BlogCategory.objects.filter(slug__startswith=PREFIX, brands=brand).delete()
            FAQCategory.objects.filter(slug__startswith=PREFIX, brands=brand).delete()
        self.stdout.write(
            self.style.SUCCESS("Removed the Web Designs demo content and its generated images.")
        )

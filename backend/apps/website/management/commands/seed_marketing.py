from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.crm.models import Lead, LeadSource, LeadStatus
from apps.website.models import (
    FAQ,
    BlogCategory,
    BlogPost,
    BlogTag,
    FAQCategory,
    Portfolio,
    Testimonial,
)


class Command(BaseCommand):
    help = "Seed marketing content (portfolio, blog, FAQs, testimonials)."

    def handle(self, *args, **options):
        lead_status, _ = LeadStatus.objects.get_or_create(name="New", defaults={"order": 0})
        lead_source, _ = LeadSource.objects.get_or_create(name="Contact Form")

        Lead.objects.get_or_create(
            email="hello@example.com",
            defaults={
                "name": "Sample Lead",
                "phone": "",
                "company": "Example Co",
                "message": "Looking for a web rebuild.",
                "status": lead_status,
                "source": lead_source,
            },
        )

        portfolio_items = [
            {
                "title": "Multi-tenant SaaS launch",
                "slug": "multi-tenant-saas-launch",
                "description": "Delivered a multi-tenant platform with analytics and billing.",
                "challenge": "Legacy tooling slowed down launches and reporting.",
                "solution": "Designed a modular architecture with automated pipelines.",
                "results": "Reduced onboarding time by 60% and improved data visibility.",
                "technologies": "Next.js, Django, PostgreSQL",
                "featured": True,
            },
            {
                "title": "Agency delivery automation",
                "slug": "agency-delivery-automation",
                "description": "Automated QA and deployment workflows for agencies.",
                "challenge": "Manual release steps created delays and regressions.",
                "solution": "Introduced automated checks and staged deployments.",
                "results": "Cut release time from days to hours.",
                "technologies": "GitHub Actions, Docker, Celery",
                "featured": True,
            },
        ]

        for item in portfolio_items:
            Portfolio.objects.get_or_create(slug=item["slug"], defaults=item)

        Testimonial.objects.get_or_create(
            client_name="Chris Walker",
            defaults={
                "quote": "ADB delivered exactly what we needed with clear communication.",
                "company": "Northside Studio",
                "job_title": "Founder",
                "rating": 5,
                "featured": True,
            },
        )

        blog_category, _ = BlogCategory.objects.get_or_create(
            slug="delivery",
            defaults={"name": "Delivery", "description": "Shipping and delivery insights"},
        )
        blog_tag, _ = BlogTag.objects.get_or_create(
            slug="automation", defaults={"name": "Automation"}
        )

        post, _ = BlogPost.objects.get_or_create(
            slug="shipping-without-agency-overhead",
            defaults={
                "title": "Shipping agency work without agency overhead",
                "excerpt": "How to keep delivery calm, accountable, and predictable while working lean.",
                "content": "## Delivery without overhead\n\nBuild clear milestones, keep scope tight, and communicate every decision.",
                "author": "ADB Software Solutions",
                "published": True,
                "featured": True,
                "meta_description": "Delivery insights for lean teams and agencies.",
                "meta_keywords": "delivery, agency, automation",
                "published_at": timezone.now(),
            },
        )
        post.categories.add(blog_category)
        post.tags.add(blog_tag)

        faq_category, _ = FAQCategory.objects.get_or_create(
            slug="engagement",
            defaults={"name": "Engagement", "description": "How we work", "order": 0},
        )

        FAQ.objects.get_or_create(
            question="Are you a full agency?",
            defaults={
                "answer": "No. ADB Software Solutions is a solo-led consultancy.",
                "category": faq_category,
                "order": 0,
            },
        )

        self.stdout.write(self.style.SUCCESS("Seeded marketing content."))

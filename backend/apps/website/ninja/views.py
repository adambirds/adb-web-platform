import logging

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router

from apps.core.models import Brand
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
from authentication.ninja.schemas import ProblemDetail, StatusResponse

from .schemas import (
    BlogCategoryOut,
    BlogPostOut,
    BlogTagOut,
    ContactRequest,
    FAQCategoryOut,
    FAQOut,
    PortfolioOut,
    TestimonialOut,
)

logger = logging.getLogger(__name__)

website_public_router = Router()
website_misc_router = Router()


def get_brand(slug: str) -> Brand:
    """Resolve an active brand slug or return a 404 response."""
    return get_object_or_404(Brand, slug=slug, is_active=True)


def build_image_url(request: HttpRequest, image_field) -> str | None:
    if not image_field:
        return None
    try:
        return request.build_absolute_uri(image_field.url)
    except Exception:
        return None


def parse_technologies(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@website_public_router.get("/portfolio", response=list[PortfolioOut])
def list_portfolio(request: HttpRequest, brand: str, featured: bool | None = None):
    selected_brand = get_brand(brand)
    qs = Portfolio.objects.filter(brands=selected_brand).distinct()
    if featured is not None:
        qs = qs.filter(featured=featured)

    return [
        PortfolioOut(
            id=item.id,
            title=item.title,
            slug=item.slug,
            description=item.description,
            challenge=item.challenge,
            solution=item.solution,
            results=item.results,
            technologies=parse_technologies(item.technologies),
            project_url=item.project_url,
            github_url=item.github_url,
            image_url=build_image_url(request, item.image),
            featured_image_url=build_image_url(request, item.featured_image),
            featured=item.featured,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in qs
    ]


@website_public_router.get("/portfolio/{slug}", response={200: PortfolioOut, 404: ProblemDetail})
def get_portfolio(request: HttpRequest, slug: str, brand: str):
    selected_brand = get_brand(brand)
    item = get_object_or_404(Portfolio.objects.filter(brands=selected_brand), slug=slug)
    return 200, PortfolioOut(
        id=item.id,
        title=item.title,
        slug=item.slug,
        description=item.description,
        challenge=item.challenge,
        solution=item.solution,
        results=item.results,
        technologies=parse_technologies(item.technologies),
        project_url=item.project_url,
        github_url=item.github_url,
        image_url=build_image_url(request, item.image),
        featured_image_url=build_image_url(request, item.featured_image),
        featured=item.featured,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@website_public_router.get("/testimonials", response=list[TestimonialOut])
def list_testimonials(request: HttpRequest, brand: str, featured: bool | None = None):
    selected_brand = get_brand(brand)
    qs = Testimonial.objects.filter(brands=selected_brand).distinct()
    if featured is not None:
        qs = qs.filter(featured=featured)

    return [
        TestimonialOut(
            id=item.id,
            quote=item.quote,
            client_name=item.client_name,
            company=item.company,
            job_title=item.job_title,
            rating=item.rating,
            image_url=build_image_url(request, item.image),
            featured=item.featured,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in qs
    ]


@website_public_router.get("/blog/categories", response=list[BlogCategoryOut])
def list_blog_categories(request: HttpRequest, brand: str):
    selected_brand = get_brand(brand)
    return [
        BlogCategoryOut(
            id=item.id,
            name=item.name,
            slug=item.slug,
            description=item.description,
        )
        for item in BlogCategory.objects.filter(brands=selected_brand).distinct()
    ]


@website_public_router.get("/blog/tags", response=list[BlogTagOut])
def list_blog_tags(request: HttpRequest, brand: str):
    selected_brand = get_brand(brand)
    return [
        BlogTagOut(
            id=item.id,
            name=item.name,
            slug=item.slug,
        )
        for item in BlogTag.objects.filter(brands=selected_brand).distinct()
    ]


def build_blog_post_response(request: HttpRequest, post: BlogPost) -> BlogPostOut:
    categories = [
        BlogCategoryOut(
            id=category.id,
            name=category.name,
            slug=category.slug,
            description=category.description,
        )
        for category in post.categories.all()
    ]
    tags = [
        BlogTagOut(
            id=tag.id,
            name=tag.name,
            slug=tag.slug,
        )
        for tag in post.tags.all()
    ]

    return BlogPostOut(
        id=post.id,
        title=post.title,
        slug=post.slug,
        excerpt=post.excerpt,
        content=post.content,
        featured_image_url=build_image_url(request, post.featured_image),
        author=post.author,
        published=post.published,
        featured=post.featured,
        categories=categories,
        tags=tags,
        meta_description=post.meta_description,
        meta_keywords=post.meta_keywords,
        created_at=post.created_at,
        published_at=post.published_at,
        updated_at=post.updated_at,
    )


@website_public_router.get("/blog/posts", response=list[BlogPostOut])
def list_blog_posts(request: HttpRequest, brand: str, featured: bool | None = None):
    selected_brand = get_brand(brand)
    qs = (
        BlogPost.objects.filter(published=True, brands=selected_brand)
        .prefetch_related("categories", "tags")
        .distinct()
    )
    if featured is not None:
        qs = qs.filter(featured=featured)

    return [build_blog_post_response(request, post) for post in qs]


@website_public_router.get("/blog/posts/{slug}", response={200: BlogPostOut, 404: ProblemDetail})
def get_blog_post(request: HttpRequest, slug: str, brand: str):
    selected_brand = get_brand(brand)
    post = get_object_or_404(
        BlogPost.objects.filter(brands=selected_brand).prefetch_related("categories", "tags"),
        slug=slug,
        published=True,
    )
    return 200, build_blog_post_response(request, post)


@website_public_router.get("/faqs/categories", response=list[FAQCategoryOut])
def list_faq_categories(request: HttpRequest, brand: str):
    selected_brand = get_brand(brand)
    return [
        FAQCategoryOut(
            id=item.id,
            name=item.name,
            slug=item.slug,
            description=item.description,
            order=item.order,
        )
        for item in FAQCategory.objects.filter(brands=selected_brand).distinct()
    ]


@website_public_router.get("/faqs", response=list[FAQOut])
def list_faqs(request: HttpRequest, brand: str, category: str | None = None):
    selected_brand = get_brand(brand)
    qs = FAQ.objects.select_related("category").filter(brands=selected_brand).distinct()
    if category:
        qs = qs.filter(category__slug=category, category__brands=selected_brand).distinct()

    return [
        FAQOut(
            id=item.id,
            question=item.question,
            answer=item.answer,
            category=FAQCategoryOut(
                id=item.category.id,
                name=item.category.name,
                slug=item.category.slug,
                description=item.category.description,
                order=item.category.order,
            ),
            order=item.order,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in qs
    ]


@website_misc_router.post(
    "/contact",
    response={200: StatusResponse, 400: ProblemDetail, 404: ProblemDetail, 500: ProblemDetail},
)
def submit_contact_form(request: HttpRequest, payload: ContactRequest, brand: str):
    try:
        selected_brand = get_brand(brand)
        status, _ = LeadStatus.objects.get_or_create(name="New", defaults={"order": 0})
        source, _ = LeadSource.objects.get_or_create(name="Contact Form")

        Lead.objects.create(
            brand=selected_brand,
            name=payload.name,
            email=payload.email,
            phone=payload.phone or "",
            company=payload.company or "",
            message=payload.message,
            status=status,
            source=source,
        )

        return 200, {"message": "Thanks! We'll be in touch shortly.", "success": True}

    except Exception as exc:
        logger.error("Contact form submission failed: %s", str(exc))
        return 500, {"message": "An error has occurred.", "success": False, "code": "server_error"}

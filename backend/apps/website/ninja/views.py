import logging
from typing import Any

from django.db.models import Q, QuerySet
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError

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
from authentication.ratelimit import rate_limit

from .schemas import (
    BlogCategoryOut,
    BlogPostOut,
    BlogTagOut,
    ContactRequest,
    FAQCategoryOut,
    FAQOut,
    PortfolioOut,
    PublicCollectionOut,
    TestimonialOut,
)

logger = logging.getLogger(__name__)

website_public_router = Router()
website_misc_router = Router()


def get_brand(slug: str) -> Brand:
    """Resolve an active brand slug or return a 404 response."""
    return get_object_or_404(Brand, slug=slug, is_active=True)


def get_brand_slugs(item: Any) -> list[str]:
    """Return stable Brand slugs assigned to a CMS object."""
    return list(item.brands.order_by("slug").values_list("slug", flat=True))


def build_image_url(request: HttpRequest, image_field: Any) -> str | None:
    if not image_field:
        return None
    try:
        return request.build_absolute_uri(image_field.url)
    except (AttributeError, ValueError):
        return None


def parse_technologies(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def build_portfolio_response(request: HttpRequest, item: Portfolio) -> PortfolioOut:
    return PortfolioOut(
        id=item.id,
        published=item.published,
        image_alt=item.image_alt,
        featured_image_alt=item.featured_image_alt,
        meta_description=item.meta_description,
        service_slugs=item.service_slugs,
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
        brand_slugs=get_brand_slugs(item),
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def build_testimonial_response(request: HttpRequest, item: Testimonial) -> TestimonialOut:
    return TestimonialOut(
        id=item.id,
        published=item.published,
        image_alt=item.image_alt,
        quote=item.quote,
        client_name=item.client_name,
        company=item.company,
        job_title=item.job_title,
        rating=item.rating,
        image_url=build_image_url(request, item.image),
        featured=item.featured,
        brand_slugs=get_brand_slugs(item),
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def build_blog_category_response(item: BlogCategory) -> BlogCategoryOut:
    return BlogCategoryOut(
        id=item.id,
        name=item.name,
        slug=item.slug,
        description=item.description,
        brand_slugs=get_brand_slugs(item),
    )


def build_blog_tag_response(item: BlogTag) -> BlogTagOut:
    return BlogTagOut(
        id=item.id,
        name=item.name,
        slug=item.slug,
        brand_slugs=get_brand_slugs(item),
    )


def build_faq_category_response(item: FAQCategory) -> FAQCategoryOut:
    return FAQCategoryOut(
        id=item.id,
        name=item.name,
        slug=item.slug,
        description=item.description,
        order=item.order,
        brand_slugs=get_brand_slugs(item),
    )


def build_blog_post_response(
    request: HttpRequest,
    post: BlogPost,
    brand: Brand | None = None,
) -> BlogPostOut:
    return BlogPostOut(
        id=post.id,
        featured_image_alt=post.featured_image_alt,
        title=post.title,
        slug=post.slug,
        excerpt=post.excerpt,
        content=post.content,
        featured_image_url=build_image_url(request, post.featured_image),
        author=post.author,
        published=post.published,
        featured=post.featured,
        categories=[
            build_blog_category_response(category)
            for category in post.categories.all()
            if brand is None or brand.slug in get_brand_slugs(category)
        ],
        tags=[
            build_blog_tag_response(tag)
            for tag in post.tags.all()
            if brand is None or brand.slug in get_brand_slugs(tag)
        ],
        brand_slugs=get_brand_slugs(post),
        meta_description=post.meta_description,
        meta_keywords=post.meta_keywords,
        created_at=post.created_at,
        published_at=post.published_at,
        updated_at=post.updated_at,
    )


@website_public_router.get("/portfolio", response=list[PortfolioOut])
def list_portfolio(
    request: HttpRequest,
    brand: str,
    featured: bool | None = None,
) -> list[PortfolioOut]:
    selected_brand = get_brand(brand)
    qs = (
        Portfolio.objects.filter(brands=selected_brand, published=True)
        .prefetch_related("brands")
        .distinct()
    )
    if featured is not None:
        qs = qs.filter(featured=featured)
    return [build_portfolio_response(request, item) for item in qs]


@website_public_router.get("/portfolio/{slug}", response={200: PortfolioOut, 404: ProblemDetail})
def get_portfolio(request: HttpRequest, slug: str, brand: str) -> tuple[int, PortfolioOut]:
    selected_brand = get_brand(brand)
    item = get_object_or_404(
        Portfolio.objects.filter(brands=selected_brand, published=True).prefetch_related("brands"),
        slug=slug,
    )
    return 200, build_portfolio_response(request, item)


@website_public_router.get("/testimonials", response=list[TestimonialOut])
def list_testimonials(
    request: HttpRequest,
    brand: str,
    featured: bool | None = None,
) -> list[TestimonialOut]:
    selected_brand = get_brand(brand)
    qs = (
        Testimonial.objects.filter(brands=selected_brand, published=True)
        .prefetch_related("brands")
        .distinct()
    )
    if featured is not None:
        qs = qs.filter(featured=featured)
    return [build_testimonial_response(request, item) for item in qs]


@website_public_router.get("/blog/categories", response=list[BlogCategoryOut])
def list_blog_categories(request: HttpRequest, brand: str) -> list[BlogCategoryOut]:
    selected_brand = get_brand(brand)
    qs = BlogCategory.objects.filter(brands=selected_brand).prefetch_related("brands").distinct()
    return [build_blog_category_response(item) for item in qs]


@website_public_router.get("/blog/tags", response=list[BlogTagOut])
def list_blog_tags(request: HttpRequest, brand: str) -> list[BlogTagOut]:
    selected_brand = get_brand(brand)
    qs = BlogTag.objects.filter(brands=selected_brand).prefetch_related("brands").distinct()
    return [build_blog_tag_response(item) for item in qs]


@website_public_router.get("/blog/posts", response=list[BlogPostOut])
def list_blog_posts(
    request: HttpRequest,
    brand: str,
    featured: bool | None = None,
) -> list[BlogPostOut]:
    selected_brand = get_brand(brand)
    qs = (
        BlogPost.objects.filter(published=True, brands=selected_brand)
        .filter(Q(published_at__isnull=True) | Q(published_at__lte=timezone.now()))
        .prefetch_related("brands", "categories__brands", "tags__brands")
        .distinct()
    )
    if featured is not None:
        qs = qs.filter(featured=featured)
    return [build_blog_post_response(request, post, selected_brand) for post in qs]


@website_public_router.get("/blog/posts/{slug}", response={200: BlogPostOut, 404: ProblemDetail})
def get_blog_post(request: HttpRequest, slug: str, brand: str) -> tuple[int, BlogPostOut]:
    selected_brand = get_brand(brand)
    post = get_object_or_404(
        BlogPost.objects.filter(brands=selected_brand)
        .filter(Q(published_at__isnull=True) | Q(published_at__lte=timezone.now()))
        .prefetch_related(
            "brands",
            "categories__brands",
            "tags__brands",
        ),
        slug=slug,
        published=True,
    )
    return 200, build_blog_post_response(request, post, selected_brand)


@website_public_router.get("/faqs/categories", response=list[FAQCategoryOut])
def list_faq_categories(request: HttpRequest, brand: str) -> list[FAQCategoryOut]:
    selected_brand = get_brand(brand)
    qs = FAQCategory.objects.filter(brands=selected_brand).prefetch_related("brands").distinct()
    return [build_faq_category_response(item) for item in qs]


@website_public_router.get("/faqs", response=list[FAQOut])
def list_faqs(
    request: HttpRequest,
    brand: str,
    category: str | None = None,
) -> list[FAQOut]:
    selected_brand = get_brand(brand)
    qs = (
        FAQ.objects.select_related("category")
        .filter(brands=selected_brand, published=True, category__brands=selected_brand)
        .prefetch_related("brands", "category__brands")
        .distinct()
    )
    if category:
        qs = qs.filter(category__slug=category, category__brands=selected_brand).distinct()

    return [
        FAQOut(
            id=item.id,
            published=item.published,
            service_slugs=item.service_slugs,
            question=item.question,
            answer=item.answer,
            category=build_faq_category_response(item.category),
            order=item.order,
            brand_slugs=get_brand_slugs(item),
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in qs
    ]


@website_misc_router.post(
    "/contact",
    response={200: StatusResponse, 400: ProblemDetail, 404: ProblemDetail, 500: ProblemDetail},
)
@rate_limit("website_contact")
def submit_contact_form(
    request: HttpRequest,
    payload: ContactRequest,
    brand: str,
) -> tuple[int, dict[str, Any]]:
    selected_brand = get_brand(brand)
    if payload.website:
        return 200, {"message": "Your enquiry has been received.", "success": True}

    try:
        status, _ = LeadStatus.objects.get_or_create(name="New", defaults={"order": 0})
        source, _ = LeadSource.objects.get_or_create(name="Contact Form")

        Lead.objects.create(
            brand=selected_brand,
            name=payload.name,
            email=payload.email,
            phone=payload.phone or "",
            company=payload.company or "",
            message=f"Website enquiry from {payload.source_path}\n\n{payload.message}",
            status=status,
            source=source,
        )

        return 200, {"message": "Your enquiry has been received.", "success": True}
    except Exception:
        logger.exception("Contact form submission failed for brand %s", selected_brand.slug)
        return 500, {
            "message": "An error has occurred.",
            "success": False,
            "code": "server_error",
        }


@website_public_router.get("/collections/{resource}", response=PublicCollectionOut)
def public_collection(
    request: HttpRequest,
    resource: str,
    brand: str,
    page: int = 1,
    page_size: int = 9,
    category: str | None = None,
    q: str = "",
    service: str | None = None,
    featured: bool | None = None,
) -> PublicCollectionOut:
    """Paginate at the database boundary; keep established list API contracts."""
    selected_brand = get_brand(brand)
    if not 1 <= page_size <= 50 or page < 1 or len(q) > 200:
        raise HttpError(400, "Invalid pagination or search parameters.")
    queryset: QuerySet[Portfolio] | QuerySet[BlogPost] | QuerySet[Testimonial] | QuerySet[FAQ]
    if resource == "portfolio":
        queryset = Portfolio.objects.filter(brands=selected_brand, published=True).prefetch_related(
            "brands"
        )
        if service:
            queryset = queryset.filter(service_slugs__contains=[service])
        if q:
            queryset = queryset.filter(Q(title__icontains=q) | Q(description__icontains=q))
    elif resource == "blog":
        queryset = (
            BlogPost.objects.filter(published=True, brands=selected_brand)
            .filter(Q(published_at__isnull=True) | Q(published_at__lte=timezone.now()))
            .prefetch_related("brands", "categories__brands", "tags__brands")
        )
        if category:
            queryset = queryset.filter(categories__slug=category, categories__brands=selected_brand)
        if q:
            queryset = queryset.filter(Q(title__icontains=q) | Q(excerpt__icontains=q))
    elif resource == "testimonials":
        queryset = Testimonial.objects.filter(
            brands=selected_brand, published=True
        ).prefetch_related("brands")
        if q:
            queryset = queryset.filter(Q(quote__icontains=q) | Q(company__icontains=q))
    elif resource == "faqs":
        queryset = (
            FAQ.objects.filter(
                brands=selected_brand, published=True, category__brands=selected_brand
            )
            .select_related("category")
            .prefetch_related("brands", "category__brands")
            .order_by("order", "id")
        )
        if category:
            queryset = queryset.filter(category__slug=category)
        if service:
            queryset = queryset.filter(service_slugs__contains=[service])
        if q:
            queryset = queryset.filter(Q(question__icontains=q) | Q(answer__icontains=q))
    else:
        raise HttpError(404, "Unknown content collection.")
    if featured is not None and resource != "faqs":
        queryset = queryset.filter(Q(featured=featured))
    queryset = queryset.distinct()
    if resource != "faqs":
        queryset = queryset.order_by("-created_at", "-id")
    total = queryset.count()
    start = (page - 1) * page_size
    items: list[PortfolioOut | BlogPostOut | TestimonialOut | FAQOut] = []
    for item in queryset[start : start + page_size]:
        if isinstance(item, Portfolio):
            items.append(build_portfolio_response(request, item))
        elif isinstance(item, BlogPost):
            items.append(build_blog_post_response(request, item, selected_brand))
        elif isinstance(item, Testimonial):
            items.append(build_testimonial_response(request, item))
        else:
            items.append(
                FAQOut(
                    id=item.id,
                    question=item.question,
                    answer=item.answer,
                    published=item.published,
                    service_slugs=item.service_slugs,
                    category=build_faq_category_response(item.category),
                    order=item.order,
                    brand_slugs=get_brand_slugs(item),
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
            )
    return PublicCollectionOut(items=items, total=total, page=page, page_size=page_size)

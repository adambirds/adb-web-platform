from __future__ import annotations

from typing import Any

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError

from apps.core.models import Brand
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
    BlogCategoryIn,
    BlogCategoryOut,
    BlogPostIn,
    BlogPostOut,
    BlogTagIn,
    BlogTagOut,
    FAQCategoryIn,
    FAQCategoryOut,
    FAQIn,
    FAQOut,
    PortfolioIn,
    PortfolioOut,
    TestimonialIn,
    TestimonialOut,
)
from .views import (
    build_blog_category_response,
    build_blog_post_response,
    build_blog_tag_response,
    build_faq_category_response,
    build_image_url,
    build_portfolio_response,
    build_testimonial_response,
    get_brand_slugs,
)

website_admin_router = Router()


def require_permission(request: HttpRequest, permission: str):
    """Require an authenticated staff user with a specific Django capability."""
    if not request.user.is_authenticated:
        return 401, {
            "message": "User not authenticated",
            "success": False,
            "code": "unauthenticated",
        }
    if not (request.user.is_staff or request.user.is_superuser):
        return 403, {
            "message": "You do not have permission to access this resource.",
            "success": False,
            "code": "forbidden",
        }
    if not request.user.has_perm(permission):
        return 403, {
            "message": "You do not have permission to perform this action.",
            "success": False,
            "code": "forbidden",
        }
    return None


def set_brands(item: Any, brand_ids: list[int]) -> None:
    """Replace an item's Brand assignments after validating every supplied ID."""
    brands = list(Brand.objects.filter(id__in=brand_ids))
    if len(brands) != len(set(brand_ids)):
        raise HttpError(400, "One or more selected brands do not exist.")
    item.brands.set(brands)


def build_faq_response(item: FAQ) -> FAQOut:
    return FAQOut(
        id=item.id,
        question=item.question,
        answer=item.answer,
        category=build_faq_category_response(item.category),
        order=item.order,
        brand_slugs=get_brand_slugs(item),
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


# Portfolio / public case studies


@website_admin_router.get(
    "/website/portfolio",
    response={200: list[PortfolioOut], 401: ProblemDetail, 403: ProblemDetail},
)
def admin_list_portfolio(request: HttpRequest):
    auth_error = require_permission(request, "website.view_portfolio")
    if auth_error:
        return auth_error
    qs = Portfolio.objects.prefetch_related("brands").all()
    return [build_portfolio_response(request, item) for item in qs]


@website_admin_router.post(
    "/website/portfolio",
    response={200: PortfolioOut, 400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail},
)
def admin_create_portfolio(request: HttpRequest, payload: PortfolioIn):
    auth_error = require_permission(request, "website.add_portfolio")
    if auth_error:
        return auth_error

    item = Portfolio.objects.create(
        title=payload.title,
        slug=payload.slug,
        description=payload.description,
        challenge=payload.challenge,
        solution=payload.solution,
        results=payload.results,
        technologies=", ".join(payload.technologies),
        project_url=payload.project_url,
        github_url=payload.github_url,
        featured=payload.featured,
    )
    set_brands(item, payload.brand_ids)
    return build_portfolio_response(request, item)


@website_admin_router.get(
    "/website/portfolio/{portfolio_id}",
    response={200: PortfolioOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_get_portfolio(request: HttpRequest, portfolio_id: int):
    auth_error = require_permission(request, "website.view_portfolio")
    if auth_error:
        return auth_error
    item = get_object_or_404(Portfolio.objects.prefetch_related("brands"), id=portfolio_id)
    return build_portfolio_response(request, item)


@website_admin_router.put(
    "/website/portfolio/{portfolio_id}",
    response={200: PortfolioOut, 400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_update_portfolio(request: HttpRequest, portfolio_id: int, payload: PortfolioIn):
    auth_error = require_permission(request, "website.change_portfolio")
    if auth_error:
        return auth_error

    item = get_object_or_404(Portfolio, id=portfolio_id)
    item.title = payload.title
    item.slug = payload.slug
    item.description = payload.description
    item.challenge = payload.challenge
    item.solution = payload.solution
    item.results = payload.results
    item.technologies = ", ".join(payload.technologies)
    item.project_url = payload.project_url
    item.github_url = payload.github_url
    item.featured = payload.featured
    item.save()
    set_brands(item, payload.brand_ids)
    return build_portfolio_response(request, item)


@website_admin_router.delete(
    "/website/portfolio/{portfolio_id}",
    response={200: StatusResponse, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_delete_portfolio(request: HttpRequest, portfolio_id: int):
    auth_error = require_permission(request, "website.delete_portfolio")
    if auth_error:
        return auth_error
    get_object_or_404(Portfolio, id=portfolio_id).delete()
    return 200, {"message": "Portfolio deleted", "success": True}


# Testimonials


@website_admin_router.get(
    "/website/testimonials",
    response={200: list[TestimonialOut], 401: ProblemDetail, 403: ProblemDetail},
)
def admin_list_testimonials(request: HttpRequest):
    auth_error = require_permission(request, "website.view_testimonial")
    if auth_error:
        return auth_error
    qs = Testimonial.objects.prefetch_related("brands").all()
    return [build_testimonial_response(request, item) for item in qs]


@website_admin_router.post(
    "/website/testimonials",
    response={200: TestimonialOut, 400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail},
)
def admin_create_testimonial(request: HttpRequest, payload: TestimonialIn):
    auth_error = require_permission(request, "website.add_testimonial")
    if auth_error:
        return auth_error

    item = Testimonial.objects.create(
        quote=payload.quote,
        client_name=payload.client_name,
        company=payload.company or "",
        job_title=payload.job_title or "",
        rating=payload.rating,
        featured=payload.featured,
    )
    set_brands(item, payload.brand_ids)
    return build_testimonial_response(request, item)


@website_admin_router.get(
    "/website/testimonials/{testimonial_id}",
    response={200: TestimonialOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_get_testimonial(request: HttpRequest, testimonial_id: int):
    auth_error = require_permission(request, "website.view_testimonial")
    if auth_error:
        return auth_error
    item = get_object_or_404(
        Testimonial.objects.prefetch_related("brands"),
        id=testimonial_id,
    )
    return build_testimonial_response(request, item)


@website_admin_router.put(
    "/website/testimonials/{testimonial_id}",
    response={200: TestimonialOut, 400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_update_testimonial(request: HttpRequest, testimonial_id: int, payload: TestimonialIn):
    auth_error = require_permission(request, "website.change_testimonial")
    if auth_error:
        return auth_error

    item = get_object_or_404(Testimonial, id=testimonial_id)
    item.quote = payload.quote
    item.client_name = payload.client_name
    item.company = payload.company or ""
    item.job_title = payload.job_title or ""
    item.rating = payload.rating
    item.featured = payload.featured
    item.save()
    set_brands(item, payload.brand_ids)
    return build_testimonial_response(request, item)


@website_admin_router.delete(
    "/website/testimonials/{testimonial_id}",
    response={200: StatusResponse, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_delete_testimonial(request: HttpRequest, testimonial_id: int):
    auth_error = require_permission(request, "website.delete_testimonial")
    if auth_error:
        return auth_error
    get_object_or_404(Testimonial, id=testimonial_id).delete()
    return 200, {"message": "Testimonial deleted", "success": True}


# Blog categories


@website_admin_router.get(
    "/website/blog/categories",
    response={200: list[BlogCategoryOut], 401: ProblemDetail, 403: ProblemDetail},
)
def admin_list_blog_categories(request: HttpRequest):
    auth_error = require_permission(request, "website.view_blogcategory")
    if auth_error:
        return auth_error
    return [
        build_blog_category_response(item)
        for item in BlogCategory.objects.prefetch_related("brands").all()
    ]


@website_admin_router.post(
    "/website/blog/categories",
    response={200: BlogCategoryOut, 400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail},
)
def admin_create_blog_category(request: HttpRequest, payload: BlogCategoryIn):
    auth_error = require_permission(request, "website.add_blogcategory")
    if auth_error:
        return auth_error

    item = BlogCategory.objects.create(
        name=payload.name,
        slug=payload.slug,
        description=payload.description or "",
    )
    set_brands(item, payload.brand_ids)
    return build_blog_category_response(item)


@website_admin_router.put(
    "/website/blog/categories/{category_id}",
    response={200: BlogCategoryOut, 400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_update_blog_category(request: HttpRequest, category_id: int, payload: BlogCategoryIn):
    auth_error = require_permission(request, "website.change_blogcategory")
    if auth_error:
        return auth_error

    item = get_object_or_404(BlogCategory, id=category_id)
    item.name = payload.name
    item.slug = payload.slug
    item.description = payload.description or ""
    item.save()
    set_brands(item, payload.brand_ids)
    return build_blog_category_response(item)


@website_admin_router.delete(
    "/website/blog/categories/{category_id}",
    response={200: StatusResponse, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_delete_blog_category(request: HttpRequest, category_id: int):
    auth_error = require_permission(request, "website.delete_blogcategory")
    if auth_error:
        return auth_error
    get_object_or_404(BlogCategory, id=category_id).delete()
    return 200, {"message": "Blog category deleted", "success": True}


# Blog tags


@website_admin_router.get(
    "/website/blog/tags",
    response={200: list[BlogTagOut], 401: ProblemDetail, 403: ProblemDetail},
)
def admin_list_blog_tags(request: HttpRequest):
    auth_error = require_permission(request, "website.view_blogtag")
    if auth_error:
        return auth_error
    return [build_blog_tag_response(item) for item in BlogTag.objects.prefetch_related("brands").all()]


@website_admin_router.post(
    "/website/blog/tags",
    response={200: BlogTagOut, 400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail},
)
def admin_create_blog_tag(request: HttpRequest, payload: BlogTagIn):
    auth_error = require_permission(request, "website.add_blogtag")
    if auth_error:
        return auth_error

    item = BlogTag.objects.create(name=payload.name, slug=payload.slug)
    set_brands(item, payload.brand_ids)
    return build_blog_tag_response(item)


@website_admin_router.put(
    "/website/blog/tags/{tag_id}",
    response={200: BlogTagOut, 400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_update_blog_tag(request: HttpRequest, tag_id: int, payload: BlogTagIn):
    auth_error = require_permission(request, "website.change_blogtag")
    if auth_error:
        return auth_error

    item = get_object_or_404(BlogTag, id=tag_id)
    item.name = payload.name
    item.slug = payload.slug
    item.save()
    set_brands(item, payload.brand_ids)
    return build_blog_tag_response(item)


@website_admin_router.delete(
    "/website/blog/tags/{tag_id}",
    response={200: StatusResponse, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_delete_blog_tag(request: HttpRequest, tag_id: int):
    auth_error = require_permission(request, "website.delete_blogtag")
    if auth_error:
        return auth_error
    get_object_or_404(BlogTag, id=tag_id).delete()
    return 200, {"message": "Blog tag deleted", "success": True}


# Blog posts


@website_admin_router.get(
    "/website/blog/posts",
    response={200: list[BlogPostOut], 401: ProblemDetail, 403: ProblemDetail},
)
def admin_list_blog_posts(request: HttpRequest):
    auth_error = require_permission(request, "website.view_blogpost")
    if auth_error:
        return auth_error
    qs = BlogPost.objects.prefetch_related("brands", "categories__brands", "tags__brands")
    return [build_blog_post_response(request, post) for post in qs]


@website_admin_router.post(
    "/website/blog/posts",
    response={200: BlogPostOut, 400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail},
)
def admin_create_blog_post(request: HttpRequest, payload: BlogPostIn):
    auth_error = require_permission(request, "website.add_blogpost")
    if auth_error:
        return auth_error

    post = BlogPost.objects.create(
        title=payload.title,
        slug=payload.slug,
        excerpt=payload.excerpt,
        content=payload.content,
        author=payload.author or "ADB Software Solutions",
        published=payload.published,
        featured=payload.featured,
        meta_description=payload.meta_description or "",
        meta_keywords=payload.meta_keywords or "",
        published_at=payload.published_at or (timezone.now() if payload.published else None),
    )
    set_brands(post, payload.brand_ids)
    post.categories.set(BlogCategory.objects.filter(id__in=payload.category_ids))
    post.tags.set(BlogTag.objects.filter(id__in=payload.tag_ids))
    return build_blog_post_response(request, post)


@website_admin_router.get(
    "/website/blog/posts/{post_id}",
    response={200: BlogPostOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_get_blog_post(request: HttpRequest, post_id: int):
    auth_error = require_permission(request, "website.view_blogpost")
    if auth_error:
        return auth_error
    post = get_object_or_404(
        BlogPost.objects.prefetch_related("brands", "categories__brands", "tags__brands"),
        id=post_id,
    )
    return build_blog_post_response(request, post)


@website_admin_router.put(
    "/website/blog/posts/{post_id}",
    response={200: BlogPostOut, 400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_update_blog_post(request: HttpRequest, post_id: int, payload: BlogPostIn):
    auth_error = require_permission(request, "website.change_blogpost")
    if auth_error:
        return auth_error

    post = get_object_or_404(BlogPost, id=post_id)
    post.title = payload.title
    post.slug = payload.slug
    post.excerpt = payload.excerpt
    post.content = payload.content
    post.author = payload.author or post.author
    post.published = payload.published
    post.featured = payload.featured
    post.meta_description = payload.meta_description or ""
    post.meta_keywords = payload.meta_keywords or ""
    post.published_at = payload.published_at
    if post.published and post.published_at is None:
        post.published_at = timezone.now()
    post.save()
    set_brands(post, payload.brand_ids)
    post.categories.set(BlogCategory.objects.filter(id__in=payload.category_ids))
    post.tags.set(BlogTag.objects.filter(id__in=payload.tag_ids))
    return build_blog_post_response(request, post)


@website_admin_router.delete(
    "/website/blog/posts/{post_id}",
    response={200: StatusResponse, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_delete_blog_post(request: HttpRequest, post_id: int):
    auth_error = require_permission(request, "website.delete_blogpost")
    if auth_error:
        return auth_error
    get_object_or_404(BlogPost, id=post_id).delete()
    return 200, {"message": "Blog post deleted", "success": True}


# FAQ categories


@website_admin_router.get(
    "/website/faqs/categories",
    response={200: list[FAQCategoryOut], 401: ProblemDetail, 403: ProblemDetail},
)
def admin_list_faq_categories(request: HttpRequest):
    auth_error = require_permission(request, "website.view_faqcategory")
    if auth_error:
        return auth_error
    return [
        build_faq_category_response(item)
        for item in FAQCategory.objects.prefetch_related("brands").all()
    ]


@website_admin_router.post(
    "/website/faqs/categories",
    response={200: FAQCategoryOut, 400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail},
)
def admin_create_faq_category(request: HttpRequest, payload: FAQCategoryIn):
    auth_error = require_permission(request, "website.add_faqcategory")
    if auth_error:
        return auth_error

    item = FAQCategory.objects.create(
        name=payload.name,
        slug=payload.slug,
        description=payload.description or "",
        order=payload.order,
    )
    set_brands(item, payload.brand_ids)
    return build_faq_category_response(item)


@website_admin_router.put(
    "/website/faqs/categories/{category_id}",
    response={200: FAQCategoryOut, 400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_update_faq_category(request: HttpRequest, category_id: int, payload: FAQCategoryIn):
    auth_error = require_permission(request, "website.change_faqcategory")
    if auth_error:
        return auth_error

    item = get_object_or_404(FAQCategory, id=category_id)
    item.name = payload.name
    item.slug = payload.slug
    item.description = payload.description or ""
    item.order = payload.order
    item.save()
    set_brands(item, payload.brand_ids)
    return build_faq_category_response(item)


@website_admin_router.delete(
    "/website/faqs/categories/{category_id}",
    response={200: StatusResponse, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_delete_faq_category(request: HttpRequest, category_id: int):
    auth_error = require_permission(request, "website.delete_faqcategory")
    if auth_error:
        return auth_error
    get_object_or_404(FAQCategory, id=category_id).delete()
    return 200, {"message": "FAQ category deleted", "success": True}


# FAQs


@website_admin_router.get(
    "/website/faqs",
    response={200: list[FAQOut], 401: ProblemDetail, 403: ProblemDetail},
)
def admin_list_faqs(request: HttpRequest):
    auth_error = require_permission(request, "website.view_faq")
    if auth_error:
        return auth_error
    qs = FAQ.objects.select_related("category").prefetch_related("brands", "category__brands")
    return [build_faq_response(item) for item in qs]


@website_admin_router.post(
    "/website/faqs",
    response={200: FAQOut, 400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail},
)
def admin_create_faq(request: HttpRequest, payload: FAQIn):
    auth_error = require_permission(request, "website.add_faq")
    if auth_error:
        return auth_error

    category = get_object_or_404(FAQCategory, id=payload.category_id)
    item = FAQ.objects.create(
        question=payload.question,
        answer=payload.answer,
        category=category,
        order=payload.order,
    )
    set_brands(item, payload.brand_ids)
    return build_faq_response(item)


@website_admin_router.put(
    "/website/faqs/{faq_id}",
    response={200: FAQOut, 400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_update_faq(request: HttpRequest, faq_id: int, payload: FAQIn):
    auth_error = require_permission(request, "website.change_faq")
    if auth_error:
        return auth_error

    item = get_object_or_404(FAQ, id=faq_id)
    item.question = payload.question
    item.answer = payload.answer
    item.category = get_object_or_404(FAQCategory, id=payload.category_id)
    item.order = payload.order
    item.save()
    set_brands(item, payload.brand_ids)
    return build_faq_response(item)


@website_admin_router.delete(
    "/website/faqs/{faq_id}",
    response={200: StatusResponse, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_delete_faq(request: HttpRequest, faq_id: int):
    auth_error = require_permission(request, "website.delete_faq")
    if auth_error:
        return auth_error
    get_object_or_404(FAQ, id=faq_id).delete()
    return 200, {"message": "FAQ deleted", "success": True}

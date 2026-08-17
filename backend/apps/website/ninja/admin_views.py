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


@website_admin_router.get(
    "/portfolio",
    response={200: list[PortfolioOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_portfolio(request: HttpRequest):
    permission_error = require_permission(request, "website.view_portfolio")
    if permission_error:
        return permission_error

    return [build_portfolio_response(request, item) for item in Portfolio.objects.all()]


@website_admin_router.get(
    "/portfolio/{portfolio_id}",
    response={200: PortfolioOut, 401: ProblemDetail, 403: ProblemDetail},
)
def get_portfolio(request: HttpRequest, portfolio_id: int):
    permission_error = require_permission(request, "website.view_portfolio")
    if permission_error:
        return permission_error

    item = get_object_or_404(Portfolio, id=portfolio_id)
    return build_portfolio_response(request, item)


@website_admin_router.post(
    "/portfolio",
    response={200: PortfolioOut, 401: ProblemDetail, 403: ProblemDetail},
)
def create_portfolio(request: HttpRequest, payload: PortfolioIn):
    permission_error = require_permission(request, "website.add_portfolio")
    if permission_error:
        return permission_error

    item = Portfolio.objects.create(
        title=payload.title,
        description=payload.description,
        url=payload.url,
        project_type=payload.project_type,
        technologies=payload.technologies,
        featured=payload.featured,
    )
    set_brands(item, payload.brand_ids)
    return build_portfolio_response(request, item)


@website_admin_router.put(
    "/portfolio/{portfolio_id}",
    response={200: PortfolioOut, 401: ProblemDetail, 403: ProblemDetail},
)
def update_portfolio(request: HttpRequest, portfolio_id: int, payload: PortfolioIn):
    permission_error = require_permission(request, "website.change_portfolio")
    if permission_error:
        return permission_error

    item = get_object_or_404(Portfolio, id=portfolio_id)
    item.title = payload.title
    item.description = payload.description
    item.url = payload.url
    item.project_type = payload.project_type
    item.technologies = payload.technologies
    item.featured = payload.featured
    item.save()
    set_brands(item, payload.brand_ids)
    return build_portfolio_response(request, item)


@website_admin_router.delete(
    "/portfolio/{portfolio_id}",
    response={200: StatusResponse, 401: ProblemDetail, 403: ProblemDetail},
)
def delete_portfolio(request: HttpRequest, portfolio_id: int):
    permission_error = require_permission(request, "website.delete_portfolio")
    if permission_error:
        return permission_error

    item = get_object_or_404(Portfolio, id=portfolio_id)
    item.delete()
    return {"success": True, "message": "Portfolio item deleted."}


@website_admin_router.get(
    "/testimonials",
    response={200: list[TestimonialOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_testimonials(request: HttpRequest):
    permission_error = require_permission(request, "website.view_testimonial")
    if permission_error:
        return permission_error

    return [build_testimonial_response(request, item) for item in Testimonial.objects.all()]


@website_admin_router.get(
    "/testimonials/{testimonial_id}",
    response={200: TestimonialOut, 401: ProblemDetail, 403: ProblemDetail},
)
def get_testimonial(request: HttpRequest, testimonial_id: int):
    permission_error = require_permission(request, "website.view_testimonial")
    if permission_error:
        return permission_error

    item = get_object_or_404(Testimonial, id=testimonial_id)
    return build_testimonial_response(request, item)


@website_admin_router.post(
    "/testimonials",
    response={200: TestimonialOut, 401: ProblemDetail, 403: ProblemDetail},
)
def create_testimonial(request: HttpRequest, payload: TestimonialIn):
    permission_error = require_permission(request, "website.add_testimonial")
    if permission_error:
        return permission_error

    item = Testimonial.objects.create(
        quote=payload.quote,
        client_name=payload.client_name,
        company=payload.company,
        rating=payload.rating,
        featured=payload.featured,
    )
    set_brands(item, payload.brand_ids)
    return build_testimonial_response(request, item)


@website_admin_router.put(
    "/testimonials/{testimonial_id}",
    response={200: TestimonialOut, 401: ProblemDetail, 403: ProblemDetail},
)
def update_testimonial(request: HttpRequest, testimonial_id: int, payload: TestimonialIn):
    permission_error = require_permission(request, "website.change_testimonial")
    if permission_error:
        return permission_error

    item = get_object_or_404(Testimonial, id=testimonial_id)
    item.quote = payload.quote
    item.client_name = payload.client_name
    item.company = payload.company
    item.rating = payload.rating
    item.featured = payload.featured
    item.save()
    set_brands(item, payload.brand_ids)
    return build_testimonial_response(request, item)


@website_admin_router.delete(
    "/testimonials/{testimonial_id}",
    response={200: StatusResponse, 401: ProblemDetail, 403: ProblemDetail},
)
def delete_testimonial(request: HttpRequest, testimonial_id: int):
    permission_error = require_permission(request, "website.delete_testimonial")
    if permission_error:
        return permission_error

    item = get_object_or_404(Testimonial, id=testimonial_id)
    item.delete()
    return {"success": True, "message": "Testimonial deleted."}


@website_admin_router.get(
    "/blog/posts",
    response={200: list[BlogPostOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_blog_posts(request: HttpRequest):
    permission_error = require_permission(request, "website.view_blogpost")
    if permission_error:
        return permission_error

    return [build_blog_post_response(request, item) for item in BlogPost.objects.all()]


@website_admin_router.get(
    "/blog/posts/{post_id}",
    response={200: BlogPostOut, 401: ProblemDetail, 403: ProblemDetail},
)
def get_blog_post(request: HttpRequest, post_id: int):
    permission_error = require_permission(request, "website.view_blogpost")
    if permission_error:
        return permission_error

    item = get_object_or_404(BlogPost, id=post_id)
    return build_blog_post_response(request, item)


@website_admin_router.post(
    "/blog/posts",
    response={200: BlogPostOut, 401: ProblemDetail, 403: ProblemDetail},
)
def create_blog_post(request: HttpRequest, payload: BlogPostIn):
    permission_error = require_permission(request, "website.add_blogpost")
    if permission_error:
        return permission_error

    item = BlogPost.objects.create(
        title=payload.title,
        slug=payload.slug,
        excerpt=payload.excerpt,
        content=payload.content,
        category_id=payload.category_id,
        featured=payload.featured,
        published=payload.published,
        published_at=timezone.now() if payload.published else None,
    )
    item.tags.set(payload.tag_ids)
    set_brands(item, payload.brand_ids)
    return build_blog_post_response(request, item)


@website_admin_router.put(
    "/blog/posts/{post_id}",
    response={200: BlogPostOut, 401: ProblemDetail, 403: ProblemDetail},
)
def update_blog_post(request: HttpRequest, post_id: int, payload: BlogPostIn):
    permission_error = require_permission(request, "website.change_blogpost")
    if permission_error:
        return permission_error

    item = get_object_or_404(BlogPost, id=post_id)
    item.title = payload.title
    item.slug = payload.slug
    item.excerpt = payload.excerpt
    item.content = payload.content
    item.category_id = payload.category_id
    item.featured = payload.featured
    if payload.published and not item.published:
        item.published_at = timezone.now()
    if not payload.published:
        item.published_at = None
    item.published = payload.published
    item.save()
    item.tags.set(payload.tag_ids)
    set_brands(item, payload.brand_ids)
    return build_blog_post_response(request, item)


@website_admin_router.delete(
    "/blog/posts/{post_id}",
    response={200: StatusResponse, 401: ProblemDetail, 403: ProblemDetail},
)
def delete_blog_post(request: HttpRequest, post_id: int):
    permission_error = require_permission(request, "website.delete_blogpost")
    if permission_error:
        return permission_error

    item = get_object_or_404(BlogPost, id=post_id)
    item.delete()
    return {"success": True, "message": "Blog post deleted."}


@website_admin_router.get(
    "/blog/categories",
    response={200: list[BlogCategoryOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_blog_categories(request: HttpRequest):
    permission_error = require_permission(request, "website.view_blogcategory")
    if permission_error:
        return permission_error
    return [build_blog_category_response(item) for item in BlogCategory.objects.all()]


@website_admin_router.post(
    "/blog/categories",
    response={200: BlogCategoryOut, 401: ProblemDetail, 403: ProblemDetail},
)
def create_blog_category(request: HttpRequest, payload: BlogCategoryIn):
    permission_error = require_permission(request, "website.add_blogcategory")
    if permission_error:
        return permission_error
    item = BlogCategory.objects.create(name=payload.name, slug=payload.slug)
    set_brands(item, payload.brand_ids)
    return build_blog_category_response(item)


@website_admin_router.put(
    "/blog/categories/{category_id}",
    response={200: BlogCategoryOut, 401: ProblemDetail, 403: ProblemDetail},
)
def update_blog_category(request: HttpRequest, category_id: int, payload: BlogCategoryIn):
    permission_error = require_permission(request, "website.change_blogcategory")
    if permission_error:
        return permission_error
    item = get_object_or_404(BlogCategory, id=category_id)
    item.name = payload.name
    item.slug = payload.slug
    item.save()
    set_brands(item, payload.brand_ids)
    return build_blog_category_response(item)


@website_admin_router.delete(
    "/blog/categories/{category_id}",
    response={200: StatusResponse, 401: ProblemDetail, 403: ProblemDetail},
)
def delete_blog_category(request: HttpRequest, category_id: int):
    permission_error = require_permission(request, "website.delete_blogcategory")
    if permission_error:
        return permission_error
    item = get_object_or_404(BlogCategory, id=category_id)
    item.delete()
    return {"success": True, "message": "Blog category deleted."}


@website_admin_router.get(
    "/blog/tags",
    response={200: list[BlogTagOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_blog_tags(request: HttpRequest):
    permission_error = require_permission(request, "website.view_blogtag")
    if permission_error:
        return permission_error
    return [build_blog_tag_response(item) for item in BlogTag.objects.all()]


@website_admin_router.post(
    "/blog/tags",
    response={200: BlogTagOut, 401: ProblemDetail, 403: ProblemDetail},
)
def create_blog_tag(request: HttpRequest, payload: BlogTagIn):
    permission_error = require_permission(request, "website.add_blogtag")
    if permission_error:
        return permission_error
    item = BlogTag.objects.create(name=payload.name, slug=payload.slug)
    set_brands(item, payload.brand_ids)
    return build_blog_tag_response(item)


@website_admin_router.put(
    "/blog/tags/{tag_id}",
    response={200: BlogTagOut, 401: ProblemDetail, 403: ProblemDetail},
)
def update_blog_tag(request: HttpRequest, tag_id: int, payload: BlogTagIn):
    permission_error = require_permission(request, "website.change_blogtag")
    if permission_error:
        return permission_error
    item = get_object_or_404(BlogTag, id=tag_id)
    item.name = payload.name
    item.slug = payload.slug
    item.save()
    set_brands(item, payload.brand_ids)
    return build_blog_tag_response(item)


@website_admin_router.delete(
    "/blog/tags/{tag_id}",
    response={200: StatusResponse, 401: ProblemDetail, 403: ProblemDetail},
)
def delete_blog_tag(request: HttpRequest, tag_id: int):
    permission_error = require_permission(request, "website.delete_blogtag")
    if permission_error:
        return permission_error
    item = get_object_or_404(BlogTag, id=tag_id)
    item.delete()
    return {"success": True, "message": "Blog tag deleted."}


@website_admin_router.get(
    "/faqs",
    response={200: list[FAQOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_faqs(request: HttpRequest):
    permission_error = require_permission(request, "website.view_faq")
    if permission_error:
        return permission_error
    return [
        FAQOut(
            id=item.id,
            question=item.question,
            answer=item.answer,
            category_id=item.category_id,
            order=item.order,
            brand_slugs=get_brand_slugs(item),
        )
        for item in FAQ.objects.all()
    ]


@website_admin_router.post(
    "/faqs",
    response={200: FAQOut, 401: ProblemDetail, 403: ProblemDetail},
)
def create_faq(request: HttpRequest, payload: FAQIn):
    permission_error = require_permission(request, "website.add_faq")
    if permission_error:
        return permission_error
    item = FAQ.objects.create(
        question=payload.question,
        answer=payload.answer,
        category_id=payload.category_id,
        order=payload.order,
    )
    set_brands(item, payload.brand_ids)
    return FAQOut(
        id=item.id,
        question=item.question,
        answer=item.answer,
        category_id=item.category_id,
        order=item.order,
        brand_slugs=get_brand_slugs(item),
    )


@website_admin_router.put(
    "/faqs/{faq_id}",
    response={200: FAQOut, 401: ProblemDetail, 403: ProblemDetail},
)
def update_faq(request: HttpRequest, faq_id: int, payload: FAQIn):
    permission_error = require_permission(request, "website.change_faq")
    if permission_error:
        return permission_error
    item = get_object_or_404(FAQ, id=faq_id)
    item.question = payload.question
    item.answer = payload.answer
    item.category_id = payload.category_id
    item.order = payload.order
    item.save()
    set_brands(item, payload.brand_ids)
    return FAQOut(
        id=item.id,
        question=item.question,
        answer=item.answer,
        category_id=item.category_id,
        order=item.order,
        brand_slugs=get_brand_slugs(item),
    )


@website_admin_router.delete(
    "/faqs/{faq_id}",
    response={200: StatusResponse, 401: ProblemDetail, 403: ProblemDetail},
)
def delete_faq(request: HttpRequest, faq_id: int):
    permission_error = require_permission(request, "website.delete_faq")
    if permission_error:
        return permission_error
    item = get_object_or_404(FAQ, id=faq_id)
    item.delete()
    return {"success": True, "message": "FAQ deleted."}


@website_admin_router.get(
    "/faqs/categories",
    response={200: list[FAQCategoryOut], 401: ProblemDetail, 403: ProblemDetail},
)
def list_faq_categories(request: HttpRequest):
    permission_error = require_permission(request, "website.view_faqcategory")
    if permission_error:
        return permission_error
    return [build_faq_category_response(item) for item in FAQCategory.objects.all()]


@website_admin_router.post(
    "/faqs/categories",
    response={200: FAQCategoryOut, 401: ProblemDetail, 403: ProblemDetail},
)
def create_faq_category(request: HttpRequest, payload: FAQCategoryIn):
    permission_error = require_permission(request, "website.add_faqcategory")
    if permission_error:
        return permission_error
    item = FAQCategory.objects.create(name=payload.name, slug=payload.slug, order=payload.order)
    set_brands(item, payload.brand_ids)
    return build_faq_category_response(item)


@website_admin_router.put(
    "/faqs/categories/{category_id}",
    response={200: FAQCategoryOut, 401: ProblemDetail, 403: ProblemDetail},
)
def update_faq_category(request: HttpRequest, category_id: int, payload: FAQCategoryIn):
    permission_error = require_permission(request, "website.change_faqcategory")
    if permission_error:
        return permission_error
    item = get_object_or_404(FAQCategory, id=category_id)
    item.name = payload.name
    item.slug = payload.slug
    item.order = payload.order
    item.save()
    set_brands(item, payload.brand_ids)
    return build_faq_category_response(item)


@website_admin_router.delete(
    "/faqs/categories/{category_id}",
    response={200: StatusResponse, 401: ProblemDetail, 403: ProblemDetail},
)
def delete_faq_category(request: HttpRequest, category_id: int):
    permission_error = require_permission(request, "website.delete_faqcategory")
    if permission_error:
        return permission_error
    item = get_object_or_404(FAQCategory, id=category_id)
    item.delete()
    return {"success": True, "message": "FAQ category deleted."}

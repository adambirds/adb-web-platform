import logging

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import Router

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
from .views import build_blog_post_response, build_image_url, parse_technologies

logger = logging.getLogger(__name__)

website_admin_router = Router()


def require_staff(request: HttpRequest):
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
    return None


@website_admin_router.get(
    "/website/portfolio",
    response={200: list[PortfolioOut], 401: ProblemDetail, 403: ProblemDetail},
)
def admin_list_portfolio(request: HttpRequest):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

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
        for item in Portfolio.objects.all()
    ]


@website_admin_router.post(
    "/website/portfolio",
    response={200: PortfolioOut, 400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail},
)
def admin_create_portfolio(request: HttpRequest, payload: PortfolioIn):
    auth_error = require_staff(request)
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

    return PortfolioOut(
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


@website_admin_router.get(
    "/website/portfolio/{portfolio_id}",
    response={200: PortfolioOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_get_portfolio(request: HttpRequest, portfolio_id: int):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    item = get_object_or_404(Portfolio, id=portfolio_id)
    return PortfolioOut(
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


@website_admin_router.put(
    "/website/portfolio/{portfolio_id}",
    response={200: PortfolioOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_update_portfolio(request: HttpRequest, portfolio_id: int, payload: PortfolioIn):
    auth_error = require_staff(request)
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

    return PortfolioOut(
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


@website_admin_router.delete(
    "/website/portfolio/{portfolio_id}",
    response={200: StatusResponse, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_delete_portfolio(request: HttpRequest, portfolio_id: int):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    item = get_object_or_404(Portfolio, id=portfolio_id)
    item.delete()
    return 200, {"message": "Portfolio deleted", "success": True}


@website_admin_router.get(
    "/website/testimonials",
    response={200: list[TestimonialOut], 401: ProblemDetail, 403: ProblemDetail},
)
def admin_list_testimonials(request: HttpRequest):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

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
        for item in Testimonial.objects.all()
    ]


@website_admin_router.post(
    "/website/testimonials",
    response={200: TestimonialOut, 400: ProblemDetail, 401: ProblemDetail, 403: ProblemDetail},
)
def admin_create_testimonial(request: HttpRequest, payload: TestimonialIn):
    auth_error = require_staff(request)
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

    return TestimonialOut(
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


@website_admin_router.get(
    "/website/testimonials/{testimonial_id}",
    response={200: TestimonialOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_get_testimonial(request: HttpRequest, testimonial_id: int):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    item = get_object_or_404(Testimonial, id=testimonial_id)
    return TestimonialOut(
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


@website_admin_router.put(
    "/website/testimonials/{testimonial_id}",
    response={200: TestimonialOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_update_testimonial(request: HttpRequest, testimonial_id: int, payload: TestimonialIn):
    auth_error = require_staff(request)
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

    return TestimonialOut(
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


@website_admin_router.delete(
    "/website/testimonials/{testimonial_id}",
    response={200: StatusResponse, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_delete_testimonial(request: HttpRequest, testimonial_id: int):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    item = get_object_or_404(Testimonial, id=testimonial_id)
    item.delete()
    return 200, {"message": "Testimonial deleted", "success": True}


@website_admin_router.get(
    "/website/blog/categories",
    response={200: list[BlogCategoryOut], 401: ProblemDetail, 403: ProblemDetail},
)
def admin_list_blog_categories(request: HttpRequest):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    return [
        BlogCategoryOut(
            id=item.id,
            name=item.name,
            slug=item.slug,
            description=item.description,
        )
        for item in BlogCategory.objects.all()
    ]


@website_admin_router.post(
    "/website/blog/categories",
    response={200: BlogCategoryOut, 401: ProblemDetail, 403: ProblemDetail},
)
def admin_create_blog_category(request: HttpRequest, payload: BlogCategoryIn):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    item = BlogCategory.objects.create(
        name=payload.name,
        slug=payload.slug,
        description=payload.description or "",
    )

    return BlogCategoryOut(
        id=item.id,
        name=item.name,
        slug=item.slug,
        description=item.description,
    )


@website_admin_router.put(
    "/website/blog/categories/{category_id}",
    response={200: BlogCategoryOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_update_blog_category(request: HttpRequest, category_id: int, payload: BlogCategoryIn):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    item = get_object_or_404(BlogCategory, id=category_id)
    item.name = payload.name
    item.slug = payload.slug
    item.description = payload.description or ""
    item.save()

    return BlogCategoryOut(
        id=item.id,
        name=item.name,
        slug=item.slug,
        description=item.description,
    )


@website_admin_router.delete(
    "/website/blog/categories/{category_id}",
    response={200: StatusResponse, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_delete_blog_category(request: HttpRequest, category_id: int):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    item = get_object_or_404(BlogCategory, id=category_id)
    item.delete()
    return 200, {"message": "Blog category deleted", "success": True}


@website_admin_router.get(
    "/website/blog/tags",
    response={200: list[BlogTagOut], 401: ProblemDetail, 403: ProblemDetail},
)
def admin_list_blog_tags(request: HttpRequest):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    return [
        BlogTagOut(
            id=item.id,
            name=item.name,
            slug=item.slug,
        )
        for item in BlogTag.objects.all()
    ]


@website_admin_router.post(
    "/website/blog/tags",
    response={200: BlogTagOut, 401: ProblemDetail, 403: ProblemDetail},
)
def admin_create_blog_tag(request: HttpRequest, payload: BlogTagIn):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    item = BlogTag.objects.create(
        name=payload.name,
        slug=payload.slug,
    )

    return BlogTagOut(
        id=item.id,
        name=item.name,
        slug=item.slug,
    )


@website_admin_router.put(
    "/website/blog/tags/{tag_id}",
    response={200: BlogTagOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_update_blog_tag(request: HttpRequest, tag_id: int, payload: BlogTagIn):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    item = get_object_or_404(BlogTag, id=tag_id)
    item.name = payload.name
    item.slug = payload.slug
    item.save()

    return BlogTagOut(
        id=item.id,
        name=item.name,
        slug=item.slug,
    )


@website_admin_router.delete(
    "/website/blog/tags/{tag_id}",
    response={200: StatusResponse, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_delete_blog_tag(request: HttpRequest, tag_id: int):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    item = get_object_or_404(BlogTag, id=tag_id)
    item.delete()
    return 200, {"message": "Blog tag deleted", "success": True}


@website_admin_router.get(
    "/website/blog/posts",
    response={200: list[BlogPostOut], 401: ProblemDetail, 403: ProblemDetail},
)
def admin_list_blog_posts(request: HttpRequest):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    qs = BlogPost.objects.prefetch_related("categories", "tags")
    return [build_blog_post_response(request, post) for post in qs]


@website_admin_router.post(
    "/website/blog/posts",
    response={200: BlogPostOut, 401: ProblemDetail, 403: ProblemDetail, 400: ProblemDetail},
)
def admin_create_blog_post(request: HttpRequest, payload: BlogPostIn):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    published_at = payload.published_at
    if payload.published and not published_at:
        published_at = timezone.now()

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
        published_at=published_at,
    )

    if payload.category_ids:
        post.categories.set(BlogCategory.objects.filter(id__in=payload.category_ids))
    if payload.tag_ids:
        post.tags.set(BlogTag.objects.filter(id__in=payload.tag_ids))

    post.refresh_from_db()
    return build_blog_post_response(request, post)


@website_admin_router.get(
    "/website/blog/posts/{post_id}",
    response={200: BlogPostOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_get_blog_post(request: HttpRequest, post_id: int):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    post = get_object_or_404(BlogPost.objects.prefetch_related("categories", "tags"), id=post_id)
    return build_blog_post_response(request, post)


@website_admin_router.put(
    "/website/blog/posts/{post_id}",
    response={200: BlogPostOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_update_blog_post(request: HttpRequest, post_id: int, payload: BlogPostIn):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    post = get_object_or_404(BlogPost, id=post_id)
    post.title = payload.title
    post.slug = payload.slug
    post.excerpt = payload.excerpt
    post.content = payload.content
    post.author = payload.author or "ADB Software Solutions"
    post.published = payload.published
    post.featured = payload.featured
    post.meta_description = payload.meta_description or ""
    post.meta_keywords = payload.meta_keywords or ""

    if payload.published and not post.published_at:
        post.published_at = payload.published_at or timezone.now()
    elif payload.published_at:
        post.published_at = payload.published_at

    post.save()

    if payload.category_ids is not None:
        post.categories.set(BlogCategory.objects.filter(id__in=payload.category_ids))
    if payload.tag_ids is not None:
        post.tags.set(BlogTag.objects.filter(id__in=payload.tag_ids))

    post.refresh_from_db()
    return build_blog_post_response(request, post)


@website_admin_router.delete(
    "/website/blog/posts/{post_id}",
    response={200: StatusResponse, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_delete_blog_post(request: HttpRequest, post_id: int):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    post = get_object_or_404(BlogPost, id=post_id)
    post.delete()
    return 200, {"message": "Blog post deleted", "success": True}


@website_admin_router.get(
    "/website/faqs/categories",
    response={200: list[FAQCategoryOut], 401: ProblemDetail, 403: ProblemDetail},
)
def admin_list_faq_categories(request: HttpRequest):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    return [
        FAQCategoryOut(
            id=item.id,
            name=item.name,
            slug=item.slug,
            description=item.description,
            order=item.order,
        )
        for item in FAQCategory.objects.all()
    ]


@website_admin_router.post(
    "/website/faqs/categories",
    response={200: FAQCategoryOut, 401: ProblemDetail, 403: ProblemDetail},
)
def admin_create_faq_category(request: HttpRequest, payload: FAQCategoryIn):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    item = FAQCategory.objects.create(
        name=payload.name,
        slug=payload.slug,
        description=payload.description or "",
        order=payload.order,
    )

    return FAQCategoryOut(
        id=item.id,
        name=item.name,
        slug=item.slug,
        description=item.description,
        order=item.order,
    )


@website_admin_router.put(
    "/website/faqs/categories/{category_id}",
    response={200: FAQCategoryOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_update_faq_category(request: HttpRequest, category_id: int, payload: FAQCategoryIn):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    item = get_object_or_404(FAQCategory, id=category_id)
    item.name = payload.name
    item.slug = payload.slug
    item.description = payload.description or ""
    item.order = payload.order
    item.save()

    return FAQCategoryOut(
        id=item.id,
        name=item.name,
        slug=item.slug,
        description=item.description,
        order=item.order,
    )


@website_admin_router.delete(
    "/website/faqs/categories/{category_id}",
    response={200: StatusResponse, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_delete_faq_category(request: HttpRequest, category_id: int):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    item = get_object_or_404(FAQCategory, id=category_id)
    item.delete()
    return 200, {"message": "FAQ category deleted", "success": True}


@website_admin_router.get(
    "/website/faqs",
    response={200: list[FAQOut], 401: ProblemDetail, 403: ProblemDetail},
)
def admin_list_faqs(request: HttpRequest):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    qs = FAQ.objects.select_related("category").all()
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


@website_admin_router.post(
    "/website/faqs",
    response={200: FAQOut, 401: ProblemDetail, 403: ProblemDetail},
)
def admin_create_faq(request: HttpRequest, payload: FAQIn):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    category = get_object_or_404(FAQCategory, id=payload.category_id)
    item = FAQ.objects.create(
        question=payload.question,
        answer=payload.answer,
        category=category,
        order=payload.order,
    )

    return FAQOut(
        id=item.id,
        question=item.question,
        answer=item.answer,
        category=FAQCategoryOut(
            id=category.id,
            name=category.name,
            slug=category.slug,
            description=category.description,
            order=category.order,
        ),
        order=item.order,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@website_admin_router.put(
    "/website/faqs/{faq_id}",
    response={200: FAQOut, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_update_faq(request: HttpRequest, faq_id: int, payload: FAQIn):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    item = get_object_or_404(FAQ, id=faq_id)
    category = get_object_or_404(FAQCategory, id=payload.category_id)
    item.question = payload.question
    item.answer = payload.answer
    item.category = category
    item.order = payload.order
    item.save()

    return FAQOut(
        id=item.id,
        question=item.question,
        answer=item.answer,
        category=FAQCategoryOut(
            id=category.id,
            name=category.name,
            slug=category.slug,
            description=category.description,
            order=category.order,
        ),
        order=item.order,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@website_admin_router.delete(
    "/website/faqs/{faq_id}",
    response={200: StatusResponse, 401: ProblemDetail, 403: ProblemDetail, 404: ProblemDetail},
)
def admin_delete_faq(request: HttpRequest, faq_id: int):
    auth_error = require_staff(request)
    if auth_error:
        return auth_error

    item = get_object_or_404(FAQ, id=faq_id)
    item.delete()
    return 200, {"message": "FAQ deleted", "success": True}

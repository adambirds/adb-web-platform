from __future__ import annotations

from datetime import datetime
from typing import Annotated
from urllib.parse import urlsplit

from ninja import Schema
from pydantic import AfterValidator, EmailStr, Field, field_validator

Slug = Annotated[str, Field(min_length=1, max_length=50, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]


def safe_external_url(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValueError("Use an absolute HTTP or HTTPS URL without credentials.")
    return value


ExternalURL = Annotated[str | None, Field(max_length=2000), AfterValidator(safe_external_url)]


class PortfolioOut(Schema):
    published: bool = False
    image_alt: str = Field(default="", max_length=300)
    featured_image_alt: str = Field(default="", max_length=300)
    meta_description: str = Field(default="", max_length=160)
    service_slugs: list[str] = Field(default_factory=list, max_length=30)
    id: int
    title: str
    slug: str
    description: str
    challenge: str
    solution: str
    results: str
    technologies: list[str]
    project_url: str | None = None
    github_url: str | None = None
    image_url: str | None = None
    featured_image_url: str | None = None
    featured: bool
    brand_slugs: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class TestimonialOut(Schema):
    published: bool = False
    image_alt: str = Field(default="", max_length=300)
    id: int
    quote: str
    client_name: str
    company: str
    job_title: str
    rating: int
    image_url: str | None = None
    featured: bool
    brand_slugs: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class BlogCategoryOut(Schema):
    id: int
    name: str
    slug: str
    description: str
    brand_slugs: list[str] = Field(default_factory=list)


class BlogTagOut(Schema):
    id: int
    name: str
    slug: str
    brand_slugs: list[str] = Field(default_factory=list)


class BlogPostOut(Schema):
    featured_image_alt: str = Field(default="", max_length=300)
    id: int
    title: str
    slug: str
    excerpt: str
    content: str
    featured_image_url: str | None = None
    author: str
    published: bool
    featured: bool
    categories: list[BlogCategoryOut]
    tags: list[BlogTagOut]
    brand_slugs: list[str] = Field(default_factory=list)
    meta_description: str
    meta_keywords: str
    created_at: datetime
    published_at: datetime | None = None
    updated_at: datetime


class FAQCategoryOut(Schema):
    id: int
    name: str
    slug: str
    description: str
    order: int
    brand_slugs: list[str] = Field(default_factory=list)


class FAQOut(Schema):
    published: bool = False
    service_slugs: list[str] = Field(default_factory=list)
    id: int
    question: str
    answer: str
    category: FAQCategoryOut
    order: int
    brand_slugs: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ContactRequest(Schema):
    name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    message: str = Field(min_length=10, max_length=10000)
    phone: str | None = Field(default=None, max_length=50)
    company: str | None = Field(default=None, max_length=200)
    website: str = Field(default="", max_length=500)
    source_path: str = Field(default="/contact/", max_length=300)

    @field_validator("name", "message")
    @classmethod
    def trim_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("source_path")
    @classmethod
    def relative_source(cls, value: str) -> str:
        if not value.startswith("/") or value.startswith("//") or "\n" in value:
            raise ValueError("Source must be a relative website path.")
        return value


class PortfolioIn(Schema):
    published: bool = False
    image_alt: str = Field(default="", max_length=300)
    featured_image_alt: str = Field(default="", max_length=300)
    meta_description: str = Field(default="", max_length=160)
    service_slugs: list[str] = Field(default_factory=list, max_length=30)
    title: str
    slug: Slug
    description: str
    challenge: str
    solution: str
    results: str
    technologies: list[str]
    project_url: ExternalURL = None
    github_url: ExternalURL = None
    featured: bool = False
    brand_ids: list[int] = Field(default_factory=list)


class TestimonialIn(Schema):
    published: bool = False
    image_alt: str = Field(default="", max_length=300)
    quote: str
    client_name: str
    company: str | None = None
    job_title: str | None = None
    rating: int = Field(default=5, ge=1, le=5)
    featured: bool = False
    brand_ids: list[int] = Field(default_factory=list)


class BlogCategoryIn(Schema):
    name: str
    slug: Slug
    description: str | None = None
    brand_ids: list[int] = Field(default_factory=list)


class BlogTagIn(Schema):
    name: str
    slug: Slug
    brand_ids: list[int] = Field(default_factory=list)


class BlogPostIn(Schema):
    featured_image_alt: str = Field(default="", max_length=300)
    title: str
    slug: Slug
    excerpt: str
    content: str
    author: str | None = None
    published: bool = False
    featured: bool = False
    brand_ids: list[int] = Field(default_factory=list)
    category_ids: list[int] = Field(default_factory=list)
    tag_ids: list[int] = Field(default_factory=list)
    meta_description: str | None = None
    meta_keywords: str | None = None
    published_at: datetime | None = None


class FAQCategoryIn(Schema):
    name: str
    slug: Slug
    description: str | None = None
    order: int = 0
    brand_ids: list[int] = Field(default_factory=list)


class FAQIn(Schema):
    published: bool = False
    service_slugs: list[str] = Field(default_factory=list, max_length=30)
    question: str
    answer: str
    category_id: int
    order: int = 0
    brand_ids: list[int] = Field(default_factory=list)


class PublicCollectionOut(Schema):
    items: list[PortfolioOut | BlogPostOut | TestimonialOut | FAQOut]
    total: int
    page: int
    page_size: int


class ContentImageOut(Schema):
    image_url: str | None = None

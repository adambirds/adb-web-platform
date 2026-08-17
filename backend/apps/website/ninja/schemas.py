from __future__ import annotations

from datetime import datetime

from ninja import Schema
from pydantic import EmailStr, Field


class PortfolioOut(Schema):
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
    id: int
    question: str
    answer: str
    category: FAQCategoryOut
    order: int
    brand_slugs: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ContactRequest(Schema):
    name: str
    email: EmailStr
    message: str
    phone: str | None = None
    company: str | None = None


class PortfolioIn(Schema):
    title: str
    slug: str
    description: str
    challenge: str
    solution: str
    results: str
    technologies: list[str]
    project_url: str | None = None
    github_url: str | None = None
    featured: bool = False
    brand_ids: list[int] = Field(default_factory=list)


class TestimonialIn(Schema):
    quote: str
    client_name: str
    company: str | None = None
    job_title: str | None = None
    rating: int = 5
    featured: bool = False
    brand_ids: list[int] = Field(default_factory=list)


class BlogCategoryIn(Schema):
    name: str
    slug: str
    description: str | None = None
    brand_ids: list[int] = Field(default_factory=list)


class BlogTagIn(Schema):
    name: str
    slug: str
    brand_ids: list[int] = Field(default_factory=list)


class BlogPostIn(Schema):
    title: str
    slug: str
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
    slug: str
    description: str | None = None
    order: int = 0
    brand_ids: list[int] = Field(default_factory=list)


class FAQIn(Schema):
    question: str
    answer: str
    category_id: int
    order: int = 0
    brand_ids: list[int] = Field(default_factory=list)

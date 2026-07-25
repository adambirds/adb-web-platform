from __future__ import annotations

from datetime import datetime
from typing import List

from ninja import Schema
from pydantic import EmailStr


class PortfolioOut(Schema):
    id: int
    title: str
    slug: str
    description: str
    challenge: str
    solution: str
    results: str
    technologies: List[str]
    project_url: str | None = None
    github_url: str | None = None
    image_url: str | None = None
    featured_image_url: str | None = None
    featured: bool
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
    created_at: datetime
    updated_at: datetime


class BlogCategoryOut(Schema):
    id: int
    name: str
    slug: str
    description: str


class BlogTagOut(Schema):
    id: int
    name: str
    slug: str


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
    categories: List[BlogCategoryOut]
    tags: List[BlogTagOut]
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


class FAQOut(Schema):
    id: int
    question: str
    answer: str
    category: FAQCategoryOut
    order: int
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
    technologies: List[str]
    project_url: str | None = None
    github_url: str | None = None
    featured: bool = False


class TestimonialIn(Schema):
    quote: str
    client_name: str
    company: str | None = None
    job_title: str | None = None
    rating: int = 5
    featured: bool = False


class BlogCategoryIn(Schema):
    name: str
    slug: str
    description: str | None = None


class BlogTagIn(Schema):
    name: str
    slug: str


class BlogPostIn(Schema):
    title: str
    slug: str
    excerpt: str
    content: str
    author: str | None = None
    published: bool = False
    featured: bool = False
    category_ids: List[int] = []
    tag_ids: List[int] = []
    meta_description: str | None = None
    meta_keywords: str | None = None
    published_at: datetime | None = None


class FAQCategoryIn(Schema):
    name: str
    slug: str
    description: str | None = None
    order: int = 0


class FAQIn(Schema):
    question: str
    answer: str
    category_id: int
    order: int = 0

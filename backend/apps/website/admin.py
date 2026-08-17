from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import FAQ, BlogCategory, BlogPost, BlogTag, FAQCategory, Portfolio, Testimonial


@admin.register(Portfolio)
class PortfolioAdmin(ModelAdmin):
    list_display = ("title", "slug", "featured", "created_at")
    list_filter = ("brands", "featured", "created_at")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("brands",)


@admin.register(Testimonial)
class TestimonialAdmin(ModelAdmin):
    list_display = ("client_name", "company", "rating", "featured", "created_at")
    list_filter = ("brands", "rating", "featured", "created_at")
    search_fields = ("client_name", "company", "quote")
    filter_horizontal = ("brands",)


@admin.register(BlogPost)
class BlogPostAdmin(ModelAdmin):
    list_display = ("title", "slug", "published", "created_at")
    list_filter = ("brands", "published", "created_at", "categories")
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("brands", "categories", "tags")


@admin.register(BlogCategory)
class BlogCategoryAdmin(ModelAdmin):
    list_display = ("name", "slug")
    list_filter = ("brands",)
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("brands",)


@admin.register(BlogTag)
class BlogTagAdmin(ModelAdmin):
    list_display = ("name", "slug")
    list_filter = ("brands",)
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("brands",)


@admin.register(FAQ)
class FAQAdmin(ModelAdmin):
    list_display = ("question", "category", "order")
    list_filter = ("brands", "category")
    search_fields = ("question", "answer")
    filter_horizontal = ("brands",)


@admin.register(FAQCategory)
class FAQCategoryAdmin(ModelAdmin):
    list_display = ("name", "order")
    list_filter = ("brands",)
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("brands",)

from django.contrib import admin

from .models import FAQ, BlogCategory, BlogPost, BlogTag, FAQCategory, Portfolio, Testimonial

# Register your models here.


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "featured", "created_at")
    list_filter = ("featured", "created_at")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("client_name", "company", "rating", "featured", "created_at")
    list_filter = ("rating", "featured", "created_at")
    search_fields = ("client_name", "company", "quote")


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "published", "created_at")
    list_filter = ("published", "created_at", "categories")
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("categories", "tags")


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "category", "order")
    list_filter = ("category",)
    search_fields = ("question", "answer")


@admin.register(FAQCategory)
class FAQCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order")

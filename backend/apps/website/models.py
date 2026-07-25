from django.db import models


class Portfolio(models.Model):
    """Portfolio project"""

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    challenge = models.TextField(help_text="Problem statement or challenge")
    solution = models.TextField(help_text="How we solved it")
    results = models.TextField(help_text="Outcome and results")
    image = models.ImageField(upload_to="portfolio/", blank=True)
    featured = models.BooleanField(default=False)
    featured_image = models.ImageField(upload_to="portfolio/featured/", blank=True)

    # Tech stack
    technologies = models.TextField(help_text="Comma-separated list of technologies")

    # Links
    project_url = models.URLField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Testimonial(models.Model):
    """Client testimonial"""

    RATING_CHOICES = [
        (5, "⭐⭐⭐⭐⭐"),
        (4, "⭐⭐⭐⭐"),
        (3, "⭐⭐⭐"),
        (2, "⭐⭐"),
        (1, "⭐"),
    ]

    quote = models.TextField()
    client_name = models.CharField(max_length=150)
    company = models.CharField(max_length=200, blank=True)
    job_title = models.CharField(max_length=150, blank=True)
    rating = models.IntegerField(choices=RATING_CHOICES, default=5)
    image = models.ImageField(upload_to="testimonials/", blank=True)
    featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.client_name} - {self.company}"


class BlogCategory(models.Model):
    """Blog post category"""

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Blog Categories"

    def __str__(self):
        return self.name


class BlogTag(models.Model):
    """Blog post tag"""

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    """Blog post"""

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    excerpt = models.TextField(max_length=500)
    content = models.TextField(help_text="Markdown content")
    featured_image = models.ImageField(upload_to="blog/", blank=True)

    author = models.CharField(max_length=100, default="ADB Software Solutions")

    published = models.BooleanField(default=False)
    featured = models.BooleanField(default=False)

    categories = models.ManyToManyField(BlogCategory, related_name="posts")
    tags = models.ManyToManyField(BlogTag, related_name="posts")

    # SEO
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title


class FAQ(models.Model):
    """FAQ item"""

    question = models.CharField(max_length=500)
    answer = models.TextField(help_text="Markdown content")
    category = models.ForeignKey("FAQCategory", on_delete=models.CASCADE, related_name="faqs")
    order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.question


class FAQCategory(models.Model):
    """FAQ category"""

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name_plural = "FAQ Categories"

    def __str__(self):
        return self.name

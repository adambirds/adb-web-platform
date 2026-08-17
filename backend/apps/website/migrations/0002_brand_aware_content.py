from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
        ("website", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="portfolio",
            name="brands",
            field=models.ManyToManyField(related_name="portfolio_entries", to="core.brand"),
        ),
        migrations.AddField(
            model_name="testimonial",
            name="brands",
            field=models.ManyToManyField(related_name="testimonials", to="core.brand"),
        ),
        migrations.AddField(
            model_name="blogcategory",
            name="brands",
            field=models.ManyToManyField(related_name="blog_categories", to="core.brand"),
        ),
        migrations.AddField(
            model_name="blogtag",
            name="brands",
            field=models.ManyToManyField(related_name="blog_tags", to="core.brand"),
        ),
        migrations.AddField(
            model_name="blogpost",
            name="brands",
            field=models.ManyToManyField(related_name="blog_posts", to="core.brand"),
        ),
        migrations.AddField(
            model_name="faq",
            name="brands",
            field=models.ManyToManyField(related_name="faqs", to="core.brand"),
        ),
        migrations.AddField(
            model_name="faqcategory",
            name="brands",
            field=models.ManyToManyField(related_name="faq_categories", to="core.brand"),
        ),
    ]

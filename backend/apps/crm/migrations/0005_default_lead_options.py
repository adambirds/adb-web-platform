from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def seed_options(apps: Apps, _schema_editor: BaseDatabaseSchemaEditor) -> None:
    status_model = apps.get_model("crm", "LeadStatus")
    source_model = apps.get_model("crm", "LeadSource")
    for order, name, outcome in [
        (10, "New", "open"),
        (20, "Contacted", "open"),
        (30, "Qualified", "open"),
        (40, "Proposal", "open"),
        (45, "Negotiation", "open"),
        (50, "Won", "won"),
        (60, "Lost", "lost"),
    ]:
        if not status_model.objects.filter(name__iexact=name).exists():
            status_model.objects.create(name=name, order=order, outcome=outcome)
    for name in [
        "Email",
        "Phone",
        "Website",
        "Contact Form",
        "Referral",
        "LinkedIn",
        "Facebook",
        "Instagram",
        "X / Twitter",
        "TikTok",
        "YouTube",
        "WhatsApp",
        "Organic search",
        "Paid advertising",
        "Event / networking",
        "Other",
    ]:
        if not source_model.objects.filter(name__iexact=name).exists():
            source_model.objects.create(name=name)


class Migration(migrations.Migration):
    dependencies = [("crm", "0004_leadstatus_outcome")]
    # Keep catalogue entries on rollback: users may already reference them.
    operations = [migrations.RunPython(seed_options, migrations.RunPython.noop)]

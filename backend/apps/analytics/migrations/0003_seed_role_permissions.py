"""Business roles reuse Django Groups without granting global staff membership."""

from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps


def seed_roles(apps: StateApps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    group_model = apps.get_model("auth", "Group")
    permission_model = apps.get_model("auth", "Permission")
    content_type_model = apps.get_model("contenttypes", "ContentType")
    viewer = {"view_business", "view_website", "view_report", "view_googleconnection"}
    admin = viewer | {
        "change_website",
        "add_website",
        "change_googleconnection",
        "change_eventdefinition",
        "sync_providerproperty",
    }
    roles = {
        "Viewer": viewer,
        "Admin": admin,
        "Owner": admin | {"change_business", "change_businessmembership"},
    }
    alias = schema_editor.connection.alias
    for role, capabilities in roles.items():
        group, _ = group_model.objects.using(alias).get_or_create(name=f"Analytics / {role}")
        permissions = []
        for capability in sorted(capabilities):
            model = "business" if capability == "view_report" else capability.split("_", 1)[1]
            content_type, _ = content_type_model.objects.using(alias).get_or_create(
                app_label="analytics", model=model
            )
            permission, _ = permission_model.objects.using(alias).get_or_create(
                content_type=content_type,
                codename=capability,
                defaults={"name": "Can " + capability.replace("_", " ")},
            )
            permissions.append(permission)
        group.permissions.set(permissions)


class Migration(migrations.Migration):
    dependencies = [
        ("analytics", "0002_alter_business_options_and_more"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]
    operations = [migrations.RunPython(seed_roles, migrations.RunPython.noop)]

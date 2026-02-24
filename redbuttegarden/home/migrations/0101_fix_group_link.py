from django.db import migrations


def fix_navbar_group_link(apps, schema_editor):
    NavigationSettings = apps.get_model("home", "NavigationSettings")

    for ns in NavigationSettings.objects.all().iterator():
        # IMPORTANT: bypass StreamField conversion entirely
        raw = ns.__dict__.get("navbar")

        if not raw:
            continue

        changed = False

        # raw should be a list of {"type": "...", "value": {...}, "id": "..."}
        if isinstance(raw, list):
            for block in raw:
                if not isinstance(block, dict):
                    continue
                if block.get("type") != "group":
                    continue

                value = block.get("value")
                if not isinstance(value, dict):
                    value = {}
                    block["value"] = value
                    changed = True

                # group_link used to be a StructBlock and got stored as null
                # now it's a StreamBlock(max_num=1), so empty should be []
                if value.get("group_link", "MISSING") is None:
                    value["group_link"] = []
                    changed = True
                elif "group_link" not in value:
                    value["group_link"] = []
                    changed = True

        if changed:
            # assign raw JSON back; this still bypasses conversion
            ns.__dict__["navbar"] = raw
            ns.save(update_fields=["navbar"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0100_alter_navigationsettings_navbar"),
    ]

    operations = [
        migrations.RunPython(fix_navbar_group_link, noop),
    ]

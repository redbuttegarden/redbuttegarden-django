# home/migrations/0102_normalize_navigationsettings_stream_data.py
from __future__ import annotations

import json
import uuid

from django.db import migrations


def _as_streamblock_list(value):
    """
    Normalize a StreamBlock value to a list of {"type","value","id"} dicts.

    For NavGroupBlock.group_link (StreamBlock max_num=1), the valid empty value is [].
    This also handles older/invalid shapes:
      - None / "" / {} => []
      - dict => [{"type": "link", "value": dict, "id": "..."}]
      - list missing ids => adds ids
      - list of dicts without type/value => wraps as link
    """
    if value is None or value == "" or value == {}:
        return []

    if isinstance(value, list):
        fixed = []
        for item in value:
            if item is None:
                continue

            if isinstance(item, dict) and "type" in item and "value" in item:
                if "id" not in item:
                    item["id"] = str(uuid.uuid4())
                fixed.append(item)
                continue

            if isinstance(item, dict):
                fixed.append({"type": "link", "value": item, "id": str(uuid.uuid4())})
                continue

            # Unknown junk; drop it
        return fixed

    if isinstance(value, dict):
        return [{"type": "link", "value": value, "id": str(uuid.uuid4())}]

    return []


def _normalize_link_value(link_val):
    """
    Your LinkBlock uses TextBlock for route_args_json / route_kwargs_json.
    Normalize list/dict to JSON strings so the StreamField editor won't choke.
    """
    if not isinstance(link_val, dict):
        return link_val

    ra = link_val.get("route_args_json")
    rk = link_val.get("route_kwargs_json")

    if isinstance(ra, (list, dict)):
        link_val["route_args_json"] = json.dumps(ra) if ra else ""

    if isinstance(rk, (dict, list)):
        link_val["route_kwargs_json"] = json.dumps(rk) if rk else ""

    return link_val


def normalize_navigation_settings(apps, schema_editor):
    """
    Bypass Wagtail StreamField conversion entirely by using SQL.
    This is necessary when existing stored JSON is invalid and crashes conversion.
    """
    table = "home_navigationsettings"  # adjust if your db_table differs

    # Update these if your column names differ
    navbar_col = "navbar"
    top_links_col = "top_links"  # if you don't have this column, remove references

    with schema_editor.connection.cursor() as cursor:
        # Detect which columns exist (so this migration doesn't break if top_links isn't present)
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s
            """,
            [table],
        )
        cols = {row[0] for row in cursor.fetchall()}

    has_navbar = navbar_col in cols
    has_top_links = top_links_col in cols

    if not has_navbar and not has_top_links:
        return

    select_cols = ["id"]
    if has_navbar:
        select_cols.append(navbar_col)
    if has_top_links:
        select_cols.append(top_links_col)

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f"SELECT {', '.join(select_cols)} FROM {table}")
        rows = cursor.fetchall()

    for row in rows:
        # Unpack dynamically
        idx = 0
        pk = row[idx]
        idx += 1

        navbar_raw = None
        top_links_raw = None
        if has_navbar:
            navbar_raw = row[idx]
            idx += 1
        if has_top_links:
            top_links_raw = row[idx]
            idx += 1

        updates = {}

        # ---- Normalize navbar (group_link + nested link JSON fields) ----
        if has_navbar and navbar_raw:
            navbar = json.loads(navbar_raw) if isinstance(navbar_raw, str) else navbar_raw
            changed = False

            if isinstance(navbar, list):
                for block in navbar:
                    if not isinstance(block, dict) or block.get("type") != "group":
                        continue

                    val = block.get("value")
                    if not isinstance(val, dict):
                        val = {}
                        block["value"] = val
                        changed = True

                    # group_link is now a StreamBlock => MUST be a list, never null
                    normalized_gl = _as_streamblock_list(val.get("group_link", None))
                    if val.get("group_link") != normalized_gl:
                        val["group_link"] = normalized_gl
                        changed = True

                    # Normalize LinkBlock values inside links list
                    links = val.get("links")
                    if isinstance(links, list):
                        for link in links:
                            if isinstance(link, dict):
                                before = (link.get("route_args_json"), link.get("route_kwargs_json"))
                                _normalize_link_value(link)
                                after = (link.get("route_args_json"), link.get("route_kwargs_json"))
                                if before != after:
                                    changed = True

            if changed:
                updates[navbar_col] = json.dumps(navbar)

        # ---- Normalize top_links (route_args_json/kwargs_json consistency) ----
        # top_links usually doesn't contain nested StreamBlocks, but the JSON string / dict issue can still exist.
        if has_top_links and top_links_raw:
            top_links = json.loads(top_links_raw) if isinstance(top_links_raw, str) else top_links_raw
            changed = False

            if isinstance(top_links, list):
                for block in top_links:
                    if not isinstance(block, dict):
                        continue
                    val = block.get("value")
                    if isinstance(val, dict):
                        before = (val.get("route_args_json"), val.get("route_kwargs_json"))
                        _normalize_link_value(val)
                        after = (val.get("route_args_json"), val.get("route_kwargs_json"))
                        if before != after:
                            changed = True

            if changed:
                updates[top_links_col] = json.dumps(top_links)

        if updates:
            set_sql = ", ".join([f"{col} = %s" for col in updates.keys()])
            params = list(updates.values()) + [pk]
            with schema_editor.connection.cursor() as cursor:
                cursor.execute(
                    f"UPDATE {table} SET {set_sql} WHERE id = %s",
                    params,
                )


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0101_fix_group_link"),
    ]

    operations = [
        migrations.RunPython(normalize_navigation_settings, migrations.RunPython.noop),
    ]
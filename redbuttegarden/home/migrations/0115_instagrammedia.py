"""Add immutable identity mappings for imported Instagram media."""

from typing import Any

from django.db import migrations, models
import django.db.models.deletion


def backfill_legacy_instagram_media(apps: Any, schema_editor: Any) -> None:
    """Map legacy image titles that use the historical media-ID convention."""

    InstagramMedia = apps.get_model("home", "InstagramMedia")
    Image = apps.get_model("wagtailimages", "Image")
    prefix = "Instagram Image "
    for image in Image.objects.filter(title__startswith=prefix).iterator():
        external_id = image.title[len(prefix):].strip()
        if external_id.isascii() and external_id.isdecimal() and len(external_id) <= 255:
            InstagramMedia.objects.get_or_create(
                external_id=external_id, defaults={"image_id": image.pk}
            )


class Migration(migrations.Migration):
    """Create and backfill immutable mappings for imported Instagram media."""

    dependencies = [
        ("home", "0114_alter_generalindexpage_body_alter_generalpage_body"),
        ("wagtailimages", "0027_image_description"),
    ]

    operations = [
        migrations.CreateModel(
            name="InstagramMedia",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("external_id", models.CharField(max_length=255, unique=True)),
                (
                    "image",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="instagram_media_mapping",
                        to="wagtailimages.image",
                    ),
                ),
            ],
        ),
        migrations.RunPython(backfill_legacy_instagram_media, migrations.RunPython.noop),
    ]

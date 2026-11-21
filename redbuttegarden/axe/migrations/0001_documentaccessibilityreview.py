# Generated manually for the existing axe application.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.WAGTAILDOCS_DOCUMENT_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentAccessibilityReview",
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
                ("needs_accessibility_review", models.BooleanField(default=True)),
                ("notes", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "document",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="accessibility_review",
                        to=settings.WAGTAILDOCS_DOCUMENT_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "document accessibility review",
                "verbose_name_plural": "document accessibility reviews",
                "ordering": ("needs_accessibility_review", "document__title"),
            },
        ),
    ]

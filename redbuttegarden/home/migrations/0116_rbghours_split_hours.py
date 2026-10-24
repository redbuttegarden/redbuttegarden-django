"""Add optional labels and additional periods without rewriting existing hours."""

from django.db import migrations, models
from wagtail.fields import StreamField

from home.hour_blocks import OpeningPeriodBlock


class Migration(migrations.Migration):
    """Add split opening hours with empty defaults for legacy snippets."""

    dependencies = [("home", "0115_instagrammedia")]

    operations = [
        migrations.AddField(
            model_name="rbghours",
            name="garden_hours_label",
            field=models.CharField(
                max_length=200, blank=True, default="",
                help_text="Optional label for the primary hours, e.g. Regular visitation",
            ),
        ),
        migrations.AddField(
            model_name="rbghours",
            name="additional_hours",
            field=StreamField(
                [("opening_period", OpeningPeriodBlock())],
                blank=True, default=list,
                help_text="Add separate opening periods on the same day. Periods must not overlap.",
            ),
        ),
    ]

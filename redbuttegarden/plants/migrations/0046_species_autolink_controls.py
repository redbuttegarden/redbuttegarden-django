from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ("plants", "0045_species_arborist_rec"),
    ]

    operations = [
        migrations.AddField(
            model_name="species",
            name="autolink_aliases",
            field=models.TextField(
                blank=True,
                help_text=_("Optional additional link names, one per line. The scientific full name is always included while auto-linking is enabled."),
            ),
        ),
        migrations.AddField(
            model_name="species",
            name="autolink_enabled",
            field=models.BooleanField(
                default=True,
                help_text=_("If enabled, matching species names in rich text will automatically link to this species page."),
            ),
        ),
    ]

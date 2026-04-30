from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plants", "0046_species_autolink_controls"),
    ]

    operations = [
        migrations.CreateModel(
            name="SpeciesAutolinkIndex",
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
                ("version", models.PositiveIntegerField(default=1)),
            ],
            options={
                "verbose_name": "species autolink index",
                "verbose_name_plural": "species autolink index",
            },
        ),
    ]

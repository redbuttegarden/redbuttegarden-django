# Generated by Django 3.2.5 on 2021-10-13 19:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plants', '0030_species_high_elevation'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='species',
            constraint=models.CheckConstraint(check=models.Q(('vernacular_name__length__gt', 0)), name='vernacular_name_not_empty'),
        ),
    ]

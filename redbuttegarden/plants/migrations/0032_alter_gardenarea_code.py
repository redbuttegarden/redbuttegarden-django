# Generated by Django 3.2.5 on 2021-10-13 23:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plants', '0031_species_vernacular_name_not_empty'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gardenarea',
            name='code',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
    ]

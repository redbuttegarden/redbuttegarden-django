# Generated by Django 3.0.10 on 2021-07-14 20:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plants', '0020_auto_20210714_1415'),
    ]

    operations = [
        migrations.AddField(
            model_name='species',
            name='flower_color',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
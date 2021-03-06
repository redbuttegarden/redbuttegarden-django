# Generated by Django 3.0.10 on 2021-01-21 18:21

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('journal', '0016_auto_20210121_1106'),
    ]

    operations = [
        migrations.AddField(
            model_name='journalpage',
            name='authors',
            field=models.ManyToManyField(blank=True, related_name='author_posts', to=settings.AUTH_USER_MODEL, verbose_name='Authors'),
        ),
    ]

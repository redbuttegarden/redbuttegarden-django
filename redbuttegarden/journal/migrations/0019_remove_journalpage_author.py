# Generated by Django 3.0.10 on 2021-01-21 18:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('journal', '0018_auto_20210121_1122'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='journalpage',
            name='author',
        ),
    ]

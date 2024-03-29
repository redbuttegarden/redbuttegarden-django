# Generated by Django 4.1.3 on 2023-01-20 22:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('journal', '0029_journalindexpage_dialog_content_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='journalindexpage',
            name='dialog_display',
            field=models.BooleanField(blank=True, default=False, help_text='Should this dialog be displayed?', null=True),
        ),
        migrations.AlterField(
            model_name='journalpage',
            name='dialog_display',
            field=models.BooleanField(blank=True, default=False, help_text='Should this dialog be displayed?', null=True),
        ),
    ]

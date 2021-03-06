# Generated by Django 3.0.10 on 2021-01-09 21:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0022_uploadedimage'),
        ('journal', '0010_auto_20210109_1424'),
    ]

    operations = [
        migrations.AddField(
            model_name='journalindexpage',
            name='thumbnail',
            field=models.ForeignKey(blank=True, help_text='You only need to add a thumbnail if this page is the child of a general index page', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailimages.Image'),
        ),
    ]

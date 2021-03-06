# Generated by Django 3.0.4 on 2020-04-09 22:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0001_squashed_0021'),
        ('home', '0012_auto_20200318_1023'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generalpage',
            name='thumbnail',
            field=models.ForeignKey(blank=True, help_text='You only need to add a thumbnail if this page is the child of a general index page', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailimages.Image'),
        ),
    ]

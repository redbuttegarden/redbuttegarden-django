# Generated by Django 3.0.10 on 2021-03-24 17:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0060_fix_workflow_unique_constraint'),
        ('home', '0061_auto_20210313_1109'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventslides',
            name='alternate_link',
            field=models.URLField(blank=True, help_text='Link to external URL or non-page Wagtail view', null=True),
        ),
        migrations.AlterField(
            model_name='eventslides',
            name='link',
            field=models.ForeignKey(blank=True, help_text='Link to Wagtail page', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailcore.Page'),
        ),
    ]

# Generated by Django 3.0.10 on 2021-03-27 20:45

from django.db import migrations
import wagtail.blocks
import wagtail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('journal', '0021_journalindexpage_bottom_button_info'),
    ]

    operations = [
        migrations.AlterField(
            model_name='journalindexpage',
            name='bottom_button_info',
            field=wagtail.fields.StreamField([('dropdown_button_list', wagtail.blocks.StructBlock([('list_items', wagtail.blocks.ListBlock(wagtail.blocks.StructBlock([('button_text', wagtail.blocks.CharBlock(label='Button Text', max_length=200)), ('info_text', wagtail.blocks.RichTextBlock(features=['h4', 'h5', 'bold', 'italic', 'link', 'ul'], label='Info Text'))]), label='Button'))]))], blank=True, help_text='Dropdown buttons appear below the list of child pages', null=True),
        ),
    ]

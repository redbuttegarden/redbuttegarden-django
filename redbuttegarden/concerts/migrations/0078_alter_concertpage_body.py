# Generated by Django 4.2.17 on 2025-03-01 00:30

import datetime
from django.db import migrations
import wagtail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('concerts', '0077_alter_concertpage_body_alter_donorpackagepage_body_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='concertpage',
            name='body',
            field=wagtail.fields.StreamField([('concerts', 15)], blank=True, block_lookup={0: ('wagtail.images.blocks.ImageBlock', [], {}), 1: ('wagtail.blocks.ChoiceBlock', [], {'choices': [(0, 'Presale'), (1, 'Wave 1'), (2, 'Wave 2')], 'required': False}), 2: ('wagtail.blocks.BooleanBlock', (), {'default': True, 'help_text': 'If hidden box is checked, concert will not be displayed on the page', 'required': False}), 3: ('wagtail.blocks.BooleanBlock', (), {'default': True, 'help_text': 'If unchecked, Buy Tickets button will be grayed out', 'required': False}), 4: ('wagtail.blocks.BooleanBlock', (), {'default': False, 'help_text': 'Is this a virtual concert?', 'required': False}), 5: ('wagtail.blocks.BooleanBlock', (), {'default': False, 'required': False}), 6: ('wagtail.blocks.DateTimeBlock', (), {'blank': True, 'help_text': 'Date that on-demand virtual concert will remain available until', 'null': True, 'required': False}), 7: ('wagtail.blocks.RichTextBlock', (), {'help_text': 'Provide the names of the bands/openers and any other info here. Text will be centered.'}), 8: ('wagtail.blocks.DateTimeBlock', (), {}), 9: ('wagtail.blocks.ListBlock', (8,), {}), 10: ('wagtail.blocks.TimeBlock', (), {'blank': True, 'default': datetime.time(18, 0), 'null': True, 'required': False}), 11: ('wagtail.blocks.TimeBlock', (), {'blank': True, 'default': datetime.time(19, 0), 'null': True, 'required': False}), 12: ('wagtail.blocks.CharBlock', (), {'blank': True, 'default': '$', 'max_length': 100, 'null': True}), 13: ('wagtail.blocks.CharBlock', (), {'default': '$', 'max_length': 100}), 14: ('wagtail.blocks.URLBlock', (), {'default': 'https://www.etix.com/ticket/e/1049536/2025-red-butte-season-salt-lake-city-red-butte-garden-arboretum'}), 15: ('wagtail.blocks.StructBlock', [[('band_img', 0), ('wave', 1), ('hidden', 2), ('on_sale', 3), ('virtual', 4), ('canceled', 5), ('postponed', 5), ('sold_out', 5), ('available_until', 6), ('band_info', 7), ('concert_dates', 9), ('gates_time', 10), ('show_time', 11), ('member_price', 12), ('public_price', 13), ('ticket_url', 14)]], {})}, null=True),
        ),
    ]

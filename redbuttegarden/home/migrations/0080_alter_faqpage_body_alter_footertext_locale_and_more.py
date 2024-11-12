# Generated by Django 4.2.13 on 2024-11-08 23:57

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import re
import wagtail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0094_alter_page_locale'),
        ('home', '0079_alter_generalindexpage_body_alter_generalpage_body_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='faqpage',
            name='body',
            field=wagtail.fields.StreamField([('heading', 0), ('paragraph', 4), ('dropdown_button_list', 9), ('image', 10), ('html', 11), ('FAQ_list', 16)], block_lookup={0: ('home.models.Heading', (), {'form_classname': 'full title', 'help_text': 'Text will be green and centered'}), 1: ('wagtail.blocks.ChoiceBlock', [], {'choices': [('left', 'Left'), ('text-center', 'Center'), ('right', 'Right')]}), 2: ('wagtail.blocks.ChoiceBlock', [], {'choices': [('default', 'Default'), ('tan-bg', 'Tan'), ('green-bg', 'Green'), ('dark-tan-bg', 'Dark Tan'), ('white-bg', 'White'), ('red-bg', 'Red'), ('orange-bg', 'Orange')]}), 3: ('wagtail.blocks.RichTextBlock', (), {}), 4: ('wagtail.blocks.StructBlock', [[('alignment', 1), ('background_color', 2), ('paragraph', 3)]], {'classname': 'paragraph', 'required': True}), 5: ('wagtail.blocks.CharBlock', (), {'label': 'Button Text', 'max_length': 200}), 6: ('wagtail.blocks.RichTextBlock', (), {'features': ['h4', 'h5', 'bold', 'italic', 'link', 'document-link', 'ul'], 'label': 'Info Text'}), 7: ('wagtail.blocks.StructBlock', [[('button_text', 5), ('info_text', 6)]], {}), 8: ('wagtail.blocks.ListBlock', (7,), {'label': 'Button'}), 9: ('wagtail.blocks.StructBlock', [[('list_items', 8)]], {}), 10: ('wagtail.images.blocks.ImageBlock', [], {}), 11: ('wagtail.blocks.RawHTMLBlock', (), {}), 12: ('wagtail.blocks.CharBlock', (), {'label': 'Title/Question', 'max_length': 200}), 13: ('wagtail.blocks.StructBlock', [[('alignment', 1), ('background_color', 2), ('paragraph', 3)]], {'label': 'Answer'}), 14: ('wagtail.blocks.StructBlock', [[('title_question', 12), ('text', 13)]], {}), 15: ('wagtail.blocks.ListBlock', (14,), {'label': 'Question & Answer'}), 16: ('wagtail.blocks.StructBlock', [[('list_items', 15)]], {})}),
        ),
        migrations.AlterField(
            model_name='footertext',
            name='locale',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailcore.locale', verbose_name='locale'),
        ),
        migrations.AlterField(
            model_name='generalindexpage',
            name='body',
            field=wagtail.fields.StreamField([('heading', 0), ('emphatic_text', 1), ('paragraph', 5), ('image', 6), ('html', 7), ('dropdown_image_list', 13), ('dropdown_button_list', 18), ('image_link_list', 23), ('button', 28), ('button_row', 30)], blank=True, block_lookup={0: ('home.models.Heading', (), {'form_classname': 'full title', 'help_text': 'Text will be green and centered'}), 1: ('home.models.EmphaticText', (), {'form_classname': 'full title', 'help_text': 'Text will be red, italic and centered'}), 2: ('wagtail.blocks.ChoiceBlock', [], {'choices': [('left', 'Left'), ('text-center', 'Center'), ('right', 'Right')]}), 3: ('wagtail.blocks.ChoiceBlock', [], {'choices': [('default', 'Default'), ('tan-bg', 'Tan'), ('green-bg', 'Green'), ('dark-tan-bg', 'Dark Tan'), ('white-bg', 'White'), ('red-bg', 'Red'), ('orange-bg', 'Orange')]}), 4: ('wagtail.blocks.RichTextBlock', (), {}), 5: ('wagtail.blocks.StructBlock', [[('alignment', 2), ('background_color', 3), ('paragraph', 4)]], {'classname': 'paragraph', 'required': True}), 6: ('wagtail.images.blocks.ImageBlock', [], {}), 7: ('wagtail.blocks.RawHTMLBlock', (), {}), 8: ('wagtail.images.blocks.ImageBlock', [], {'label': 'Image'}), 9: ('wagtail.blocks.CharBlock', (), {'label': 'Title', 'max_length': 200}), 10: ('wagtail.blocks.RichTextBlock', (), {'label': 'Text'}), 11: ('wagtail.blocks.StructBlock', [[('image', 8), ('title', 9), ('text', 10)]], {}), 12: ('wagtail.blocks.ListBlock', (11,), {'label': 'List Item'}), 13: ('wagtail.blocks.StructBlock', [[('list_items', 12)]], {}), 14: ('wagtail.blocks.CharBlock', (), {'label': 'Button Text', 'max_length': 200}), 15: ('wagtail.blocks.RichTextBlock', (), {'features': ['h4', 'h5', 'bold', 'italic', 'link', 'document-link', 'ul'], 'label': 'Info Text'}), 16: ('wagtail.blocks.StructBlock', [[('button_text', 14), ('info_text', 15)]], {}), 17: ('wagtail.blocks.ListBlock', (16,), {'label': 'Button'}), 18: ('wagtail.blocks.StructBlock', [[('list_items', 17)]], {}), 19: ('wagtail.blocks.CharBlock', (), {'label': 'Title', 'max_length': 200, 'required': False}), 20: ('wagtail.blocks.URLBlock', (), {'label': 'URL'}), 21: ('wagtail.blocks.StructBlock', [[('title', 19), ('url', 20), ('image', 6)]], {}), 22: ('wagtail.blocks.ListBlock', (21,), {'label': 'Image Links'}), 23: ('wagtail.blocks.StructBlock', [[('list_items', 22)]], {}), 24: ('wagtail.blocks.CharBlock', (), {'max_length': 100}), 25: ('wagtail.blocks.URLBlock', (), {}), 26: ('wagtail.blocks.ChoiceBlock', [], {'choices': [('dk-tn', 'Dark Tan'), ('green', 'Green'), ('orange', 'Orange'), ('red', 'Red'), ('tan', 'Tan'), ('black', 'Black'), ('white', 'White')]}), 27: ('wagtail.blocks.ChoiceBlock', [], {'choices': [('center', 'Center'), ('justify', 'Justified'), ('left', 'Left'), ('right', 'Right')]}), 28: ('wagtail.blocks.StructBlock', [[('text', 24), ('url', 25), ('color', 26), ('alignment', 27)]], {}), 29: ('wagtail.blocks.ListBlock', (28,), {'label': 'Button'}), 30: ('wagtail.blocks.StructBlock', [[('list_items', 29)]], {})}),
        ),
        migrations.AlterField(
            model_name='generalpage',
            name='body',
            field=wagtail.fields.StreamField([('button', 4), ('custom_heading', 11), ('heading', 12), ('emphatic_text', 13), ('paragraph', 16), ('multi_column_paragraph', 19), ('image', 20), ('image_carousel', 23), ('html', 24), ('dropdown_image_list', 30), ('dropdown_button_list', 35), ('dropdown_card_list', 42), ('card_info_list', 48), ('image_info_list', 59), ('image_link_list', 64), ('three_column_dropdown_info_panel', 80), ('newsletters', 85)], block_lookup={0: ('wagtail.blocks.CharBlock', (), {'max_length': 100}), 1: ('wagtail.blocks.URLBlock', (), {}), 2: ('wagtail.blocks.ChoiceBlock', [], {'choices': [('dk-tn', 'Dark Tan'), ('green', 'Green'), ('orange', 'Orange'), ('red', 'Red'), ('tan', 'Tan'), ('black', 'Black'), ('white', 'White')]}), 3: ('wagtail.blocks.ChoiceBlock', [], {'choices': [('center', 'Center'), ('justify', 'Justified'), ('left', 'Left'), ('right', 'Right')]}), 4: ('wagtail.blocks.StructBlock', [[('text', 0), ('url', 1), ('color', 2), ('alignment', 3)]], {}), 5: ('wagtail.blocks.CharBlock', (), {'label': 'Title', 'required': True}), 6: ('wagtail.blocks.ChoiceBlock', [], {'choices': [('h2', 'H2'), ('h3', 'H3'), ('h4', 'H4'), ('h5', 'H5'), ('h6', 'H6')], 'label': 'Size'}), 7: ('wagtail.blocks.ChoiceBlock', [], {'choices': [('center', 'Center'), ('justify', 'Justified'), ('left', 'Left'), ('right', 'Right')], 'label': 'Alignment'}), 8: ('wagtail.blocks.ChoiceBlock', [], {'choices': [('dk-tn', 'Dark Tan'), ('green', 'Green'), ('orange', 'Orange'), ('red', 'Red'), ('tan', 'Tan'), ('black', 'Black'), ('white', 'White')], 'label': 'Color'}), 9: ('wagtail.blocks.ChoiceBlock', [], {'choices': [('default', 'Default'), ('tan-bg', 'Tan'), ('green-bg', 'Green'), ('dark-tan-bg', 'Dark Tan'), ('white-bg', 'White'), ('red-bg', 'Red'), ('orange-bg', 'Orange')]}), 10: ('wagtail.blocks.CharBlock', (), {'label': 'Optional Anchor Identifier', 'required': False, 'validators': [django.core.validators.RegexValidator(re.compile('^[-a-zA-Z0-9_]+\\Z'), 'Enter a valid “slug” consisting of letters, numbers, underscores or hyphens.', 'invalid')]}), 11: ('wagtail.blocks.StructBlock', [[('title', 5), ('heading_size', 6), ('alignment', 7), ('color', 8), ('background_color', 9), ('anchor_id', 10)]], {}), 12: ('home.models.Heading', (), {'form_classname': 'full title', 'help_text': 'Text will be green and centered'}), 13: ('home.models.EmphaticText', (), {'form_classname': 'full title', 'help_text': 'Text will be red, italic and centered'}), 14: ('wagtail.blocks.ChoiceBlock', [], {'choices': [('left', 'Left'), ('text-center', 'Center'), ('right', 'Right')]}), 15: ('wagtail.blocks.RichTextBlock', (), {}), 16: ('wagtail.blocks.StructBlock', [[('alignment', 14), ('background_color', 9), ('paragraph', 15)]], {'classname': 'paragraph', 'required': True}), 17: ('wagtail.blocks.ListBlock', (15,), {}), 18: ('wagtail.blocks.CharBlock', (), {'help_text': 'Green centered heading above column content', 'max_length': 100, 'required': False}), 19: ('wagtail.blocks.StructBlock', [[('alignment', 14), ('background_color', 9), ('paragraph', 17), ('title', 18)]], {}), 20: ('wagtail.images.blocks.ImageBlock', [], {'help_text': 'Centered image'}), 21: ('wagtail.images.blocks.ImageBlock', [], {}), 22: ('wagtail.blocks.ListBlock', (21,), {}), 23: ('wagtail.blocks.StructBlock', [[('images', 22)]], {}), 24: ('wagtail.blocks.RawHTMLBlock', (), {}), 25: ('wagtail.images.blocks.ImageBlock', [], {'label': 'Image'}), 26: ('wagtail.blocks.CharBlock', (), {'label': 'Title', 'max_length': 200}), 27: ('wagtail.blocks.RichTextBlock', (), {'label': 'Text'}), 28: ('wagtail.blocks.StructBlock', [[('image', 25), ('title', 26), ('text', 27)]], {}), 29: ('wagtail.blocks.ListBlock', (28,), {'label': 'List Item'}), 30: ('wagtail.blocks.StructBlock', [[('list_items', 29)]], {}), 31: ('wagtail.blocks.CharBlock', (), {'label': 'Button Text', 'max_length': 200}), 32: ('wagtail.blocks.RichTextBlock', (), {'features': ['h4', 'h5', 'bold', 'italic', 'link', 'document-link', 'ul'], 'label': 'Info Text'}), 33: ('wagtail.blocks.StructBlock', [[('button_text', 31), ('info_text', 32)]], {}), 34: ('wagtail.blocks.ListBlock', (33,), {'label': 'Button'}), 35: ('wagtail.blocks.StructBlock', [[('list_items', 34)]], {}), 36: ('wagtail.blocks.StructBlock', [[('alignment', 14), ('background_color', 9), ('paragraph', 15)]], {'label': 'Card Text'}), 37: ('wagtail.blocks.RichTextBlock', (), {'label': 'Info Text'}), 38: ('wagtail.blocks.CharBlock', (), {'help_text': 'Button appears below Info Text', 'max_length': 100, 'required': False}), 39: ('wagtail.blocks.URLBlock', (), {'label': 'Button URL', 'max_length': 200, 'required': False}), 40: ('wagtail.blocks.StructBlock', [[('card_info', 36), ('info_text', 37), ('info_button_text', 38), ('info_button_url', 39)]], {}), 41: ('wagtail.blocks.ListBlock', (40,), {'label': 'Card'}), 42: ('wagtail.blocks.StructBlock', [[('list_items', 41)]], {}), 43: ('wagtail.blocks.RichTextBlock', (), {'features': ['h4', 'h5', 'bold', 'italic', 'link', 'ul'], 'help_text': 'Note that h4 elements will be colored green and h5 elements will be colored purple', 'label': 'Text'}), 44: ('wagtail.blocks.CharBlock', (), {'label': 'Button Text', 'required': False}), 45: ('wagtail.blocks.CharBlock', (), {'label': 'Button URL', 'required': False}), 46: ('wagtail.blocks.StructBlock', [[('image', 25), ('text', 43), ('button_text', 44), ('button_url', 45)]], {}), 47: ('wagtail.blocks.ListBlock', (46,), {'label': 'Image Card List Item'}), 48: ('wagtail.blocks.StructBlock', [[('list_items', 47)]], {}), 49: ('wagtail.blocks.CharBlock', (), {'help_text': 'Overlayed on image', 'label': 'Image Title', 'max_length': 100, 'required': False}), 50: ('wagtail.blocks.CharBlock', (), {'help_text': 'Overlayed on image below title', 'label': 'Image Sub-title', 'max_length': 100, 'required': False}), 51: ('wagtail.blocks.CharBlock', (), {'help_text': 'Title heading for info displayed to the right of the image', 'label': 'Information Title', 'max_length': 500, 'required': True}), 52: ('wagtail.blocks.CharBlock', (), {'help_text': 'Subheading for info displayed beneath the Information Title', 'label': 'Information Sub-title', 'max_length': 500, 'required': False}), 53: ('wagtail.blocks.RichTextBlock', (), {'help_text': 'Text is centered, bold and green inside a tan background element', 'label': 'Tan background info text'}), 54: ('wagtail.blocks.CharBlock', (), {'help_text': 'Text for button within tan background element', 'label': 'Button text', 'required': False}), 55: ('wagtail.blocks.URLBlock', (), {'help_text': 'URL for button', 'required': False}), 56: ('wagtail.blocks.RichTextBlock', (), {'help_text': 'Text displayed below tan background element', 'required': False}), 57: ('wagtail.blocks.StructBlock', [[('image', 21), ('title', 49), ('subtitle', 50), ('info_title', 51), ('info_subtitle', 52), ('tan_bg_info', 53), ('tan_bg_button_text', 54), ('tan_bg_button_url', 55), ('additional_info', 56)]], {}), 58: ('wagtail.blocks.ListBlock', (57,), {'label': 'Image Information'}), 59: ('wagtail.blocks.StructBlock', [[('list_items', 58)]], {}), 60: ('wagtail.blocks.CharBlock', (), {'label': 'Title', 'max_length': 200, 'required': False}), 61: ('wagtail.blocks.URLBlock', (), {'label': 'URL'}), 62: ('wagtail.blocks.StructBlock', [[('title', 60), ('url', 61), ('image', 21)]], {}), 63: ('wagtail.blocks.ListBlock', (62,), {'label': 'Image Links'}), 64: ('wagtail.blocks.StructBlock', [[('list_items', 63)]], {}), 65: ('wagtail.blocks.ChoiceBlock', [], {'choices': [('default-panel', 'Default'), ('purple-panel', 'Purple'), ('orange-panel', 'Orange'), ('blue-panel', 'Blue'), ('green-panel', 'Green')]}), 66: ('wagtail.blocks.RichTextBlock', (), {'help_text': 'Header for first column of dropdown panel', 'label': 'Column One Panel Header', 'required': True}), 67: ('wagtail.blocks.RichTextBlock', (), {'help_text': 'Header for second column of dropdown panel', 'label': 'Column Two Panel Header', 'required': True}), 68: ('wagtail.blocks.RichTextBlock', (), {'help_text': 'Header for third column of dropdown panel', 'label': 'Column Three Panel Header', 'required': True}), 69: ('wagtail.blocks.BooleanBlock', (), {'help_text': 'Select this option to include class-related subheadings for all columns (e.g. Grade, Ages, Session, Location, Cost', 'label': 'Subheaders for Classes'}), 70: ('wagtail.blocks.RichTextBlock', (), {'help_text': 'If class subheaders are selected, this text appears after the "GRADE:" subheading'}), 71: ('wagtail.blocks.RichTextBlock', (), {'help_text': 'If class subheaders are selected, this text appears after the "AGES:" subheading'}), 72: ('wagtail.blocks.RichTextBlock', (), {'help_text': 'If class subheaders are selected, this text appears after the "SESSION:" subheading'}), 73: ('wagtail.blocks.StructBlock', [[('alignment', 14), ('background_color', 9), ('paragraph', 15)]], {'help_text': 'Text info appearing inside expanded panel between top and bottom subheader content'}), 74: ('wagtail.blocks.StructBlock', [[('text', 0), ('url', 1), ('color', 2), ('alignment', 3)]], {'required': False}), 75: ('wagtail.blocks.RichTextBlock', (), {'help_text': 'If class subheaders are selected, this text appears beside the "LOCATION:" subheading'}), 76: ('wagtail.blocks.RichTextBlock', (), {'help_text': 'If class subheaders are selected, this text appears beside the "COST:" subheading'}), 77: ('wagtail.blocks.RichTextBlock', (), {'help_text': 'If class subheaders are selected, this text appears beside the "CONTACT INFORMATION:" subheading'}), 78: ('wagtail.blocks.StructBlock', [[('background_color', 65), ('col_one_header', 66), ('col_two_header', 67), ('col_three_header', 68), ('class_info_subheaders', 69), ('col_one_top_info', 70), ('col_two_top_info', 71), ('col_three_top_info', 72), ('middle_info', 73), ('button', 74), ('col_one_bottom_info', 75), ('col_two_bottom_info', 76), ('col_three_bottom_info', 77)]], {}), 79: ('wagtail.blocks.ListBlock', (78,), {'label': 'Thee Column Dropdown Info Panel'}), 80: ('wagtail.blocks.StructBlock', [[('list_items', 79)]], {}), 81: ('wagtail.blocks.CharBlock', (), {'max_length': 100, 'required': False}), 82: ('wagtail.blocks.RawHTMLBlock', (), {'required': True}), 83: ('wagtail.blocks.StructBlock', [[('title', 81), ('embed', 82)]], {}), 84: ('wagtail.blocks.ListBlock', (83,), {}), 85: ('wagtail.blocks.StructBlock', [[('list_items', 84)]], {})}),
        ),
        migrations.AlterField(
            model_name='twocolumngeneralpage',
            name='body',
            field=wagtail.fields.StreamField([('green_heading', 0), ('emphatic_text', 1), ('paragraph', 5), ('image', 6), ('document', 7), ('two_columns', 16), ('embedded_video', 17), ('html', 13), ('dropdown_image_list', 23), ('dropdown_button_list', 28)], blank=True, block_lookup={0: ('home.models.Heading', (), {'form_classname': 'full title', 'help_text': 'Text will be green and centered'}), 1: ('home.models.EmphaticText', (), {'form_classname': 'full title', 'help_text': 'Text will be red, italic and centered'}), 2: ('wagtail.blocks.ChoiceBlock', [], {'choices': [('left', 'Left'), ('text-center', 'Center'), ('right', 'Right')]}), 3: ('wagtail.blocks.ChoiceBlock', [], {'choices': [('default', 'Default'), ('tan-bg', 'Tan'), ('green-bg', 'Green'), ('dark-tan-bg', 'Dark Tan'), ('white-bg', 'White'), ('red-bg', 'Red'), ('orange-bg', 'Orange')]}), 4: ('wagtail.blocks.RichTextBlock', (), {}), 5: ('wagtail.blocks.StructBlock', [[('alignment', 2), ('background_color', 3), ('paragraph', 4)]], {}), 6: ('wagtail.images.blocks.ImageBlock', [], {}), 7: ('wagtail.documents.blocks.DocumentChooserBlock', (), {}), 8: ('wagtail.blocks.CharBlock', (), {'max_length': 100}), 9: ('wagtail.blocks.URLBlock', (), {}), 10: ('wagtail.blocks.ChoiceBlock', [], {'choices': [('dk-tn', 'Dark Tan'), ('green', 'Green'), ('orange', 'Orange'), ('red', 'Red'), ('tan', 'Tan'), ('black', 'Black'), ('white', 'White')]}), 11: ('wagtail.blocks.ChoiceBlock', [], {'choices': [('center', 'Center'), ('justify', 'Justified'), ('left', 'Left'), ('right', 'Right')]}), 12: ('wagtail.blocks.StructBlock', [[('text', 8), ('url', 9), ('color', 10), ('alignment', 11)]], {}), 13: ('wagtail.blocks.RawHTMLBlock', (), {}), 14: ('wagtail.blocks.StreamBlock', [[('heading', 0), ('emphatic_text', 1), ('aligned_paragraph', 5), ('paragraph', 4), ('image', 6), ('document', 7), ('button', 12), ('html', 13)]], {'icon': 'arrow-left', 'label': 'Left column content'}), 15: ('wagtail.blocks.StreamBlock', [[('heading', 0), ('emphatic_text', 1), ('aligned_paragraph', 5), ('paragraph', 4), ('image', 6), ('document', 7), ('button', 12), ('html', 13)]], {'icon': 'arrow-right', 'label': 'Right column content'}), 16: ('wagtail.blocks.StructBlock', [[('left_column', 14), ('right_column', 15)]], {}), 17: ('wagtail.embeds.blocks.EmbedBlock', (), {'icon': 'media'}), 18: ('wagtail.images.blocks.ImageBlock', [], {'label': 'Image'}), 19: ('wagtail.blocks.CharBlock', (), {'label': 'Title', 'max_length': 200}), 20: ('wagtail.blocks.RichTextBlock', (), {'label': 'Text'}), 21: ('wagtail.blocks.StructBlock', [[('image', 18), ('title', 19), ('text', 20)]], {}), 22: ('wagtail.blocks.ListBlock', (21,), {'label': 'List Item'}), 23: ('wagtail.blocks.StructBlock', [[('list_items', 22)]], {}), 24: ('wagtail.blocks.CharBlock', (), {'label': 'Button Text', 'max_length': 200}), 25: ('wagtail.blocks.RichTextBlock', (), {'features': ['h4', 'h5', 'bold', 'italic', 'link', 'document-link', 'ul'], 'label': 'Info Text'}), 26: ('wagtail.blocks.StructBlock', [[('button_text', 24), ('info_text', 25)]], {}), 27: ('wagtail.blocks.ListBlock', (26,), {'label': 'Button'}), 28: ('wagtail.blocks.StructBlock', [[('list_items', 27)]], {})}, null=True),
        ),
    ]
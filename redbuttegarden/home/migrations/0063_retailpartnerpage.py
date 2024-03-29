# Generated by Django 3.0.10 on 2021-04-06 16:57

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import home.models
import wagtail.blocks
import wagtail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0023_add_choose_permissions'),
        ('wagtailcore', '0060_fix_workflow_unique_constraint'),
        ('home', '0062_auto_20210324_1117'),
    ]

    operations = [
        migrations.CreateModel(
            name='RetailPartnerPage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('body', wagtail.fields.StreamField([('button', wagtail.blocks.StructBlock([('text', wagtail.blocks.CharBlock(max_length=100)), ('url', wagtail.blocks.URLBlock()), ('color', wagtail.blocks.ChoiceBlock(choices=[('dk-tn', 'Dark Tan'), ('green', 'Green'), ('org', 'Orange'), ('red', 'Red'), ('tan', 'Tan')])), ('alignment', wagtail.blocks.ChoiceBlock(choices=[('center', 'Center'), ('justify', 'Justified'), ('left', 'Left'), ('right', 'Right')]))])), ('green_heading', home.models.Heading()), ('paragraph', wagtail.blocks.StructBlock([('alignment', wagtail.blocks.ChoiceBlock(choices=[('left', 'Left'), ('text-center', 'Center'), ('right', 'Right')])), ('background_color', wagtail.blocks.ChoiceBlock(choices=[('default', 'Default'), ('tan-bg', 'Tan'), ('green-bg', 'Green'), ('dark-tan-bg', 'Dark Tan'), ('white-bg', 'White'), ('red-bg', 'Red'), ('orange-bg', 'Orange')])), ('paragraph', wagtail.blocks.RichTextBlock())]))])),
                ('retail_partners', wagtail.fields.StreamField([('retail_partner', wagtail.blocks.StructBlock([('name', wagtail.blocks.CharBlock(max_length=75)), ('addresses', wagtail.blocks.ListBlock(wagtail.blocks.StructBlock([('street_address', wagtail.blocks.CharBlock(max_length=40, required=False)), ('city', wagtail.blocks.CharBlock(max_length=30, required=False)), ('zipcode', wagtail.blocks.IntegerBlock(max_value=99950, min_value=501, required=False)), ('phone', wagtail.blocks.CharBlock(validators=[django.core.validators.RegexValidator('\\(?[0-9]{3}\\)?[-|\\s]?[0-9]{3}-?[0-9]{4}', 'Please enter a valid phone number')]))]), required=False)), ('url', wagtail.blocks.URLBlock(required=False)), ('info', wagtail.blocks.RichTextBlock())]))])),
                ('banner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailimages.Image')),
                ('thumbnail', models.ForeignKey(blank=True, help_text='You only need to add a thumbnail if this page is the child of a another page', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailimages.Image')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
    ]

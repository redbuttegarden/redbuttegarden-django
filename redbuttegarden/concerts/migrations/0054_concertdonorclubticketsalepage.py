# Generated by Django 4.1.10 on 2023-11-08 23:17

from django.db import migrations, models
import django.db.models.deletion
import wagtail.blocks
import wagtail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0083_workflowcontenttype'),
        ('wagtailimages', '0025_alter_image_file_alter_rendition_file'),
        ('wagtaildocs', '0012_uploadeddocument'),
        ('concerts', '0053_alter_concertpage_body'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConcertDonorClubTicketSalePage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.page')),
                ('dialog_display', models.BooleanField(blank=True, default=False, help_text='Should this dialog be displayed?', null=True)),
                ('dialog_title', models.CharField(blank=True, help_text='Title for pop-up dialog box', max_length=100, null=True)),
                ('dialog_content', wagtail.fields.RichTextField(blank=True, help_text='Main content of the dialog box', null=True)),
                ('dialog_style', models.CharField(blank=True, choices=[('corner', 'Corner'), ('full', 'Full Page')], max_length=6, null=True)),
                ('body', wagtail.fields.StreamField([('paragraph', wagtail.blocks.StructBlock([('alignment', wagtail.blocks.ChoiceBlock(choices=[('left', 'Left'), ('text-center', 'Center'), ('right', 'Right')])), ('background_color', wagtail.blocks.ChoiceBlock(choices=[('default', 'Default'), ('tan-bg', 'Tan'), ('green-bg', 'Green'), ('white-bg', 'White'), ('red-bg', 'Red'), ('orange-bg', 'Orange')])), ('paragraph', wagtail.blocks.RichTextBlock())], classname='paragraph', required=True))], use_json_field=True)),
                ('banner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailimages.image')),
                ('custom_css', models.ForeignKey(blank=True, help_text='Upload a CSS file to apply custom styling to this page. Note that editing an existing document will apply the changes to ALL pages where the document is used', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtaildocs.document', verbose_name='Custom CSS')),
                ('thumbnail', models.ForeignKey(blank=True, help_text='You only need to add a thumbnail if this page is the child of a another page', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailimages.image')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
    ]
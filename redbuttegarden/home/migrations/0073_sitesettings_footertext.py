# Generated by Django 4.1.9 on 2023-09-05 19:00

from django.db import migrations, models
import django.db.models.deletion
import uuid
import wagtail.fields
import wagtail.models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0078_referenceindex'),
        ('home', '0072_alter_faqpage_body'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title_suffix', models.CharField(default='Red Butte Garden', help_text="The suffix for the title meta tag e.g. ' | Red Butte Garden'", max_length=255, verbose_name='Title suffix')),
                ('site', models.OneToOneField(editable=False, on_delete=django.db.models.deletion.CASCADE, to='wagtailcore.site')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FooterText',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('translation_key', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('live', models.BooleanField(default=True, editable=False, verbose_name='live')),
                ('has_unpublished_changes', models.BooleanField(default=False, editable=False, verbose_name='has unpublished changes')),
                ('first_published_at', models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='first published at')),
                ('last_published_at', models.DateTimeField(editable=False, null=True, verbose_name='last published at')),
                ('go_live_at', models.DateTimeField(blank=True, null=True, verbose_name='go live date/time')),
                ('expire_at', models.DateTimeField(blank=True, null=True, verbose_name='expiry date/time')),
                ('expired', models.BooleanField(default=False, editable=False, verbose_name='expired')),
                ('body', wagtail.fields.RichTextField()),
                ('latest_revision', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailcore.revision', verbose_name='latest revision')),
                ('live_revision', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailcore.revision', verbose_name='live revision')),
                ('locale', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailcore.locale')),
            ],
            options={
                'verbose_name_plural': 'Footer Text',
                'abstract': False,
                'unique_together': {('translation_key', 'locale')},
            },
            bases=(wagtail.models.PreviewableMixin, models.Model),
        ),
    ]
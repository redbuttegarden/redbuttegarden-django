# Generated by Django 3.0.10 on 2020-10-01 17:05

from django.db import migrations
import wagtail.core.blocks
import wagtail.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0028_rbghours_gad_dates'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rbghours',
            name='gad_dates',
            field=wagtail.core.fields.StreamField([('date', wagtail.core.blocks.DateBlock(help_text='Date that GAD takes place', verbose_name='Garden After Dark date'))], blank=True, help_text='Choose the dates of GAD. If there are many, using the manual override might be easier', null=True),
        ),
    ]
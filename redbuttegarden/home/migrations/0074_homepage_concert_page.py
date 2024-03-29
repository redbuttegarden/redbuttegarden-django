# Generated by Django 4.1.9 on 2023-10-04 15:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('concerts', '0053_alter_concertpage_body'),
        ('home', '0073_sitesettings_footertext'),
    ]

    operations = [
        migrations.AddField(
            model_name='homepage',
            name='concert_page',
            field=models.ForeignKey(blank=True, help_text='Set to this years concert Wagtail page to extract concert dates', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='concerts.concertpage'),
        ),
    ]

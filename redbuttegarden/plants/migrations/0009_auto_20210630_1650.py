# Generated by Django 3.0.10 on 2021-06-30 22:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plants', '0008_auto_20210630_1611'),
    ]

    operations = [
        migrations.AlterField(
            model_name='species',
            name='name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]

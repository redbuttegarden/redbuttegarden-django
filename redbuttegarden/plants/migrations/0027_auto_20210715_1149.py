# Generated by Django 3.0.10 on 2021-07-15 17:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plants', '0026_auto_20210715_1132'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gardenarea',
            name='code',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]

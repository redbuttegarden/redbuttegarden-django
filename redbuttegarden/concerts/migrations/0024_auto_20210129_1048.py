# Generated by Django 3.0.10 on 2021-01-29 17:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('concerts', '0023_auto_20210121_1102'),
    ]

    operations = [
        migrations.AlterField(
            model_name='concert',
            name='concert_date',
            field=models.DateField(),
        ),
    ]
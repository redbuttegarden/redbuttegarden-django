# Generated by Django 3.0.10 on 2021-01-12 19:40

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('concerts', '0012_auto_20210112_1228'),
    ]

    operations = [
        migrations.AlterField(
            model_name='concert',
            name='gates_time',
            field=models.TimeField(blank=True, default=datetime.time(18, 0), null=True),
        ),
    ]
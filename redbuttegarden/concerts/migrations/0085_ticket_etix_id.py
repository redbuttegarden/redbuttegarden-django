# Generated by Django 4.2.20 on 2025-05-17 17:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('concerts', '0084_alter_concertdonorclubmember_phone_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='etix_id',
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
    ]

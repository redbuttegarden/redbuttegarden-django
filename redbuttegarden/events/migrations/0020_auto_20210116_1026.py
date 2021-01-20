# Generated by Django 3.0.10 on 2021-01-16 17:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0019_auto_20210115_1511'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventpage',
            name='member_cost',
            field=models.CharField(blank=True, help_text='Accepts numbers or text. e.g. Free!', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='eventpage',
            name='public_cost',
            field=models.CharField(blank=True, help_text='Accepts numbers or text. e.g. $35', max_length=200, null=True),
        ),
    ]
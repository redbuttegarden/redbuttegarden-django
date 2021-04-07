# Generated by Django 3.0.10 on 2021-03-30 18:48

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0029_eventgeneralpage_event_categories'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventgeneralpage',
            name='order_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='eventindexpage',
            name='order_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='eventpage',
            name='order_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
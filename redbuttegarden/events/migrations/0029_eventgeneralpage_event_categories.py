# Generated by Django 3.0.10 on 2021-02-19 19:31

from django.db import migrations
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0028_auto_20210219_1138'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventgeneralpage',
            name='event_categories',
            field=modelcluster.fields.ParentalManyToManyField(blank=True, to='events.EventCategory'),
        ),
    ]

# Generated by Django 4.2.20 on 2025-05-02 16:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('concerts', '0082_concertdonorclubmember_chat_access_token_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='concertdonorclubmember',
            options={'ordering': ['user__username', 'user__last_name', 'user__first_name']},
        ),
        migrations.AlterField(
            model_name='concertdonorclubmember',
            name='packages',
            field=models.ManyToManyField(blank=True, help_text='Concert Donor Club packages that this member has purchased. Hold command', to='concerts.concertdonorclubpackage'),
        ),
    ]

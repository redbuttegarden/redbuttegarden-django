# Generated by Django 3.2.5 on 2021-10-14 20:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plants', '0033_alter_location_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='species',
            name='forma',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='species',
            name='subforma',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='species',
            name='subspecies',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='species',
            name='subvariety',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='species',
            name='variety',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='species',
            unique_together={('genus', 'name', 'subspecies', 'variety', 'subvariety', 'forma', 'subforma', 'cultivar')},
        ),
    ]

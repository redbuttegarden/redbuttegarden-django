# Generated by Django 3.2.5 on 2021-10-15 20:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plants', '0034_auto_20211014_1431'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='species',
            options={'ordering': ['full_name'], 'verbose_name_plural': 'species'},
        ),
        migrations.AddField(
            model_name='species',
            name='full_name',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
        migrations.AddConstraint(
            model_name='species',
            constraint=models.CheckConstraint(check=models.Q(('full_name__length__gt', 0)), name='full_name_not_empty'),
        ),
    ]

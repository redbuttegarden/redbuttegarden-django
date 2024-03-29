# Generated by Django 4.1.10 on 2024-01-26 18:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('concerts', '0059_alter_ticket_barcode_alter_ticket_serial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ticket',
            name='serial',
        ),
        migrations.AddField(
            model_name='ticket',
            name='order_id',
            field=models.PositiveBigIntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='ticket',
            name='package',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='concerts.concertdonorclubpackage'),
        ),
    ]

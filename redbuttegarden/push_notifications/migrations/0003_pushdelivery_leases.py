import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("push_notifications", "0002_pushrequestratelimit")]

    operations = [
        migrations.AddField(
            model_name="pushdelivery",
            name="dispatch_lease_expires_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="pushdelivery",
            name="dispatch_lease_token",
            field=models.UUIDField(blank=True, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name="pushdelivery",
            name="status",
            field=models.CharField(choices=[("pending", "Pending"), ("sending", "Sending"), ("accepted", "Accepted by push service"), ("failed", "Failed"), ("expired", "Expired subscription")], db_index=True, default="pending", max_length=16),
        ),
    ]

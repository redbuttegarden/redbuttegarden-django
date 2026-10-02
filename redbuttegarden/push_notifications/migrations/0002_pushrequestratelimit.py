import django.db.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("push_notifications", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="PushRequestRateLimit",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("client_hash", models.CharField(max_length=64)),
                ("window_started_at", models.DateTimeField()),
                ("request_count", models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.AddConstraint(
            model_name="pushrequestratelimit",
            constraint=models.UniqueConstraint(fields=("client_hash", "window_started_at"), name="unique_push_rate_limit_window"),
        ),
        migrations.AddIndex(
            model_name="pushrequestratelimit",
            index=models.Index(fields=["window_started_at"], name="push_notif_window__eee8f4_idx"),
        ),
    ]

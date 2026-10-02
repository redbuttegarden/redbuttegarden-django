# Generated manually for the initial additive Web Push schema.

import django.db.models.deletion
import push_notifications.models
import uuid
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PushNotification",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=120)),
                ("body", models.CharField(max_length=300)),
                ("icon_path", models.CharField(default=push_notifications.models.DEFAULT_ICON_PATH, max_length=500, validators=[push_notifications.models.validate_same_origin_path])),
                ("destination_path", models.CharField(default="/", max_length=500, validators=[push_notifications.models.validate_same_origin_path])),
                ("scheduled_time", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("dispatch_started_at", models.DateTimeField(blank=True, null=True)),
                ("dispatch_lease_expires_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("dispatch_lease_token", models.UUIDField(blank=True, editable=False, null=True)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("scheduled", "Scheduled"), ("sending", "Sending"), ("sent", "Sent"), ("failed", "Failed"), ("cancelled", "Cancelled")], db_index=True, default="draft", max_length=16)),
                ("subscriber_count_at_send", models.PositiveIntegerField(default=0)),
                ("accepted_count", models.PositiveIntegerField(default=0)),
                ("click_count", models.PositiveIntegerField(default=0)),
                ("failure_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="PushSubscriber",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("endpoint", models.URLField(max_length=2048, unique=True)),
                ("p256dh", models.CharField(max_length=256)),
                ("auth", models.CharField(max_length=128)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("last_seen_at", models.DateTimeField(default=timezone.now)),
                ("unsubscribed_at", models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="PushDelivery",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("subscriber_id_at_dispatch", models.UUIDField()),
                ("status", models.CharField(choices=[("pending", "Pending"), ("accepted", "Accepted by push service"), ("failed", "Failed"), ("expired", "Expired subscription")], db_index=True, default="pending", max_length=16)),
                ("accepted_at", models.DateTimeField(blank=True, null=True)),
                ("clicked_at", models.DateTimeField(blank=True, null=True)),
                ("error_category", models.CharField(blank=True, max_length=64)),
                ("click_token", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("notification", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="deliveries", to="push_notifications.pushnotification")),
                ("subscriber", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="deliveries", to="push_notifications.pushsubscriber")),
            ],
        ),
        migrations.AddIndex(model_name="pushsubscriber", index=models.Index(fields=["is_active", "last_seen_at"], name="push_notif_is_acti_b58417_idx")),
        migrations.AddConstraint(model_name="pushdelivery", constraint=models.UniqueConstraint(fields=("notification", "subscriber"), name="unique_push_delivery")),
        migrations.AddIndex(model_name="pushdelivery", index=models.Index(fields=["notification", "status"], name="push_notif_notific_7049d5_idx")),
    ]

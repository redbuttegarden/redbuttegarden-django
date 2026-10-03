"""Persistent Web Push subscriptions, notifications, and delivery records."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from wagtail.admin.panels import FieldPanel, MultiFieldPanel


DEFAULT_ICON_PATH = "/static/redbuttegarden/img/favicon/icon-192x192.png"


def validate_same_origin_path(value: str) -> None:
    """Reject URLs which could navigate or load an asset from another origin."""

    parsed = urlparse(value)
    if (
        not value.startswith("/")
        or value.startswith("//")
        or parsed.scheme
        or parsed.netloc
        or "\\" in value
        or any(character.isspace() for character in value)
        or any(ord(character) < 32 for character in value)
    ):
        raise ValidationError("Enter a same-origin path beginning with '/'.")


class PushSubscriber(models.Model):
    """A browser's anonymous Web Push subscription."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    endpoint = models.URLField(unique=True, max_length=2048)
    p256dh = models.CharField(max_length=256)
    auth = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen_at = models.DateTimeField(default=timezone.now)
    unsubscribed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [models.Index(fields=["is_active", "last_seen_at"], name="push_notif_is_acti_b58417_idx")]

    def __str__(self) -> str:
        """Return a non-sensitive label suitable for internal debugging."""

        return f"Push subscriber {self.pk}"


class PushNotification(models.Model):
    """An editor-authored broadcast notification and its aggregate analytics."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SCHEDULED = "scheduled", "Scheduled"
        SENDING = "sending", "Sending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=120)
    body = models.CharField(max_length=300)
    icon_path = models.CharField(max_length=500, default=DEFAULT_ICON_PATH, validators=[validate_same_origin_path])
    destination_path = models.CharField(max_length=500, default="/", validators=[validate_same_origin_path])
    scheduled_time = models.DateTimeField(blank=True, null=True, db_index=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    dispatch_started_at = models.DateTimeField(blank=True, null=True)
    dispatch_lease_expires_at = models.DateTimeField(blank=True, null=True, db_index=True)
    dispatch_lease_token = models.UUIDField(blank=True, null=True, editable=False)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True)
    subscriber_count_at_send = models.PositiveIntegerField(default=0)
    accepted_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)
    failure_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    panels = [
        MultiFieldPanel([FieldPanel("title"), FieldPanel("body"), FieldPanel("icon_path"), FieldPanel("destination_path")], heading="Content"),
        MultiFieldPanel([FieldPanel("scheduled_time")], heading="Delivery"),
    ]

    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("manage_push_notifications", "Can manage push notifications"),
        ]

    def clean(self) -> None:
        """Enforce valid scheduling and immutable completed notification content."""

        super().clean()
        if self.status == self.Status.SCHEDULED and not self.scheduled_time:
            raise ValidationError({"scheduled_time": "Scheduled notifications need a delivery time."})
        if (
            self.status == self.Status.SCHEDULED
            and self.scheduled_time
            and self.scheduled_time < timezone.now() - timedelta(seconds=5)
        ):
            raise ValidationError({"scheduled_time": "Choose a present or future delivery time."})
        if not self.pk:
            return
        previous = type(self).objects.filter(pk=self.pk).first()
        if previous and previous.status in {self.Status.SENT, self.Status.CANCELLED}:
            protected = ("title", "body", "icon_path", "destination_path", "scheduled_time", "status")
            if any(getattr(previous, field) != getattr(self, field) for field in protected):
                raise ValidationError("Completed or cancelled notifications cannot be edited.")

    @property
    def accepted_rate(self) -> float | None:
        """Return acceptance percentage, or None when no audience existed."""

        return (self.accepted_count / self.subscriber_count_at_send * 100) if self.subscriber_count_at_send else None

    @property
    def click_rate(self) -> float | None:
        """Return click-through percentage, or None when nothing was accepted."""

        return (self.click_count / self.accepted_count * 100) if self.accepted_count else None

    def __str__(self) -> str:
        """Return the editor-visible notification title."""

        return self.title


class PushDelivery(models.Model):
    """One subscriber-level send attempt retained for accurate aggregate metrics."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENDING = "sending", "Sending"
        ACCEPTED = "accepted", "Accepted by push service"
        FAILED = "failed", "Failed"
        EXPIRED = "expired", "Expired subscription"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification = models.ForeignKey(PushNotification, on_delete=models.CASCADE, related_name="deliveries")
    subscriber = models.ForeignKey(PushSubscriber, on_delete=models.SET_NULL, null=True, related_name="deliveries")
    subscriber_id_at_dispatch = models.UUIDField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)
    accepted_at = models.DateTimeField(blank=True, null=True)
    clicked_at = models.DateTimeField(blank=True, null=True)
    dispatch_lease_token = models.UUIDField(blank=True, null=True, editable=False)
    dispatch_lease_expires_at = models.DateTimeField(blank=True, null=True, db_index=True)
    error_category = models.CharField(max_length=64, blank=True)
    click_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["notification", "subscriber"], name="unique_push_delivery")]
        indexes = [models.Index(fields=["notification", "status"], name="push_notif_notific_7049d5_idx")]


class PushRequestRateLimit(models.Model):
    """Short-lived, hashed client counters for globally effective write throttling."""

    client_hash = models.CharField(max_length=64)
    window_started_at = models.DateTimeField()
    request_count = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["window_started_at"], name="push_notif_window__eee8f4_idx")]
        constraints = [
            models.UniqueConstraint(
                fields=["client_hash", "window_started_at"],
                name="unique_push_rate_limit_window",
            )
        ]

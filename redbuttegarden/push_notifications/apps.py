"""Application configuration for Web Push notifications."""

from django.apps import AppConfig


class PushNotificationsConfig(AppConfig):
    """Configure the Web Push notification application."""

    default_auto_field = "django.db.models.AutoField"
    name = "push_notifications"
